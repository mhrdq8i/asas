from uuid import UUID
from typing import List, Optional

from sqlmodel import select, func, or_
from sqlmodel.ext.asyncio.session import (
    AsyncSession
)

from src.models.user import User
from src.api.v1.schemas.user_schemas import (
    UserCreateInternal
)


class CrudUser:
    """
    CRUD operations for User model.
    An instance of this class should be
    initialized with an AsyncSession.
    """

    def __init__(
            self, db_session: AsyncSession
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

        statement = select(
            User
        ).where(
            User.id == user_id
        )

        result = await self.db.exec(
            statement=statement
        )

        return result.first()

    async def get_user_by_username(
        self,
        *,
        username: str
    ) -> Optional[User]:
        """
        Retrieve a user by their username
        (case-insensitive).
        """

        statement = select(User).where(
            func.lower(
                User.username
            ) == func.lower(
                username
            )
        )

        result = await self.db.exec(
            statement=statement
        )

        return result.first()

    async def get_user_by_email(
        self,
        *,
        email: str
    ) -> Optional[User]:
        """
        Retrieve a user by their
        email address (case-insensitive).
        """

        statement = select(
            User
        ).where(
            func.lower(
                User.email
            ) == func.lower(
                email
            )
        )

        result = await self.db.exec(
            statement=statement
        )

        return result.first()

    async def get_user_by_username_or_email(
        self,
        *,
        username: str,
        email: str
    ) -> Optional[User]:
        """
        Retrieves a user by either username
        or email (case-insensitive).
        This method is fixed to use
        the correct 'or_' operator from SQLAlchemy.
        """

        statement = select(User).where(
            or_(
                func.lower(
                    User.username
                ) == func.lower(username),
                func.lower(
                    User.email
                ) == func.lower(email)
            )
        )

        result = await self.db.exec(
            statement=statement
        )

        return result.first()

    async def create_user(
        self,
        *,
        user_in: UserCreateInternal
    ) -> User:
        """
        Create a new user in the database.
        """

        db_user = User.model_validate(user_in)

        self.db.add(
            instance=db_user
        )

        # The service layer will
        # handle the commit.
        return db_user

    async def update_user(
        self,
        *,
        db_user_to_update: User,
        user_in_update_data: dict
    ) -> User:
        """
        Update an existing user's information.
        """

        for (
            field,
            value
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

        statement = select(User).offset(
            offset=skip
        ).limit(
            limit=limit
        ).order_by(
            User.username
        )

        result = await self.db.exec(
            statement=statement
        )

        return list(result.all())

    async def get_commanders(self) -> List[User]:
        """
        Retrieve a list of all active
        users designated as commanders.
        """

        statement = select(User).where(
            User.is_commander,
            User.is_active
        )

        result = await self.db.exec(
            statement=statement
        )

        return list(result.all())
