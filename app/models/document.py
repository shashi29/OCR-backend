from pydantic import BaseModel, Field
from typing import List

class ProcessedData(BaseModel):
    text_id: str = Field(..., example="123e4567-e89b-12d3-a456-426614174000")
    text: str = Field(..., example="This is an example text from the processed document.")
    text_type: str = Field(..., example="paragraph")
    languages: List[str] = Field(..., example=["en"])
    filetype: str = Field(..., example="pdf")
    last_modified: str = Field(..., example="2024-07-31T12:34:56Z")
    page_number: int = Field(..., example=1)

class SearchRequest(BaseModel):
    query: str = Field(..., example="What is the name in the dataset")
    limit: int = Field(5, example=10)

class SearchResult(BaseModel):
    text_id: str = Field(..., example="123e4567-e89b-12d3-a456-426614174000")
    text: str = Field(..., example="This is an example text that matches the search query.")
    text_type: str = Field(..., example="paragraph")
    languages: List[str] = Field(..., example=["en"])
    filetype: str = Field(..., example="pdf")
    last_modified: str = Field(..., example="2024-07-31T12:34:56Z")
    page_number: int = Field(..., example=1)
    score: float = Field(..., example=0.95)
