from fastapi import FastAPI
from app.api.routes import document, collection
from app.core.logging import setup_logging
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
origins = ["*", "http://localhost:3000"]#,"https://prospero-two.vercel.app","http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup logging
setup_logging()

# Include routers
app.include_router(document.router, prefix="/documents", tags=["documents"])
app.include_router(collection.router, prefix="/collections", tags=["collections"])

if __name__ == "__main__":
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
