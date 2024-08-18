import os
import tempfile
import logging
from typing import List, Dict, Any
from fastapi import UploadFile
import pdfplumber
import easyocr
import numpy as np
from pdf2image import convert_from_path
from langchain_unstructured import UnstructuredLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.config import Config
from collections import OrderedDict

logger = logging.getLogger(__name__)

class LRUCache:
    def __init__(self, capacity: int):
        self.cache = OrderedDict()
        self.capacity = capacity

    def get(self, key: str):
        if key not in self.cache:
            return None
        else:
            self.cache.move_to_end(key)
            return self.cache[key]

    def put(self, key: str, value: Any):
        if len(self.cache) >= self.capacity:
            self.cache.popitem(last=False)
        self.cache[key] = value
        self.cache.move_to_end(key)

class FileProcessor:
    def __init__(self):
        self.ocr_strategy = Config.UNSTRUCTURE__OCR_STRATEGY
        self.chunk_size = Config.LANGCHAIN__CHUNK_SIZE
        self.chunk_overlap = Config.LANGCHAIN__CHUNK_OVERLAP
        self.model_cache = LRUCache(capacity=5)  # Cache with capacity for 5 models

    def load_model(self, languages: list):
        languages_key = ','.join(sorted(languages))
        cached_model = self.model_cache.get(languages_key)
        if cached_model is not None:
            return cached_model

        # Load the model if not in cache
        model = easyocr.Reader(languages)
        self.model_cache.put(languages_key, model)

        return model

    async def process(self, file: UploadFile) -> List[Dict[str, Any]]:
        """Process a file based on its type."""
        file_extension = self._get_file_extension(file.filename)
        tmp_path = await self._save_temp_file(file)
        try:
            return self._process_unstructured(tmp_path)
        finally:
            self._remove_temp_file(tmp_path)
            
    async def process_invoice(self, file: UploadFile) -> List[Dict[str, Any]]:
        """Process a file based on its type."""
        file_extension = self._get_file_extension(file.filename)
        tmp_path = await self._save_temp_file(file)
        try:
            if file_extension == '.pdf':
                return self._process_pdf(tmp_path)
            elif file_extension in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
                return self._process_image(tmp_path)
            else:
                raise "Currently we support pdf and image format for invoice"
        finally:
            self._remove_temp_file(tmp_path)

    def _process_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """Process a PDF file."""
        if self._is_searchable_pdf(file_path):
            logger.info(f"Running pdf plumber on pdf: {file_path}")
            return self._process_searchable_pdf(file_path)
        else:
            logger.info(f"Running EasyOCR on pdf: {file_path}")
            return self._process_non_searchable_pdf(file_path)

    def _process_image(self, file_path: str) -> List[Dict[str, Any]]:
        """Process an image file."""
        return self._process_image_file(file_path)

    def _process_unstructured(self, file_path: str) -> List[Dict[str, Any]]:
        """Process an unstructured document."""
        loader = UnstructuredLoader(file_path, strategy=self.ocr_strategy)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=int(self.chunk_size),
            chunk_overlap=int(self.chunk_overlap)
        )
        processed_data = text_splitter.split_documents(documents=documents)
        return [page.to_json() for page in processed_data]

    @staticmethod
    def _is_searchable_pdf(pdf_path: str) -> bool:
        """Check if a PDF is searchable."""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                return bool(pdf.pages[0].extract_text())
        except Exception as e:
            logger.error(f"Error checking if PDF is searchable: {e}", exc_info=True)
            return False

    @staticmethod
    def _get_file_extension(filename: str) -> str:
        """Get the file extension from a filename."""
        return os.path.splitext(filename)[1].lower()

    @staticmethod
    async def _save_temp_file(file: UploadFile) -> str:
        """Save an uploaded file to a temporary location."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp:
            tmp.write(await file.read())
            return tmp.name

    @staticmethod
    def _remove_temp_file(tmp_path: str) -> None:
        """Remove a temporary file."""
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
            logger.info(f"Temporary file at {tmp_path} has been removed")

    def _process_searchable_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """Process a searchable PDF."""
        pages_data = []
        with pdfplumber.open(file_path) as pdf:
            for page_number, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                pages_data.append({
                    'page_number': page_number + 1,
                    'text': text
                })
        return pages_data

    def _process_non_searchable_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """Process a non-searchable PDF."""
        reader = self.load_model(['en'])
        pages_data = []
        images = convert_from_path(file_path)
        for page_number, image in enumerate(images):
            image = np.array(image)
            result = reader.readtext(image, detail=0)
            text = ' '.join(result)
            pages_data.append({
                'page_number': page_number + 1,
                'text': text
            })
        return pages_data

    def _process_image_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Process an image file."""
        reader = self.load_model(['en'])
        result = reader.readtext(file_path, detail=0)
        text = ' '.join(result)
        return [{
            'page_number': 1,
            'text': text
        }]
