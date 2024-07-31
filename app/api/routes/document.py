from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from typing import List
from app.models.document import ProcessedData, SearchRequest, SearchResult
from app.services.document_service import DocumentService
from app.api.dependencies import get_document_service

router = APIRouter()

@router.post("/process-document/", response_model=List[dict])
async def process_document(
    file: UploadFile = File(...),
    document_service: DocumentService = Depends(get_document_service)
):  
    try:
        return await document_service.process_pdf(file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing File: {str(e)}")

@router.post("/search/", response_model=List[SearchResult])
async def search_documents(
    request: SearchRequest,
    document_service: DocumentService = Depends(get_document_service)
):
    try:
        return document_service.search_documents(request.query, request.limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching documents: {str(e)}")