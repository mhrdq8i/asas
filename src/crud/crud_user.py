from uuid import UUID
from typing import (
    List,
    Optional
)

from sqlmodel import (
    select,
    func  # func for count
)
from sqlmodel.ext.asyncio.session import (
    AsyncSession
)  # type: ignore

from src.models.user import User

# For creating user with hashed_password
from src.api.v1.schemas.user_schemas import (
    UserCreateInternal
)


class CRUDUser:
    """
    CRUD operations for User model.
    An instance of this class should be
    initialized with an AsyncSession.
    """

    def __init__(
            self,
            db_session: AsyncSession
    ):
        self.db: AsyncSession = db_session

    async def get_user_by_id(
        self,
        *,
        user_id: UUID
    ) -> Optional[User]:
        """
        Retrieve a user by their ID.
        """
        statement = select(User).where(
            User.id == user_id
        )
        result = await self.db.exec(statement)

        return result.first()

    async def get_user_by_username(
        self,
        *,
        username: str
    ) -> Optional[User]:
        """
        Retrieve a user by their username.
        Uses case-insensitive search for username.
        """
        statement = select(User).where(
            func.lower(
                User.username
            ) == func.lower(
                username
            )
        )
        result = await self.db.exec(statement)

        return result.first()

    async def get_user_by_email(
        self,
        *,
        email: str
    ) -> Optional[User]:
        """
        Retrieve a user by their email address.
        Uses case-insensitive search for email.
        """
        statement = select(User).where(
            func.lower(
                User.email
            ) == func.lower(
                email
            )
        )
        result = await self.db.exec(statement)

        return result.first()

    async def get_user_by_username_or_email(
        self,
        *,
        username: str | None = None,
        email: str | None = None
    ) -> Optional[User]:
        """
        Retrieve a user by either username or email (case-insensitive).
        Useful for checking if a user already exists during registration.
        """
        if not username and not email:
            return None

        conditions = []
        if username:
            conditions.append(
                func.lower(
                    User.username
                ) == func.lower(
                    username
                )
            )
        if email:
            conditions.append(
                func.lower(
                    User.email
                ) == func.lower(
                    email
                )
            )

        if not conditions:
            return None

        statement = select(User).where(
            func.or_(
                *conditions
            )
        )
        result = await self.db.exec(statement)

        return result.first()

    async def db_create_user(
            self,
            *,
            user_in: UserCreateInternal
    ) -> User:
        """
        Create a new user in the database.
        Expects user_in.hashed_password to be already hashed.
        """

        db_user = User.model_validate(
            user_in
        )  # Pydantic V2 way

        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)

        return db_user

    async def update_user(
        self,
        *,
        db_user_to_update: User,
        user_in_update_data: dict
    ) -> User:
        """
        Update an existing user's information.
        'db_user_to_update' is the existing SQLAlchemy model instance.
        'user_in_update_data' should be a dictionary of fields to update.
        """

        for (
            field, value
        ) in user_in_update_data.items():

            if value is not None:
                setattr(
                    db_user_to_update,
                    field,
                    value
                )

        self.db.add(
            db_user_to_update
        )
        await self.db.commit()
        await self.db.refresh(
            db_user_to_update
        )

        return db_user_to_update

    async def get_users(
        self,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """
        Retrieve a list of users with pagination.
        """
        statement = select(
            User
        ).offset(skip).limit(limit)
        result = await self.db.exec(statement)
        users = result.all()

        return list(users)

    async def count_users(self) -> int:
        """
        Count the total number of users.
        """
        statement = select(
            func.count(
                User.id
            )
        )
        result = await self.db.exec(statement)
        count = result.one_or_none()

        return count if count is not None else 0

    async def soft_delete_user(
        self,
        *,
        user_id: UUID
    ) -> Optional[User]:

        # No need to pass db
        db_user = await self.get_user_by_id(user_id=user_id)

        if not db_user:
            return None

        if not hasattr(
            db_user, 'is_deleted'
        ) or not hasattr(
            db_user, 'deleted_at'
        ):
            raise AttributeError(
                "User model does not support soft delete"
                "(missing 'is_deleted' or 'deleted_at' fields)."
            )

        from datetime import datetime, timezone

        db_user.is_deleted = True
        db_user.deleted_at = datetime.now(
            timezone.utc
        )
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)

        return db_user
