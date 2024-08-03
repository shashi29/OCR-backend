#https://medium.com/quantrium-tech/installing-tesseract-4-on-ubuntu-18-04-b6fcd0cbd78f
sudo apt install -y tesseract-ocr libtesseract-dev
#tesseract --version
uvicorn app.main:app --reload --loop asyncio

project_root/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── document.py
│   │   │   └── collection.py
│   │   └── dependencies.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── logging.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── document.py
│   │   └── collection.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── document_service.py
│   │   └── collection_service.py
│   └── repositories/
│       ├── __init__.py
│       ├── storage_repository.py
│       └── vector_db_repository.py
│
├── tests/
│   ├── __init__.py
│   ├── test_document_service.py
│   └── test_collection_service.py
│
├── .env
├── requirements.txt
└── README.md