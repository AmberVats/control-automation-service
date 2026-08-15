from typing import List
from fastapi import APIRouter
from src.components.registry import ComponentRegistry
from src.api.schemas import ComponentCatalogueItem

router = APIRouter(prefix="/components", tags=["Component Catalogue"])


@router.get("", response_model=List[ComponentCatalogueItem])
def list_available_components():
    """
    Discoverable component catalogue for the Citizen Developer framework.
    Lists all registered components, categories, and parameter schemas.
    """
    registry = ComponentRegistry.default()
    catalogue = registry.get_catalogue()
    return [ComponentCatalogueItem.model_validate(item) for item in catalogue]
