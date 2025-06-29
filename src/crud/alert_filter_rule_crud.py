from uuid import UUID
from typing import List, Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import (
    AsyncSession
)

from src.models.alert_filter_rule import (
    AlertFilterRule
)


class CrudAlertFilterRule:

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def create_rule(
        self,
        *,
        rule: AlertFilterRule
    ) -> AlertFilterRule:

        self.db.add(rule)
        await self.db.flush()
        await self.db.refresh(rule)

        return rule

    async def get_rule_by_id(
        self,
        *,
        rule_id: UUID
    ) -> Optional[AlertFilterRule]:

        statement = select(AlertFilterRule).where(
            AlertFilterRule.id == rule_id
        )

        result = await self.db.exec(statement)

        return result.first()

    async def get_rule_by_name(
        self,
        *,
        name: str
    ) -> Optional[AlertFilterRule]:

        statement = select(AlertFilterRule).where(
            AlertFilterRule.rule_name == name
        )

        result = await self.db.exec(statement)

        return result.first()

    async def get_all_rules(
        self,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[AlertFilterRule]:

        statement = select(AlertFilterRule).order_by(
            AlertFilterRule.rule_name
        ).offset(offset=skip).limit(limit=limit)

        result = await self.db.exec(statement)

        return list(result.all())

    async def get_all_active_rules(
        self
    ) -> List[AlertFilterRule]:

        statement = select(
            AlertFilterRule
        ).where(
            AlertFilterRule.is_active == True
        ).order_by(
            AlertFilterRule.rule_name
        )

        result = await self.db.exec(
            statement
        )

        return list(result.all())

    async def update_rule(
        self,
        *,
        db_rule: AlertFilterRule,
        update_data: dict
    ) -> AlertFilterRule:

        for (
            field,
            value
        ) in update_data.items():
            if value is not None:
                setattr(
                    db_rule,
                    field,
                    value
                )

        self.db.add(db_rule)
        await self.db.flush()
        await self.db.refresh(
            db_rule
        )

        return db_rule

    async def delete_rule(
        self,
        *,
        rule: AlertFilterRule
    ) -> None:

        await self.db.delete(rule)
        await self.db.flush()
