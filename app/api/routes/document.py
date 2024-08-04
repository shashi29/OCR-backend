from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from typing import List
from app.models.document import ProcessedData, SearchRequest, SearchResult
from app.services.document_service import DocumentService
from app.api.dependencies import get_document_service
import logging

router = APIRouter()

@router.post("/process-document/", response_model=List[dict])
async def process_document(
    collection_name: str,
    file: UploadFile = File(...),
    document_service: DocumentService = Depends(get_document_service)
):  
    try:
        return await document_service.process_docs_unstructure(file, collection_name)
        logging.info(f" Insert Embedding in collection : {collection_name}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing File: {str(e)}")

@router.post("/search/", response_model=dict)
async def search_documents(
    request: SearchRequest,
    document_service: DocumentService = Depends(get_document_service)
):
    try:
        return document_service.search_documents(request.query, request.limit, request.collection_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching documents: {str(e)}")