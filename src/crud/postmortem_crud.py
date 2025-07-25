from uuid import UUID
from typing import Optional, List

from sqlmodel import select
from sqlmodel.ext.asyncio.session import (
    AsyncSession
)
from sqlalchemy.orm import selectinload

from src.models.postmortem import (
    PostMortem
)


class CrudPostmortem:

    def __init__(
        self,
        db_session: AsyncSession
    ):
        self.db: AsyncSession = db_session

    async def get_all_postmortems(
        self,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[PostMortem]:
        """
        Retrieve a list of users with pagination.
        """

        statement = select(
            PostMortem
        ).options(
            selectinload(
                PostMortem.contributing_factors
            ),
            selectinload(PostMortem.action_items),
            selectinload(PostMortem.approvals)
        )

        result = await self.db.exec(
            statement=statement
        )

        return result.all()

    async def get_postmortem_by_id(
        self,
        *,
        postmortem_id: UUID
    ) -> Optional[PostMortem]:
        """
        Retrieves a single post-mortem by its ID
        with all related data eagerly loaded.
        """

        statement = select(
            PostMortem
        ).where(
            PostMortem.id == postmortem_id
        ).options(
            selectinload(
                PostMortem.contributing_factors
            ),
            selectinload(PostMortem.action_items),
            selectinload(PostMortem.approvals)
        )

        result = await self.db.exec(
            statement=statement
        )

        return result.unique().first()

    async def get_postmortem_by_incident_id(
        self,
        *,
        incident_id: UUID
    ) -> Optional[PostMortem]:
        """
        Retrieves a post-mortem by
        its associated incident's ID.
        """

        statement = select(
            PostMortem
        ).where(
            PostMortem.incident_id == incident_id
        )

        result = await self.db.exec(
            statement=statement
        )

        return result.first()

    async def create_postmortem(
        self,
        *,
        postmortem: PostMortem
    ) -> PostMortem:
        """
        Adds a new PostMortem
        instance to the database.
        """

        self.db.add(
            instance=postmortem
        )
        await self.db.flush()
        await self.db.refresh(
            instance=postmortem
        )

        return postmortem

    async def update_postmortem(
        self,
        *,
        db_postmortem: PostMortem,
        update_data: dict
    ) -> PostMortem:
        """
        Updates a post-mortem
        instance with new data.
        """

        for (
            field,
            value
        ) in update_data.items():

            if value is not None:
                setattr(
                    db_postmortem,
                    field,
                    value
                )

        self.db.add(
            instance=db_postmortem
        )
        await self.db.flush()
        await self.db.refresh(
            instance=db_postmortem
        )

        return db_postmortem

    async def delete_postmortem(
        self,
        *,
        db_postmortem: PostMortem
    ) -> None:
        """
        Deletes a post-mortem
        instance from the database.
        """

        await self.db.delete(
            instance=db_postmortem
        )
        await self.db.flush()

    async def refresh_with_relationships(
        self,
        *,
        postmortem: PostMortem
    ) -> PostMortem:
        """
        Refreshes the given post-mortem instance
        and eagerly loads its relationships.
        This is crucial to prevent MissingGreenlet
        errors upon response serialization.
        """

        await self.db.refresh(
            postmortem,
            attribute_names=[
                "contributing_factors",
                "action_items",
                "approvals"
            ]
        )

        return postmortem
