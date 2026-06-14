from pydantic import AnyUrl, BaseModel, Field
from typing import Literal


class URLRequest(BaseModel):
    url: AnyUrl
    strategy: Literal["semantic", "headers"] = Field("semantic", description="Chunking strategy for web content")
    collection_name: str = Field("documents", description="Vector store collection name")


class QueryRequest(BaseModel):
    query: str = Field(..., description="Natural language query")
    collection_name: str = Field("documents", description="Collection name to query")
    top_k: int = Field(5, gt=0, le=20, description="Number of top documents to return")
