from fastapi import APIRouter, Depends, HTTPException
from app.models.collection import CollectionRequest
from app.services.collection_service import CollectionService
from app.api.dependencies import get_collection_service

router = APIRouter()

@router.post("/create/")
async def create_collection(
    request: CollectionRequest,
    collection_service: CollectionService = Depends(get_collection_service)
):
    try:
        collection_service.create_collection(request.collection_name)
        return {"message": f"Collection {request.collection_name} created successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create collection: {str(e)}")

@router.post("/delete/")
async def delete_collection(
    request: CollectionRequest,
    collection_service: CollectionService = Depends(get_collection_service)
):
    try:
        collection_service.delete_collection(request.collection_name)
        return {"message": f"Collection {request.collection_name} deleted successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete collection: {str(e)}")

@router.post("/details/")
async def get_collection_details(
    request: CollectionRequest,
    collection_service: CollectionService = Depends(get_collection_service)
):
    try:
        details = collection_service.get_collection_details(request.collection_name)
        return {"message": details}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get collection details: {str(e)}")