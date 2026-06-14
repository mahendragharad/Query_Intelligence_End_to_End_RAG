from pathlib import Path
from typing import Optional
import logging

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from src.api.auth import (
    AUTH_HEADER_PREFIX,
    authenticate_user,
    create_access_token,
    create_user,
    get_email_from_token,
)
from src.loaders.pdf_loader import FileStorageService
from src.services.ingestion_service import IngestionService
from src.services.retrieval_service import RetrievalService
from src.api.schemas import QueryRequest, URLRequest

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RAG Ingestion API",
    version="1.0.0",
    description="Document ingestion and retrieval API for RAG pipelines",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path.cwd().resolve()
UPLOAD_DIRECTORY = BASE_DIR / "config" / "data" / "uploads"
VECTOR_DIRECTORY = BASE_DIR / "config" / "data" / "vector_db"

storage_service = FileStorageService(str(UPLOAD_DIRECTORY))
DEFAULT_COLLECTION = "documents"

retrieval_service = RetrievalService(db_path=str(VECTOR_DIRECTORY), collection_name=DEFAULT_COLLECTION)


def get_current_user(request: Request) -> str:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith(AUTH_HEADER_PREFIX):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = auth_header[len(AUTH_HEADER_PREFIX) :].strip()
    email = get_email_from_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return email


@app.get("/")
def root() -> dict:
    """Root endpoint with API information."""
    return {
        "message": "RAG Ingestion API is running",
        "version": "1.0.0",
        "documentation": "http://localhost:8000/docs",
        "openapi": "http://localhost:8000/openapi.json",
        "endpoints": {
            "health": "GET /health",
            "upload_pdf": "POST /upload",
            "ingest_url": "POST /ingest/url",
            "preview_chunks": "POST /chunk/url",
            "query": "POST /query",
            "answer": "POST /answer",
        },
    }


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok", "message": "FastAPI ingestion service is running."}


@app.post("/register")
def register_user(payload: dict):
    try:
        email = payload.get("email")
        password = payload.get("password")
        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password are required")
        create_user(email=email, password=password)
        return {"status": "success", "message": "User registered successfully."}
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception as error:
        logger.error(f"Registration error: {str(error)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Registration failed")


@app.post("/login")
def login_user(payload: dict):
    try:
        email = payload.get("email")
        password = payload.get("password")
        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password are required")

        if not authenticate_user(email=email, password=password):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        token = create_access_token(email=email)
        return {"status": "success", "access_token": token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as error:
        logger.error(f"Login error: {str(error)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Login failed")


@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    collection_name: str = DEFAULT_COLLECTION,
    current_user: str = Depends(get_current_user),
):
    """Upload and ingest a PDF file into the vector store."""
    try:
        logger.info(f"Receiving upload: {file.filename}")
        
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        saved_path = await storage_service.save_uploaded_file(file)
        logger.info(f"File saved to: {saved_path}")
        
        ingestion = IngestionService(
            upload_dir=UPLOAD_DIRECTORY,
            vector_dir=VECTOR_DIRECTORY,
            collection_name=collection_name,
        )

        logger.info(f"Starting ingestion for collection: {collection_name}")
        ingest_result = ingestion.ingest_pdf(saved_path)
        pdf_chunks = ingestion.chunk_pdf(saved_path)
        
        logger.info(f"Successfully ingested {len(pdf_chunks)} chunks")

        return {
            "message": "File uploaded and ingested successfully.",
            "filename": file.filename,
            "saved_path": saved_path,
            "chunk_count": len(pdf_chunks),
            "collection_name": collection_name,
        }

    except HTTPException:
        raise
    except Exception as error:
        logger.error(f"Upload error: {str(error)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(error)}")


@app.post("/ingest/url")
def ingest_url(request: URLRequest, current_user: str = Depends(get_current_user)):
    """Ingest content from a URL into the vector store."""
    try:
        url = str(request.url)
        logger.info(f"Receiving URL ingest request: {url}")
        
        ingestion = IngestionService(
            upload_dir=UPLOAD_DIRECTORY,
            vector_dir=VECTOR_DIRECTORY,
            collection_name=request.collection_name,
        )
        
        logger.info(f"Starting URL ingestion for collection: {request.collection_name}")
        ingest_result = ingestion.ingest_web_url(url, strategy=request.strategy)
        
        logger.info(f"Successfully ingested URL with {ingest_result['document_count']} documents")
        return ingest_result
        
    except Exception as error:
        logger.error(f"URL ingestion error: {str(error)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"URL ingestion failed: {str(error)}")


@app.post("/chunk/url")
def chunk_url(request: URLRequest, current_user: str = Depends(get_current_user)):
    """Preview chunked content from a URL without storing."""
    try:
        url = str(request.url)
        logger.info(f"Receiving chunk preview request: {url}")
        
        ingestion = IngestionService(
            upload_dir=UPLOAD_DIRECTORY,
            vector_dir=VECTOR_DIRECTORY,
            collection_name=request.collection_name,
        )
        
        docs = ingestion.chunk_web(url, strategy=request.strategy)
        logger.info(f"Generated {len(docs)} chunks from URL")
        
        preview = [
            {
                "text": doc.page_content,
                "metadata": doc.metadata,
            }
            for doc in docs[:5]
        ]
        return {
            "status": "success",
            "url": str(request.url),
            "strategy": request.strategy,
            "chunk_count": len(docs),
            "preview": preview,
        }
    except Exception as error:
        logger.error(f"Chunk preview error: {str(error)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chunk preview failed: {str(error)}")


@app.post("/query")
def query_embeddings(request: QueryRequest, current_user: str = Depends(get_current_user)):
    """Query the vector store for relevant documents."""
    try:
        logger.info(f"Receiving query request: {request.query}")
        
        service = RetrievalService(
            db_path=str(VECTOR_DIRECTORY),
            collection_name=request.collection_name,
        )
        
        logger.info(f"Querying collection: {request.collection_name} with top_k={request.top_k}")
        results = service.query(request.query, top_k=request.top_k)
        
        logger.info(f"Query returned {len(results)} results")
        return {
            "status": "success",
            "query": request.query,
            "collection_name": request.collection_name,
            "result_count": len(results),
            "results": results,
        }
    except Exception as error:
        logger.error(f"Query error: {str(error)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Query failed: {str(error)}")


@app.post("/answer")
def answer_query(request: QueryRequest, current_user: str = Depends(get_current_user)):
    """Answer a query using retrieved chunks and an NVIDIA OpenAI model."""
    try:
        logger.info(f"Receiving answer request: {request.query}")
        
        service = RetrievalService(
            db_path=str(VECTOR_DIRECTORY),
            collection_name=request.collection_name,
        )
        
        logger.info(f"Generating answer for collection: {request.collection_name} with top_k={request.top_k}")
        answer_payload = service.generate_answer(request.query, top_k=request.top_k)
        
        logger.info("Answer generation complete")
        return {
            "status": "success",
            "query": answer_payload["query"],
            "collection_name": request.collection_name,
            "result_count": answer_payload.get("result_count", 0),
            "answer": answer_payload.get("answer", ""),
            "context": answer_payload.get("context", []),
        }
    except Exception as error:
        logger.error(f"Answer generation error: {str(error)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Answer generation failed: {str(error)}")


    

    


