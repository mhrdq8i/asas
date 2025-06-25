from uuid import UUID
from typing import List, Annotated
from fastapi import APIRouter, Depends, status, Response

from src.dependencies.auth_deps import get_current_active_superuser
from src.dependencies.service_deps import get_alert_filter_rule_service
from src.services.alert_filter_rule_service import AlertFilterRuleService
from src.api.v1.schemas.alert_filter_rule_schemas import (
    AlertFilterRuleRead,
    AlertFilterRuleCreate,
    AlertFilterRuleUpdate
)

router = APIRouter(
    prefix="/admin/alert-rules",
    dependencies=[
        Depends(get_current_active_superuser)
    ]
)


@router.post(
    "/",
    response_model=AlertFilterRuleRead,
    status_code=status.HTTP_201_CREATED
)
async def create_alert_filter_rule(
    rule_in: AlertFilterRuleCreate,
    service: Annotated[
        AlertFilterRuleService,
        Depends(get_alert_filter_rule_service)
    ]
):

    return await service.create(rule_in=rule_in)


@router.get(
    "/",
    response_model=List[AlertFilterRuleRead]
)
async def get_all_alert_filter_rules(
    service: Annotated[
        AlertFilterRuleService,
        Depends(get_alert_filter_rule_service)
    ],
    skip: int = 0,
    limit: int = 100
):

    return await service.get_all(skip=skip, limit=limit)


@router.get(
    "/{rule_id}",
    response_model=AlertFilterRuleRead
)
async def get_alert_filter_rule(
    rule_id: UUID,
    service: Annotated[
        AlertFilterRuleService,
        Depends(get_alert_filter_rule_service)
    ]
):

    return await service.get_by_id(rule_id=rule_id)


@router.put(
    "/{rule_id}",
    response_model=AlertFilterRuleRead
)
async def update_alert_filter_rule(
    rule_id: UUID,
    update_data: AlertFilterRuleUpdate,
    service: Annotated[
        AlertFilterRuleService,
        Depends(get_alert_filter_rule_service)
    ]
):
    return await service.update(
        rule_id=rule_id,
        update_data=update_data
    )


@router.delete(
    "/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_alert_filter_rule(
    rule_id: UUID,
    service: Annotated[
        AlertFilterRuleService,
        Depends(get_alert_filter_rule_service)
    ]
):

    await service.delete(rule_id=rule_id)

    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )
