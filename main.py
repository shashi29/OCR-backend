from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from unstructured.partition.auto import partition
from google.cloud import storage
import tempfile
import os
import json
from datetime import datetime
from configparser import ConfigParser
from pydantic import BaseModel
from typing import List
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from qdrant_client.http.models import CollectionStatus, UpdateStatus

import uuid
import logging

app = FastAPI()

# Load configuration
config = ConfigParser()
config.read('config.ini')  # Adjust the path if needed
bucket_name = config['storage']['bucket_name']
qdrant_url = config['qdrant']['url']
qdrant_api_key = config['qdrant']['api_key']
qdrant_collection_name = config['qdrant']['collection_name']

# Initialize Google Cloud Storage client
storage_client = storage.Client()

# Initialize Qdrant client
qdrant_client = QdrantClient(
    url=qdrant_url,
    api_key=qdrant_api_key,
)

# Initialize Sentence Transformer model
embedding_model = SentenceTransformer("nomic-ai/nomic-embed-text-v1", trust_remote_code=True)

# Configure logging
logging.basicConfig(level=logging.INFO)

class ProcessedData(BaseModel):
    text_id: str
    text: str
    text_type: str
    languages: List[str]
    filetype: str
    last_modified: str
    page_number: int

class SearchRequest(BaseModel):
    query: str
    limit: int = 5

class SearchResult(BaseModel):
    text_id: str
    text: str
    text_type: str
    languages: List[str]
    filetype: str
    last_modified: str
    page_number: int
    score: float

class CollectionRequest(BaseModel):
    collection_name: str

@app.post("/process-pdf/", response_model=List[ProcessedData])
async def process_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    partition_output = partition(
        filename=tmp_path,
        extract_image_block_to_payload=True,
        extract_images_in_pdf=True,
        pdf_infer_table_structure=True,
        strategy="hi_res",
        chunking_strategy="by_title",
        max_characters=4000,
        new_after_n_chars=3800,
        combine_text_under_n_chars=2000
    )

    out = [page.to_dict() for page in partition_output]
    date_folder = datetime.now().strftime("%Y-%m-%d")
    document_name = os.path.splitext(file.filename)[0]
    folder_path = f"{date_folder}/{document_name}/"

    upload_to_gcs(bucket_name, folder_path + file.filename, tmp_path)

    json_tmp_path = tmp_path + ".json"
    with open(json_tmp_path, "w") as json_tmp:
        json.dump(out, json_tmp)
    upload_to_gcs(bucket_name, folder_path + file.filename + ".json", json_tmp_path)

    text_list = [info['text'] for info in out]
    embeddings = embedding_model.encode(text_list)

    add_data_to_collection(out)
    return JSONResponse(content=out)


# Pydantic models
class SearchRequest(BaseModel):
    query: str
    limit: int = 10

class SearchResult(BaseModel):
    text_id: str
    text: str
    text_type: str
    languages: List[str]
    filetype: str
    last_modified: str
    page_number: int
    score: float

@app.post("/search/", response_model=List[dict])
async def search_documents(request: SearchRequest):
    query_vector = embedding_model.encode(request.query)
    hits = qdrant_client.search(
        collection_name=qdrant_collection_name,
        query_vector=("text",query_vector),
        limit=request.limit
    )
    
    results = []
    for hit in hits:
        result = {
            "score": hit.score,
            "payload": hit.payload
        }
        results.append(result)

    return JSONResponse(content=results)

@app.post("/create-collection/")
async def create_collection(request: CollectionRequest):
    try:
        qdrant_client.create_collection(
            collection_name=request.collection_name,
            vectors_config={
                "text": VectorParams(
                    size=embedding_model.get_sentence_embedding_dimension(),
                    distance=Distance.COSINE
                )
            }
        )
        logging.info(f"Collection {request.collection_name} created successfully!")
        return JSONResponse(content={"message": f"Collection {request.collection_name} created successfully!"})

    except Exception as e:
        logging.error(f"Failed to create collection: {e}")
        raise HTTPException(status_code=500, detail="Failed to create collection")

@app.post("/delete-collection/")
async def delete_collection(request: CollectionRequest):
    try:
        qdrant_client.delete_collection(collection_name=request.collection_name)
        logging.info(f"Collection {request.collection_name} deleted successfully!")
        return JSONResponse(content={"message": f"Collection {request.collection_name} deleted successfully!"})

    except Exception as e:
        logging.error(f"Failed to delete collection: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete collection")
    
@app.post("/get-collection-details/")
async def get_collection_details(request: CollectionRequest):
    try:
        collection_details = qdrant_client.get_collection(collection_name=request.collection_name)
        logging.info(collection_details)
        return JSONResponse(content={"message": collection_details.to_dict()})

    except Exception as e:
        logging.error(f"Failed to delete collection: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete collection")

def upload_to_gcs(bucket_name, destination_blob_name, source_file_name):
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    logging.info(f"File {source_file_name} uploaded to {destination_blob_name}.")

def add_data_to_collection(data: List[dict], collection_name: str = "text_info"):

    # instantiate an empty list for the points
    points = []

    # get the relevent data from the input dictionary
    for item in data:
        text_id = str(uuid.uuid4())
        text_type = item.get("type")
        text = item.get("text")
        metadata = item.get("metadata")
        filetype = metadata.get("filetype")
        languages = metadata.get("languages")
        last_modified = metadata.get("last_modified")
        page_number = metadata.get("page_number")


        # get the vector embeddings for the summary and chunk
        summary_vector = embedding_model.encode(text)
        # create a dictionary with the vector embeddings
        vector_dict = {"text": summary_vector}

        # create a dictionary with the payload data
        payload = {
            "text_id":text_id,
            "text": text,
            "text_type": text_type,
            "languages": languages,
            "filetype": filetype,
            "last_modified": last_modified,
            "page_number": page_number,
            }

        # create a PointStruct object and append it to the list of points
        point = PointStruct(id=text_id, vector=vector_dict, payload=payload)
        points.append(point)

    operation_info = qdrant_client.upsert(
        collection_name=collection_name,
        wait=True,
        points=points)

    if operation_info.status == UpdateStatus.COMPLETED:
        print("Data inserted successfully!")
    else:
        print("Failed to insert data")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
