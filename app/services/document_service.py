import logging
from typing import List, Dict, Any
from fastapi import UploadFile, HTTPException
from app.repositories.storage_repository import StorageRepository
from app.repositories.vector_db_repository import VectorDBRepository
from app.core.file_processor import FileProcessor
from app.config import Config
from langchain_openai import OpenAI

logger = logging.getLogger(__name__)

class DocumentService:
    def __init__(self, storage_repo: StorageRepository, vector_db_repo: VectorDBRepository):
        self.storage_repo = storage_repo
        self.vector_db_repo = vector_db_repo
        self.file_processor = FileProcessor()
        self.llm_service = OpenAI(temperature=Config.OPENAI_TEMPERATURE, model_name=Config.OPENAI_LLM_MODEL)

    async def process_docs_unstructure(self, file: UploadFile, collection: str) -> List[Dict[str, Any]]:
        """Process a document file and add it to the vector database."""
        try:
            processed_data = await self.file_processor.process(file)
            self.vector_db_repo.add_data_to_collection_unstructured(processed_data, collection)
            return processed_data
        except Exception as e:
            logger.error(f"Error processing document: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
        
    async def process_invoice_structure(self, file: UploadFile) -> List[Dict[str, Any]]:
        """Process a document file and add it to the vector database."""
        try:
            processed_data = await self.file_processor.process_invoice(file)
            logger.info(processed_data)
            #self.vector_db_repo.add_data_to_collection_unstructured(processed_data, collection)
            return processed_data
        except Exception as e:
            logger.error(f"Error processing document: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    def search_documents(self, query: str, limit: int, collection_name: str) -> Dict[str, Any]:
        """Search documents in the vector database."""
        try:
            results = self.vector_db_repo.search(query, limit, collection_name)
            if not results:
                return {"final_answer": "No results found", "metadata": []}
            final_answer = self._generate_final_answer(results, query)
            metadata = [result["payload"] for result in results]
            return {"final_answer": final_answer, "metadata": metadata}
        except Exception as e:
            logger.error(f"Error searching documents: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Error searching documents")

    def _generate_final_answer(self, results: List[Dict[str, Any]], query: str) -> str:
        """Generate a final answer using the LLM service."""
        texts = [result["payload"]["text"] for result in results]
        combined_text = "\n".join(texts)
        formatted_prompt = self._get_formatted_prompt(combined_text, query)
        try:
            return self.llm_service.invoke(formatted_prompt)
        except Exception as e:
            logger.error(f"Error generating final answer with LLM: {e}", exc_info=True)
            return "Failed to generate final answer."

    @staticmethod
    def _get_formatted_prompt(combined_text: str, query: str) -> str:
        """Format the prompt for the LLM service."""
        return f"""
        Context:
        {combined_text}

        Question:
        {query}

        Instructions:
        1. Answer the question based exclusively on the information provided in the Context.
        2. Do not introduce any external knowledge or make assumptions beyond what is explicitly stated in the Context.
        3. If the Context does not contain sufficient information to answer the question fully, state this clearly in your response.
        4. Cite specific parts of the Context to support your answer when possible.
        5. If any part of the question cannot be answered using the given information, explain why.

        Please provide your answer below:
        """