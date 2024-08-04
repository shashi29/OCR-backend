import tempfile
import os

from typing import List, Dict, Any
from fastapi import UploadFile
from langchain_unstructured import UnstructuredLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAI

from app.repositories.storage_repository import StorageRepository
from app.repositories.vector_db_repository import VectorDBRepository
from app.models.document import ProcessedData, SearchResult
from app.config import Config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentService:
    def __init__(self, storage_repo: StorageRepository, vector_db_repo: VectorDBRepository):
        self.storage_repo = storage_repo
        self.vector_db_repo = vector_db_repo
        self.ocr_strategy = Config.UNSTRUCTURE__OCR_STRATEGY
        self.chunk_size = Config.LANGCHAIN__CHUNK_SIZE
        self.chunk_overlap = Config.LANGCHAIN__CHUNK_OVERLAP
        self.llm_service = OpenAI(temperature=OPENAI_TEMPERATURE, model=Config.OPENAI_LLM_MODEL)


    async def process_pdf(self, file: UploadFile) -> List[dict]:
        tmp_path = None
        try:
            # Create a temporary file and write the uploaded file content to it
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(await file.read())
                tmp_path = tmp.name

            logger.info(f"Temporary file created at: {tmp_path}")

            # Process the PDF using the partition function
            partition_output = partition(
                filename=tmp_path,
                extract_image_block_to_payload=True,
                extract_images_in_pdf=True,
                pdf_infer_table_structure=True,
                strategy="hi_res",
                max_characters=4000,
                new_after_n_chars=3800,
                combine_text_under_n_chars=2000
            )

            processed_data = [page.to_dict() for page in partition_output]

            # Optional: Upload the processed file and JSON data to storage
            # self.storage_repo.upload_file(file.filename, tmp_path)
            # self.storage_repo.upload_json(f"{file.filename}.json", [data.dict() for data in processed_data])

            # Add processed data to vector database
            self.vector_db_repo.add_data_to_collection(processed_data)
            
            logger.info(f"Processed PDF data for file: {file.filename}")

            return processed_data
        except Exception as e:
            logger.error(f"Error processing PDF document: {e}", exc_info=True)
            raise
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
                logger.info(f"Temporary file at {tmp_path} has been removed")

    async def process_docs_unstructure(self, file: UploadFile, collection: str) -> List[dict]:
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(await file.read())
                tmp_path = tmp.name

            logger.info(f"Temporary file created at: {tmp_path}")

            # Load the document using the UnstructuredLoader
            loader = UnstructuredLoader(tmp_path, strategy=self.ocr_strategy)
            documents = loader.load()

            # Split the loaded documents into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=int(self.chunk_size), 
                chunk_overlap=int(self.chunk_overlap)
            )
            processed_data = text_splitter.split_documents(documents=documents)

            # Add processed data to vector database
            self.vector_db_repo.add_data_to_collection_unstructure(processed_data, collection)
            processed_data = [page.to_json() for page in processed_data]
            
            logger.info(f"Processed unstructured data for file: {file.filename}")

            return processed_data
        except Exception as e:
            logger.error(f"Error processing unstructured document: {e}", exc_info=True)
            raise
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
                logger.info(f"Temporary file at {tmp_path} has been removed")

    def search_documents(self, query: str, limit: int, collection_name: str) -> dict[str, List[dict]]:
        try:
            # Perform the search
            results = self.vector_db_repo.search(query, limit, collection_name)
            
            # Check if results are empty
            if not results:
                logger.info(f"No results found for query: {query}")
                return {"final_answer": "No results found", "metadata": []}

            # Process the results to include final answer and metadata
            final_answer = self._generate_final_answer(results, query)
            #final_answer = ""
            metadata = [result["payload"] for result in results]
            
            logger.info(f"Search completed for query: {query} with {len(results)} results.")
            return {"final_answer": final_answer, "metadata": metadata}

        except Exception as e:
            logger.error(f"Error searching documents: {e}", exc_info=True)
            raise

    def _generate_final_answer(self, results: List[Dict[str, Any]], query: str) -> str:
        texts = [result["payload"]["text"] for result in results]
        combined_text = "\n".join(texts)
        formatted_prompt = self._get_formatted_prompt(combined_text, query)
        
        try:
            final_answer = self.llm_service.invoke(formatted_prompt)
            return final_answer
        except Exception as e:
            logger.error(f"Error generating final answer with LLM: {e}", exc_info=True)
            return "Failed to generate final answer."

    @staticmethod
    def _get_formatted_prompt(combined_text: str, query: str) -> str:
        return f"""
        Given the following information: {combined_text}
        Please answer this question based solely on the information provided above: {query}
        Remember to use only the information from the given text in your answer. 
        Do not introduce any external information or make assumptions beyond what is explicitly stated in the text.
        """

# Example usage
# Initialize the DocumentService with required parameters
# document_service = DocumentService(storage_repo=StorageRepository(), vector_db_repo=VectorDBRepository())
# processed_data = await document_service.process_docs_unstructure(file)
# search_results = document_service.search_documents(query="example", limit=10)
