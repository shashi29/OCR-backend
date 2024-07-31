from app.repositories.vector_db_repository import VectorDBRepository

class CollectionService:
    def __init__(self, vector_db_repo: VectorDBRepository):
        self.vector_db_repo = vector_db_repo

    def create_collection(self, collection_name: str):
        self.vector_db_repo.create_collection(collection_name)

    def delete_collection(self, collection_name: str):
        self.vector_db_repo.delete_collection(collection_name)

    def get_collection_details(self, collection_name: str):
        return self.vector_db_repo.get_collection_details(collection_name)