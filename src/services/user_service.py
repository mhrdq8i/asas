import logging
from uuid import UUID
from typing import List
from datetime import datetime, timezone

from sqlmodel.ext.asyncio.session import (
    AsyncSession
)

from src.crud.user_crud import CRUDUser
from src.crud.incident_crud import (
    CrudIncident
)
from src.models.user import User
from src.api.v1.schemas.user_schemas import (
    UserCreate,
    UserCreateInternal,
    UserUpdate,
    UserUpdatePassword,
)
from src.core.security import (
    get_password_hash,
    verify_password
)
from src.exceptions.common_exceptions import (
    DuplicateResourceException,
    InvalidOperationException,
    InvalidInputException,
)
from src.exceptions.user_exceptions import (
    AuthenticationFailedException,
    UserNotFoundException,
    UserAlreadyDeletedException,
    CannotDeleteActiveCommanderException,
)
from src.core.celery import celery_app


logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, db_session: AsyncSession):
        self.db_session: AsyncSession = db_session
        self.crud_user = CRUDUser(db_session=self.db_session)
        self.crud_incident = CrudIncident(db_session=self.db_session)

    async def register_user(self, *, user_in: UserCreate) -> User:
        """
        Registers a new user and queues a verification email task.
        """

        existing_user = await self.crud_user.get_user_by_username_or_email(
            username=user_in.username,
            email=user_in.email
        )

        if existing_user:
            raise DuplicateResourceException(
                detail="Username or email is already registered."
            )

        hashed_password = get_password_hash(user_in.password)

        user_data = UserCreateInternal(
            **user_in.model_dump(),
            hashed_password=hashed_password
        )

        created_user = await self.crud_user.create_user(
            user_in=user_data
        )

        await self.db_session.commit()

        # Try to queue the task,
        # but log errors instead
        # of raising them.
        try:
            celery_app.send_task(
                "tasks.send_verification_email",
                args=[
                    str(created_user.id)]
            )

            logger.info(
                "Verification email task successfully queued for "
                f"user ID: {created_user.id}"
            )

        except Exception:
            # Log the full exception info for debugging,
            # but don't fail the request.
            logger.error(
                "Failed to queue verification email "
                f"task for user {created_user.id}.",
                exc_info=True
            )

        return created_user

    async def get_users_list(
        self,
        *,
        skip: int,
        limit: int
    ) -> List[User]:
        """
        Retrieves a list of users with pagination.
        """
        return await self.crud_user.get_users(
            skip=skip, limit=limit
        )

    async def get_user_by_id(self, *, user_id: UUID) -> User:
        """
        Retrieves a single user by their ID,
        raising an error if not found.
        """

        user = await self.crud_user.get_user_by_id(
            user_id=user_id
        )

        if not user:
            raise UserNotFoundException(
                identifier=str(user_id)
            )

        return user

    async def update_user_profile(
        self,
        *,
        current_user: User,
        user_in: UserUpdate
    ) -> User:
        """
        Updates a user's profile,
        checking for email/username conflicts.
        """

        update_data = user_in.model_dump(exclude_unset=True)

        if "email" in update_data and update_data[
            "email"
        ] != current_user.email:
            existing_user = await self.crud_user.get_user_by_email(
                email=update_data["email"]
            )

            if existing_user and existing_user.id != current_user.id:
                raise DuplicateResourceException(
                    detail="Email is already registered by another user."
                )

            update_data["is_email_verified"] = False

        if "username" in update_data and update_data[
            "username"
        ] != current_user.username:

            existing_user = await self.crud_user.get_user_by_username(
                username=update_data["username"]
            )

            if existing_user and existing_user.id != current_user.id:
                raise DuplicateResourceException(
                    detail="Username is already taken."
                )

        updated_user = await self.crud_user.update_user(
            db_user_to_update=current_user,
            user_in_update_data=update_data
        )

        await self.db_session.commit()
        await self.db_session.refresh(updated_user)

        return updated_user

    async def change_password(
        self,
        *,
        current_user: User,
        password_in: UserUpdatePassword
    ) -> User:
        """
        Changes the password for the current user.
        """

        if not verify_password(
            password_in.current_password,
            current_user.hashed_password
        ):
            raise AuthenticationFailedException(
                detail="Incorrect current password."
            )

        if password_in.current_password == password_in.new_password:
            raise InvalidInputException(
                detail=(
                    "New password cannot be the same as the current one."
                )
            )

        new_hashed_password = get_password_hash(password_in.new_password)

        updated_user = await self.crud_user.update_user(
            db_user_to_update=current_user,
            user_in_update_data={
                "hashed_password": new_hashed_password
            }
        )

        await self.db_session.commit()
        await self.db_session.refresh(updated_user)

        return updated_user

    async def get_commander_list(self) -> List[User]:
        """
        Retrieves a list of all active incident commanders.
        """
        return await self.crud_user.get_commanders()

    async def soft_delete_user(
        self,
        *,
        user_to_delete_id: UUID,
        performing_user: User
    ) -> User:
        """
        Soft deletes a user,
        enforcing business rules
        like not deleting oneself
        or active commanders.
        """

        if user_to_delete_id == performing_user.id:
            raise InvalidOperationException(
                detail="Users cannot delete their own account."
            )

        user_to_delete = await self.get_user_by_id(
            user_id=user_to_delete_id
        )

        if user_to_delete.is_deleted:
            raise UserAlreadyDeletedException()

        is_commander = await self.crud_incident.is_user_active_commander(
            user_id=user_to_delete.id
        )

        if is_commander:
            raise CannotDeleteActiveCommanderException()

        update_data = {
            "is_deleted": True,
            "deleted_at": datetime.now(timezone.utc),
            "is_active": False,
            "email": (
                f"deleted_{user_to_delete_id}_{user_to_delete.email}"
            ),
            "username": (
                f"deleted_{user_to_delete_id}_{user_to_delete.username}"
            )
        }

        deleted_user = await self.crud_user.update_user(
            db_user_to_update=user_to_delete,
            user_in_update_data=update_data
        )

        await self.db_session.commit()
        await self.db_session.refresh(deleted_user)

        return deleted_user
