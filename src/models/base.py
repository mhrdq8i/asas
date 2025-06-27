from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Annotated

from sqlalchemy.sql import func
from sqlmodel import SQLModel, Field, DateTime


class BaseEntity(SQLModel):
    """
    It provides common fields for other table models.
    """

    id: Annotated[
        UUID,
        Field(
            default_factory=uuid4,
            primary_key=True,
            index=True,
            nullable=False
        )
    ]

    created_at: Annotated[
        datetime,
        Field(
            default_factory=lambda: datetime.now(
                timezone.utc
            ),
            # This is for Pydantic validation
            nullable=False,
            # Specify SQLAlchemy type
            sa_type=DateTime(timezone=True),
            # Pass nullable to Column
            sa_column_kwargs={
                "server_default": func.now(),
                "nullable": False
            }
        )]

    updated_at: Annotated[
        datetime,
        Field(
            default_factory=lambda: datetime.now(
                timezone.utc
            ),
            # This is for Pydantic validation
            nullable=False,
            # Specify SQLAlchemy type
            sa_type=DateTime(timezone=True),
            # Pass nullable to Column
            sa_column_kwargs={
                "server_default": func.now(),
                "onupdate": func.now(),
                "nullable": False
            }
        )]
