from uuid import UUID
from typing import List

from sqlmodel.ext.asyncio.session import AsyncSession

from src.crud.alert_filter_rule_crud import (
    CrudAlertFilterRule
)
from src.models.alert_filter_rule import (
    AlertFilterRule
)
from src.api.v1.schemas.alert_filter_rule_schemas import (
    AlertFilterRuleCreate,
    AlertFilterRuleUpdate
)
from src.exceptions.common_exceptions import (
    ResourceNotFoundException,
    DuplicateResourceException
)


class AlertFilterRuleService:

    def __init__(
        self,
        db_session: AsyncSession
    ):
        self.db_session = db_session
        self.crud = CrudAlertFilterRule(
            db_session=db_session
        )

    async def get_by_id(
        self,
        *,
        rule_id: UUID
    ) -> AlertFilterRule:

        rule = await self.crud.get_rule_by_id(
            rule_id=rule_id
        )

        if not rule:
            raise ResourceNotFoundException(
                resource_name="AlertFilterRule",
                identifier=rule_id
            )

        return rule

    async def get_all(
        self,
        *,
        skip: int,
        limit: int
    ) -> List[AlertFilterRule]:

        return await self.crud.get_all_rules(
            skip=skip,
            limit=limit
        )

    async def create(
        self,
        *,
        rule_in: AlertFilterRuleCreate
    ) -> AlertFilterRule:

        existing_rule = await self.crud.get_rule_by_name(
            name=rule_in.rule_name
        )

        if existing_rule:
            raise DuplicateResourceException(
                "AlertFilterRule with name "
                f"'{rule_in.rule_name}' "
                "already exists."
            )

        db_rule = AlertFilterRule.model_validate(
            rule_in
        )

        new_rule = await self.crud.create_rule(
            rule=db_rule
        )
        await self.db_session.commit()
        await self.db_session.refresh(
            instance=new_rule
        )

        return new_rule

    async def update(
        self,
        *,
        rule_id: UUID,
        update_data: AlertFilterRuleUpdate
    ) -> AlertFilterRule:

        db_rule = await self.get_by_id(
            rule_id=rule_id
        )

        update_dict = update_data.model_dump(
            exclude_unset=True
        )

        if not update_dict:
            return db_rule

        if 'rule_name' in update_dict and update_dict[
            'rule_name'
        ] != db_rule.rule_name:
            existing_rule = await self.crud.get_rule_by_name(
                name=update_dict['rule_name']
            )

            if existing_rule:
                raise DuplicateResourceException(
                    "AlertFilterRule with name "
                    f"'{update_dict['rule_name']}' "
                    "already exists."
                )

        updated_rule = await self.crud.update_rule(
            db_rule=db_rule,
            update_data=update_dict
        )

        await self.db_session.commit()
        await self.db_session.refresh(
            instance=updated_rule
        )

        return updated_rule

    async def delete(
        self,
        *,
        rule_id: UUID
    ) -> None:

        rule_to_delete = await self.get_by_id(
            rule_id=rule_id
        )

        await self.crud.delete_rule(
            rule=rule_to_delete
        )
        await self.db_session.commit()
