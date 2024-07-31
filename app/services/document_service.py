import tempfile
from typing import List
from fastapi import UploadFile
from unstructured.partition.auto import partition
from app.repositories.storage_repository import StorageRepository
from app.repositories.vector_db_repository import VectorDBRepository
from app.models.document import ProcessedData, SearchResult

class DocumentService:
    def __init__(self, storage_repo: StorageRepository, vector_db_repo: VectorDBRepository):
        self.storage_repo = storage_repo
        self.vector_db_repo = vector_db_repo

    async def process_pdf(self, file: UploadFile):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        partition_output = partition(
            filename=tmp_path,
            extract_image_block_to_payload=True,
            extract_images_in_pdf=True,
            pdf_infer_table_structure=True,
            strategy="hi_res",
            #chunking_strategy="by_title",
            max_characters=4000,
            new_after_n_chars=3800,
            combine_text_under_n_chars=2000
        )

        processed_data = [page.to_dict() for page in partition_output]
        # print(file.filename, tmp_path)
        #self.storage_repo.upload_file(file.filename, tmp_path)
        # self.storage_repo.upload_json(f"{file.filename}.json", [data.dict() for data in processed_data])

        # self.vector_db_repo.add_data_to_collection([data.dict() for data in processed_data])
        
        return processed_data

    def search_documents(self, query: str, limit: int) -> List[SearchResult]:
        results = self.vector_db_repo.search(query, limit)
        return [SearchResult(**result["payload"], score=result["score"]) for result in results]