from app.repositories.storage_repository import StorageRepository
from app.repositories.vector_db_repository import VectorDBRepository
from app.services.document_service import DocumentService
from app.services.collection_service import CollectionService

def get_document_service():
    storage_repo = StorageRepository()
    vector_db_repo = VectorDBRepository()
    return DocumentService(storage_repo, vector_db_repo)

def get_collection_service():
    vector_db_repo = VectorDBRepository()
    return CollectionService(vector_db_repo)