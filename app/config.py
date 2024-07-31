import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Storage Settings
    STORAGE_BUCKET_NAME = os.getenv('STORAGE__BUCKET_NAME')
    
    # Qdrant Settings
    QDRANT_URL = os.getenv('QDRANT__URL')
    QDRANT_API_KEY = os.getenv('QDRANT__API_KEY')
    QDRANT_COLLECTION_NAME = os.getenv('QDRANT__COLLECTION_NAME')
    
    # Embedding Model
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL')

# Access settings
# config = Config()

# # Print out the values to verify they're being loaded correctly
# print(f"Storage bucket name: {config.STORAGE_BUCKET_NAME}")
# print(f"Qdrant URL: {config.QDRANT_URL}")
# print(f"Qdrant API key: {config.QDRANT_API_KEY}")
# print(f"Qdrant collection name: {config.QDRANT_COLLECTION_NAME}")
# print(f"Embedding model: {config.EMBEDDING_MODEL}")
