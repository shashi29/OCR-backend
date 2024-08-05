import logging
import time

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from fastapi.responses import JSONResponse
from typing import List

from app.models.document import ProcessedData, SearchRequest, SearchResult
from app.services.document_service import DocumentService
from app.api.dependencies import get_document_service


router = APIRouter()

@router.post("/process-document/", response_model=List[dict])
async def process_document(
    collection_name: str,
    file: UploadFile = File(...),
    document_service: DocumentService = Depends(get_document_service)
):  
    start_time = time.time()
    try:
        pdf_output = await document_service.process_docs_unstructure(file, collection_name)
        end_time = time.time()
        duration = end_time - start_time
        
        logging.info(f"Start Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(start_time))}")
        logging.info(f"End Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(end_time))}")
        logging.info(f"Process Duration: {duration:.2f} seconds")
        logging.info(f"Success: True")
        logging.info(f"Status Code: {status.HTTP_200_OK}")
        logging.info(f"Inserted into Collection: {collection_name}")

        return JSONResponse(
            content=[{
                "message": "Document processed successfully",
                "start_time": time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(start_time)),
                "end_time": time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(end_time)),
                "process_duration": f"{duration:.2f} seconds",
                "success": True,
                "status_code": status.HTTP_200_OK,
                "collection_name": collection_name
            }],
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        
        logging.error(f"Start Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(start_time))}")
        logging.error(f"End Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(end_time))}")
        logging.error(f"Process Duration: {duration:.2f} seconds")
        logging.error(f"Success: False")
        logging.error(f"Status Code: {status.HTTP_500_INTERNAL_SERVER_ERROR}")
        logging.error(f"Error: {str(e)}")
        logging.error(f"Failed to Insert into Collection: {collection_name}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "Document processing failed",
                "start_time": time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(start_time)),
                "end_time": time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(end_time)),
                "process_duration": f"{duration:.2f} seconds",
                "success": False,
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "error": str(e),
                "collection_name": collection_name
            }
        )

@router.post("/search/", response_model=dict)
async def search_documents(
    request: SearchRequest,
    document_service: DocumentService = Depends(get_document_service)
):
    try:
        return document_service.search_documents(request.query, request.limit, request.collection_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching documents: {str(e)}")