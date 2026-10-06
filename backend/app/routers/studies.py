from app.deps import get_store
from app.models import Study
from app.store import Store
from fastapi import APIRouter, Depends

router = APIRouter(tags=["studies"])


@router.get("/api/studies", response_model=list[Study])
def list_studies(store: Store = Depends(get_store)) -> list[Study]:
    return store.list_studies()
