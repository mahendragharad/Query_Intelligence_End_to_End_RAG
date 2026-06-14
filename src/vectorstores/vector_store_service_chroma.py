# 1. Let's Read The PDF 
from pathlib import Path 
from src.chunkers.recursive__chunker import HybridRAGChunker
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings, HuggingFaceBgeEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyMuPDFLoader

BASE_DIR = Path.cwd().resolve()
vector_file_path = BASE_DIR / "config" / "data" / "LC_vector_db" 
pdf_upload_directory = BASE_DIR / "config" / "data" / "uploads" / "Neural-Network(Basics).pdf"


class VectorStoreServiceChroma :

    def __init__(self, collection_name : str, persist_directory : str) :
        self.collection_name = collection_name
        self.persist_directory = persist_directory

        self.embedddings = HuggingFaceBgeEmbeddings(
            model_name = "BAAI/bge-small-en-v1.5"
        )
    
    def create(self,documents) :
        db =  Chroma.from_documents(
            documents=documents,
            embedding=self.embedddings,
            persist_directory=self.persist_directory,
            collection_name=self.collection_name,
        )

        return db
    
    def load(self) :
        db = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embedddings,
            collection_name=self.collection_name,
        )

        return db

        
class VectorStoreInitiate_With_LC_Croma :
    def __init__(self, collection_name : str) :
        self.pdf_file_path = pdf_upload_directory
        self.db_path = vector_file_path
        self.chunker = HybridRAGChunker(chunk_size=900, chunk_overlap=120)
        self.collection_name = collection_name
        self.embeddings = HuggingFaceBgeEmbeddings(
            model_name = "BAAI/bge-small-en-v1.5"
        )

    def create_vector_store(self) :
        retrieved_chunks = self.chunker.chunk_pdf(self.pdf_file_path, extraction_mode="layout", pdf_mode="page")
        db = Chroma.from_documents(
            documents=retrieved_chunks,
            embedding=self.embeddings,
            persist_directory=str(self.db_path),
            collection_name=self.collection_name

        )

        return {
            "Status" : "Vector Store Created Successfully",
            "Chunk Size" : len(retrieved_chunks),
            "DB" : db
        }

collection_name = "Attention_You_Need"
create_db = VectorStoreInitiate_With_LC_Croma(collection_name)
print(create_db.create_vector_store())
        
 
