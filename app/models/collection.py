from pydantic import BaseModel

class CollectionRequest(BaseModel):
    collection_name: str