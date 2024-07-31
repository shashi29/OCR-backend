import json
from google.cloud import storage
from app.config import Config

class StorageRepository:
    def __init__(self):
        self.storage_client = storage.Client()
        self.bucket_name = Config.STORAGE_BUCKET_NAME

    def upload_file(self, destination_blob_name: str, source_file_name: str):
        bucket = self.storage_client.bucket(self.bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_name)

    def upload_json(self, destination_blob_name: str, data: dict):
        bucket = self.storage_client.bucket(self.bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_string(json.dumps(data))