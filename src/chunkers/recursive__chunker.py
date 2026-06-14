# pip install -U langchain langchain-core langchain-community langchain-text-splitters pypdf beautifulsoup4 tiktoken requests
from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional, Literal
from urllib.parse import urlparse

import requests
from bs4 import Tag
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    HTMLHeaderTextSplitter,
    HTMLSemanticPreservingSplitter,
)

SourceMode = Literal["pdf", "web"]


class HybridRAGChunker:
    def __init__(
        self,
        chunk_size: int = 900,
        chunk_overlap: int = 120,
        model_name_for_tokens: str = "gpt-4o-mini",
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.headers_to_split_on = [
            ("h1", "h1"),
            ("h2", "h2"),
            ("h3", "h3"),
            ("h4", "h4"),
        ]

        self.recursive_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            model_name=model_name_for_tokens,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=[
                "\n\n",
                "\n",
                ". ",
                "! ",
                "? ",
                "; ",
                ", ",
                " ",
                "",
            ],
        )

    def _clean_text(self, text: str) -> str:
        text = text.replace("\xa0", " ")
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        return text.strip()

    def _code_handler(self, element: Tag) -> str:
        lang = element.get("data-lang") or "text"
        body = element.get_text(" ", strip=True)
        return f"<code:{lang}>{body}</code>"

    def _enrich_chunks(self, docs: List[Document], source_type: str) -> List[Document]:
        out = []
        total = len(docs)

        for i, d in enumerate(docs):
            content = self._clean_text(d.page_content)
            if not content:
                continue

            meta = dict(d.metadata)
            meta["chunk_index"] = i
            meta["chunk_count"] = total
            meta["char_length"] = len(content)
            meta["source_type"] = source_type
            out.append(Document(page_content=content, metadata=meta))

        return out

    def chunk_pdf(
        self,
        pdf_path: str | Path,
        extraction_mode: Literal["plain", "layout"] = "layout",
        pdf_mode: Literal["page", "single"] = "page",
    ) -> List[Document]:
        loader = PyPDFLoader(
            file_path=str(pdf_path),
            mode=pdf_mode,
            extraction_mode=extraction_mode,
        )
        docs = loader.load()

        for d in docs:
            d.page_content = self._clean_text(d.page_content)
            d.metadata["source"] = str(pdf_path)
            d.metadata["filename"] = Path(pdf_path).name

        split_docs = self.recursive_splitter.split_documents(docs)
        return self._enrich_chunks(split_docs, source_type="pdf")

    def chunk_web(
        self,
        url: str,
        strategy: Literal["semantic", "headers"] = "semantic",
    ) -> List[Document]:
        if strategy == "headers":
            splitter = HTMLHeaderTextSplitter(
                headers_to_split_on=self.headers_to_split_on,
                return_each_element=False,
            )
            docs = splitter.split_text_from_url(url)
            for d in docs:
                d.metadata["source"] = url
                d.metadata["domain"] = urlparse(url).netloc
            split_docs = self.recursive_splitter.split_documents(docs)
            return self._enrich_chunks(split_docs, source_type="web")

        html = requests.get(
            url,
            timeout=30,
            headers={"User-Agent": "Mozilla/5.0 RAGChunker/1.0"},
        )
        html.raise_for_status()

        splitter = HTMLSemanticPreservingSplitter(
            headers_to_split_on=self.headers_to_split_on,
            max_chunk_size=self.chunk_size,
            separators=["\n\n", "\n", ". ", "! ", "? ", "; "],
            elements_to_preserve=["table", "ul", "ol", "pre", "code"],
            denylist_tags=["script", "style", "head", "nav", "footer"],
            preserve_images=False,
            preserve_videos=False,
            custom_handlers={"code": self._code_handler, "pre": self._code_handler},
        )

        docs = splitter.split_text(html.text)

        for d in docs:
            d.page_content = self._clean_text(d.page_content)
            d.metadata["source"] = url
            d.metadata["domain"] = urlparse(url).netloc

        return self._enrich_chunks(docs, source_type="web")

    def chunk_text(self, text: str, source: str = "text", source_type: str = "text") -> List[Document]:
        cleaned = self._clean_text(text)
        if not cleaned:
            return []

        doc = Document(page_content=cleaned, metadata={"source": source})
        split_docs = self.recursive_splitter.split_documents([doc])
        return self._enrich_chunks(split_docs, source_type=source_type)

    def chunk_sources(
        self,
        pdf_paths: Optional[List[str]] = None,
        urls: Optional[List[str]] = None,
    ) -> List[Document]:
        all_chunks: List[Document] = []

        for pdf in pdf_paths or []:
            all_chunks.extend(self.chunk_pdf(pdf))

        for url in urls or []:
            all_chunks.extend(self.chunk_web(url, strategy="semantic"))

        return all_chunks