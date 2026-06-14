# 🚀 Query Intelligence Hub

## Enterprise-Grade AI Knowledge Retrieval & Grounded Answer Generation Platform

**Search your ingested knowledge base or generate grounded AI answers
directly from your documents using a modular Retrieval-Augmented
Generation (RAG) architecture built with FastAPI, Streamlit, ChromaDB,
and open-source LLMs.**

------------------------------------------------------------------------

# 📌 Overview

Query Intelligence Hub is a production-oriented Retrieval-Augmented
Generation (RAG) platform designed to transform unstructured documents
into an intelligent and searchable knowledge base.

The platform supports PDF and Web URL ingestion, semantic embedding
generation, persistent vector storage, cross-encoder reranking, and
grounded answer generation through open-source LLMs.

Unlike a traditional chatbot, the application follows a modular software
architecture with dedicated layers for document ingestion,
preprocessing, embedding generation, retrieval, reranking,
authentication, and AI inference, making it scalable and maintainable.

------------------------------------------------------------------------

# ✨ Key Features

-   JWT Authentication & Secure User Management
-   PDF & Web URL Knowledge Ingestion
-   Recursive Text Chunking & Cleaning
-   BAAI Semantic Embeddings
-   ChromaDB Persistent Vector Store
-   Cross Encoder Reranking
-   Grounded AI Response Generation
-   Automatic LLM Fallback Strategy
-   FastAPI REST Architecture
-   Interactive Streamlit Frontend
-   Modular Production-Oriented Design

------------------------------------------------------------------------

# 🏛️ Architecture Philosophy

    Presentation Layer
            │
            ▼
    API Layer
            │
            ▼
    Service Layer
            │
            ▼
    Document Processing
            │
            ▼
    Embedding Pipeline
            │
            ▼
    Vector Storage
            │
            ▼
    Semantic Retrieval
            │
            ▼
    Cross Encoder Reranking
            │
            ▼
    LLM Inference

------------------------------------------------------------------------

# ⚙️ Technology Stack

  Category              Technology
  --------------------- ------------------------------
  Frontend              Streamlit + Custom CSS
  Backend               FastAPI
  Language              Python
  Vector Database       ChromaDB
  Embedding Model       BAAI/bge-small-en-v1.5
  Reranker              BAAI/bge-reranker-base
  Primary LLM           Ollama Gemma3:4B
  Fallback LLM          NVIDIA Nemotron-3-Ultra-550B
  Document Processing   LangChain Loaders
  Authentication        JWT + OAuth2
  Storage               Local Persistent Storage

------------------------------------------------------------------------

# 🔄 Functional Workflow

    User Authentication
            │
            ▼
    Document Upload / URL Ingestion
            │
            ▼
    Text Extraction
            │
            ▼
    Recursive Chunking
            │
            ▼
    Cleaning & Metadata Enrichment
            │
            ▼
    Embedding Generation
            │
            ▼
    ChromaDB Vector Storage
            │
            ▼
    Semantic Retrieval
            │
            ▼
    Cross Encoder Reranking
            │
            ▼
    Context Selection
            │
            ▼
    LLM Inference
            │
            ▼
    Grounded AI Response

------------------------------------------------------------------------

# 🏗️ Engineering Highlights

-   Layered Modular Architecture
-   Service-Oriented Design
-   RESTful API Development
-   Semantic Search Pipeline
-   Cross Encoder Context Optimization
-   Local LLM Inference
-   Automatic Model Failover
-   Persistent Vector Storage
-   Metadata Driven Retrieval
-   Separation of Business Logic and API Layer

------------------------------------------------------------------------

# 🔌 API Endpoints

## Public

-   GET `/`
-   GET `/health`
-   POST `/register`
-   POST `/login`

## Protected

-   POST `/upload`
-   POST `/ingest/url`
-   POST `/chunk/url`
-   POST `/query`
-   POST `/answer`

------------------------------------------------------------------------

# 🎯 Core Capabilities

-   Knowledge Base Creation
-   Semantic Document Search
-   Grounded AI Answer Generation
-   Cross Encoder Context Optimization
-   Open Source AI Stack
-   Local Deployment
-   Enterprise Modular Architecture
-   Extensible Component Design

------------------------------------------------------------------------

# 🚀 Future Roadmap

-   Docker & Docker Compose
-   Redis Caching
-   Hybrid Retrieval
-   Query Expansion
-   LangGraph Integration
-   Evaluation Framework
-   CI/CD Pipeline
-   Monitoring & Observability
-   Cloud Deployment

------------------------------------------------------------------------

# 💡 Project Vision

Query Intelligence Hub demonstrates how modern AI components---including
semantic embeddings, vector databases, cross-encoder reranking,
authentication, and local LLM inference---can be integrated into a
scalable, maintainable, production-oriented Retrieval-Augmented
Generation platform.
