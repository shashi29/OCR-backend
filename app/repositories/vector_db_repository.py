import uuid
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http.models import UpdateStatus
from qdrant_client.models import PointStruct, VectorParams, Distance
from sentence_transformers import SentenceTransformer
from app.config import Config
from collections import OrderedDict
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# LRU Cache class
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

# Initialize LRU cache
model_cache = LRUCache(capacity=1)  # Adjust capacity as needed

class VectorDBRepository:
    def __init__(self):
        self.qdrant_client = QdrantClient(url=Config.QDRANT_URL, api_key=Config.QDRANT_API_KEY)
        self.collection_name = Config.QDRANT_COLLECTION_NAME

        # Load the embedding model with caching
        self.embedding_model = self._load_embedding_model(Config.EMBEDDING_MODEL)

    def _load_embedding_model(self, model_name: str) -> SentenceTransformer:
        model = model_cache.get(model_name)
        if model is None:
            logger.info(f"Loading embedding model: {model_name}")
            model = SentenceTransformer(model_name, trust_remote_code=True)
            model_cache.put(model_name, model)
        return model

    def add_data_to_collection(self, data: List[Dict[str, Any]]):
        points = []
        for item in data:
            text_id = str(uuid.uuid4())
            vector = self.embedding_model.encode(item["text"]).tolist()
            payload = {
                "text_id": text_id,
                "text": item["text"],
                "text_type": item["type"],
                "languages": item["metadata"].get("languages"),
                "filetype": item["metadata"].get("filetype"),
                "last_modified": item["metadata"].get("last_modified"),
                "page_number": item["metadata"].get("page_number"),
            }
            point = PointStruct(id=text_id, vector=vector, payload=payload)
            points.append(point)

        try:
            operation_info = self.qdrant_client.upsert(
                collection_name=self.collection_name,
                wait=True,
                points=points
            )
            if operation_info.status != UpdateStatus.COMPLETED:
                raise Exception("Failed to insert data")
            logger.info(f"Successfully inserted data into collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error inserting data: {e}")
            raise

    def add_data_to_collection_unstructured(self, data: List[Dict[str, Any]], collection_name: str):
        points = []
        for item in data:
            text_id = str(uuid.uuid4())
            page_content = item.to_json()['kwargs']['page_content']
            vector = self.embedding_model.encode(page_content).tolist()
            metadata = item.to_json()['kwargs']['metadata']
            payload = {
                "text_id": text_id,
                "text": page_content,
                "category": metadata.get('category'),
                "languages": metadata.get("languages"),
                "filetype": metadata.get("filetype"),
                "last_modified": metadata.get("last_modified"),
                "coordinates": metadata.get("coordinates", {}).get('points'),
                "page_number": metadata.get("page_number"),
            }
            point = PointStruct(id=text_id, vector=vector, payload=payload)
            points.append(point)

        try:
            operation_info = self.qdrant_client.upsert(
                collection_name=collection_name,
                wait=True,
                points=points
            )
            if operation_info.status != UpdateStatus.COMPLETED:
                raise Exception("Failed to insert data")
            logger.info(f"Successfully inserted data into collection: {collection_name}")
        except Exception as e:
            logger.error(f"Error inserting data: {e}")
            raise

    def search(self, query: str, limit: int, collection_name: str) -> List[Dict[str, Any]]:
        query_vector = self.embedding_model.encode(query).tolist()
        try:
            hits = self.qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit
            )
            results = [{"score": hit.score, "payload": hit.payload} for hit in hits]
            logger.info(f"Search completed successfully in collection: {collection_name}")
            return results
        except Exception as e:
            logger.error(f"Error during search: {e}")
            raise

    def create_collection(self, collection_name: str):
        try:
            self.qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_model.get_sentence_embedding_dimension(),
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Collection created successfully: {collection_name}")
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            raise

    def delete_collection(self, collection_name: str):
        try:
            self.qdrant_client.delete_collection(collection_name=collection_name)
            logger.info(f"Collection deleted successfully: {collection_name}")
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            raise

    def get_all_collections_details(self) -> Dict[str, Dict[str, Any]]:
        try:
            collections = self.qdrant_client.get_collections().collections
            all_details = {}
            
            for collection in collections:
                collection_name = collection.name
                collection_info = self.qdrant_client.get_collection(collection_name)
                all_details[collection_name] = collection_info.dict()
            
            logger.info("Retrieved details for all collections.")
            return all_details
        except Exception as e:
            logger.error(f"Error retrieving collection details: {e}")
            raise

    def get_collection_details(self, collection_name: str) -> Dict[str, Any]:
        try:
            collection_info = self.qdrant_client.get_collection(collection_name=collection_name)
            logger.info(f"Retrieved details for collection: {collection_name}")
            return collection_info.dict()
        except Exception as e:
            logger.error(f"Error retrieving details for collection {collection_name}: {e}")
            raise

    def check_collection_exists(self, collection_name: str):
        try:
            collection_info = self.qdrant_client.collection_exists(collection_name=collection_name)
            logger.info(f"Retrieved details for collection: {collection_name}")
            return collection_info
        except Exception as e:
            logger.error(f"Error retrieving details for collection {collection_name}: {e}")
            raise        