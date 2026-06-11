"""Document Ingestion Agent — reads and pre-processes input documents."""

from dataclasses import dataclass, field
from pathlib import Path

from src.tools.document_reader import read_document


@dataclass
class DocumentIngestionResult:
    file_path: str
    file_type: str
    raw_text: str
    char_count: int
    word_count: int
    page_estimate: int


def ingest_document(file_path: str) -> DocumentIngestionResult:
    """
    Read and pre-process a bid document (PDF or DOCX).
    Returns structured ingestion result with extracted text.
    """
    print(f"[Ingestion] Reading document: {file_path}")
    text, file_type = read_document(file_path)

    char_count = len(text)
    word_count = len(text.split())
    page_estimate = max(1, char_count // 2500)  # rough estimate

    print(f"[Ingestion] Done — {word_count:,} words, ~{page_estimate} pages, type={file_type}")

    return DocumentIngestionResult(
        file_path=file_path,
        file_type=file_type,
        raw_text=text,
        char_count=char_count,
        word_count=word_count,
        page_estimate=page_estimate,
    )
