from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from unstructured.partition.auto import partition
from unstructured.partition.pdf_image.pdf_image_utils import (
    check_element_types_to_extract,
    convert_pdf_to_images,
    get_the_last_modification_date_pdf_or_img,
    save_elements,
)
from google.cloud import storage
import tempfile
import os
import json
from datetime import datetime
from configparser import ConfigParser

app = FastAPI()

# Load configuration
config = ConfigParser()
config.read('config.ini')  # Adjust the path if needed
bucket_name = config['storage']['bucket_name']

# Initialize Google Cloud Storage client
storage_client = storage.Client()

@app.post("/process-pdf/")
async def process_pdf(file: UploadFile = File(...)):
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        # Process the PDF file using the partition function
        partition_output = partition(
            filename=tmp_path,
            extract_image_block_to_payload=True,
            extract_images_in_pdf=True,
            pdf_infer_table_structure=True,
            strategy="hi_res",
            # Post processing to aggregate text once we have the title
            chunking_strategy="by_title",
            # Chunking params to aggregate text blocks
            # Attempt to create a new chunk 3800 chars
            # Attempt to keep chunks > 2000 chars
            max_characters=4000,
            new_after_n_chars=3800,
            combine_text_under_n_chars=2000
        )

        # Convert the partition output to a list of dictionaries
        out = [page.to_dict() for page in partition_output]

        # Create a folder with the current date
        date_folder = datetime.now().strftime("%Y-%m-%d")

        # Create a folder with the document name (without extension)
        document_name = os.path.splitext(file.filename)[0]
        folder_path = f"{date_folder}/{document_name}/"

        # Upload the PDF file to Google Cloud Storage
        upload_to_gcs(bucket_name, folder_path + file.filename, tmp_path)

        # Save JSON output to a temporary file
        json_tmp_path = tmp_path + ".json"
        with open(json_tmp_path, "w") as json_tmp:
            json.dump(out, json_tmp)

        # Upload the JSON file to Google Cloud Storage
        upload_to_gcs(bucket_name, folder_path + file.filename + ".json", json_tmp_path)

        # Return the result as JSON
        return JSONResponse(content=out)

    finally:
        print("Cleaning up...")
        # Ensure the temporary files are deleted
        os.remove(tmp_path)
        if os.path.exists(json_tmp_path):
            os.remove(json_tmp_path)

def upload_to_gcs(bucket_name, destination_blob_name, source_file_name):
    """Uploads a file to the bucket."""
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    print(f"File {source_file_name} uploaded to {destination_blob_name}.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
