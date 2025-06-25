from uuid import UUID
from pydantic import BaseModel, Field
from typing import Optional

from src.models.enums import MatchTypeEnum


class AlertFilterRuleBase(BaseModel):
    rule_name: str = Field(max_length=255)
    description: Optional[str] = Field(None, max_length=512)
    target_field: str = Field(
        max_length=100,
        description="e.g., 'labels.severity' or 'annotations.summary'"
    )
    match_type: MatchTypeEnum
    match_value: str = Field(max_length=255)
    is_active: bool = True
    is_exclusion_rule: bool = False


class AlertFilterRuleCreate(AlertFilterRuleBase):
    pass


class AlertFilterRuleUpdate(BaseModel):
    rule_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=512)
    target_field: Optional[str] = Field(None, max_length=100)
    match_type: Optional[MatchTypeEnum] = None
    match_value: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None
    is_exclusion_rule: Optional[bool] = None


class AlertFilterRuleRead(AlertFilterRuleBase):
    id: UUID

    class Config:
        from_attributes = True
