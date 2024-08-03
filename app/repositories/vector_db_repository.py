import uuid
from typing import List, Dict
from qdrant_client import QdrantClient
from qdrant_client.http.models import UpdateStatus
from qdrant_client.models import PointStruct, VectorParams, Distance
from sentence_transformers import SentenceTransformer
from app.config import Config


class VectorDBRepository:
    def __init__(self):
        self.qdrant_client = QdrantClient(url=Config.QDRANT_URL, api_key=Config.QDRANT_API_KEY)
        self.collection_name = Config.QDRANT_COLLECTION_NAME
        self.embedding_model = SentenceTransformer(Config.EMBEDDING_MODEL, trust_remote_code=True)

    def add_data_to_collection_unstructure(self, data: List[Dict]):
        points = []
        for item in data:
            text_id = str(uuid.uuid4())
            vector = self.embedding_model.encode(item["text"])
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

        operation_info = self.qdrant_client.upsert(
            collection_name=self.collection_name,
            wait=True,
            points=points
        )

        if operation_info.status != UpdateStatus.COMPLETED:
            raise Exception("Failed to insert data")
        
    def add_data_to_collection_unstructure(self, data: List[Dict]):
        points = []
        for item in data:
            text_id = str(uuid.uuid4())
            vector = self.embedding_model.encode(item.to_json()['kwargs']['page_content'])
            payload = {
                "text_id": text_id,
                "text": item.to_json()['kwargs']['page_content'],
                "category": item.to_json()['kwargs']['metadata']['category'],
                "languages": item.to_json()['kwargs']['metadata']["languages"],
                "filetype": item.to_json()['kwargs']['metadata']['filetype'],
                "last_modified": item.to_json()['kwargs']['metadata']['last_modified'],
                "coordinates": item.to_json()['kwargs']['metadata']['coordinates']['points'],
                "page_number": item.to_json()['kwargs']['metadata']['page_number'],
            }
            point = PointStruct(id=text_id, vector=vector, payload=payload)
            points.append(point)

        operation_info = self.qdrant_client.upsert(
            collection_name=self.collection_name,
            wait=True,
            points=points
        )

        if operation_info.status != UpdateStatus.COMPLETED:
            raise Exception("Failed to insert data")

    def search(self, query: str, limit: int, collection_name: str):
        query_vector = self.embedding_model.encode(query)
        hits = self.qdrant_client.search(
            collection_name=collection_name,
            query_vector=("text", query_vector),
            limit=limit
        )
        return [{"score": hit.score, "payload": hit.payload} for hit in hits]

    def create_collection(self, collection_name: str):
        self.qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=self.embedding_model.get_sentence_embedding_dimension(),
                distance=Distance.COSINE
            )
        )

    def delete_collection(self, collection_name: str):
        self.qdrant_client.delete_collection(collection_name=collection_name)

    def get_collection_details(self, collection_name: str):
        return self.qdrant_client.get_collection(collection_name=collection_name).json()