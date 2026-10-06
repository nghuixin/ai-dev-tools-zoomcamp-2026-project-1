from app.deps import get_store
from app.models import CreateSiteRequest, Site
from app.store import Store
from fastapi import APIRouter, Depends, status

router = APIRouter(tags=["sites"])


@router.get("/api/sites", response_model=list[Site])
def list_sites(study_id: int | None = None, store: Store = Depends(get_store)) -> list[Site]:
    return store.list_sites(study_id)


@router.post("/api/sites", response_model=Site, status_code=status.HTTP_201_CREATED)
def create_site(payload: CreateSiteRequest, store: Store = Depends(get_store)) -> Site:
    return store.create_site(payload)
