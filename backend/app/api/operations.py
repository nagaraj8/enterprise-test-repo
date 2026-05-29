from fastapi import APIRouter, Query

from app.services.operations_repository import list_deployments, list_services

router = APIRouter()


@router.get("/services")
def services(limit: int = Query(default=50, ge=1, le=200)):
    return {
        "services": list_services(limit=limit)
    }


@router.get("/deployments")
def deployments(
    service_name: str | None = None,
    limit: int = Query(default=25, ge=1, le=100),
):
    return {
        "deployments": list_deployments(
            service_name=service_name,
            limit=limit,
        )
    }
