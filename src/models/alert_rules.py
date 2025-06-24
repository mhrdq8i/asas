from typing import Annotated
from sqlmodel import Field

from src.models.base import BaseEntity
from src.models.enums import MatchTypeEnum


class AlertFilterRule(BaseEntity, table=True):
    __tablename__ = "alert_filter_rules"

    rule_name: Annotated[
        str,
        Field(
            max_length=255,
            nullable=False,
            unique=True,
            description="A unique, human-readable name for the rule."
        )
    ]

    description: Annotated[
        str | None,
        Field(
            max_length=512,
            nullable=True,
            description="A brief description of what the rule does."
        )
    ]

    target_field: Annotated[
        str,
        Field(
            max_length=100,
            nullable=False,
            description=(
                "The field in the alert payload to check "
                "(e.g., 'labels.severity', 'annotations.summary')."
            )
        )
    ]

    match_type: Annotated[
        MatchTypeEnum,
        Field(
            default=MatchTypeEnum.EQUALS,
            nullable=False,
            description="The type of comparison to perform."
        )
    ]

    match_value: Annotated[
        str,
        Field(
            max_length=255,
            nullable=False,
            description="The value to match against."
        )
    ]

    is_active: Annotated[
        bool,
        Field(
            default=True,
            nullable=False,
            index=True,
            description=(
                "Whether the rule is currently "
                "active and should be applied."
            )
        )
    ]

    is_exclusion_rule: Annotated[
        bool,
        Field(
            default=False,
            nullable=False,
            description=(
                "If true, an alert matching this rule will be EXCLUDED, "
                "even if it matches other inclusion rules."
            )
        )
    ]
