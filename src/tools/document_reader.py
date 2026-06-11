"""Document reading tools for PDF and DOCX files."""

import io
from pathlib import Path
from typing import Optional


def read_pdf(file_path: str) -> str:
    """Extract full text from a PDF file using pdfplumber (better for tables/layouts)."""
    import pdfplumber

    text_parts = []
    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages):
            page_text = page.extract_text()
            if page_text:
                text_parts.append(f"--- Page {i + 1} ---\n{page_text}")
    return "\n\n".join(text_parts)


def read_pdf_pypdf(file_path: str) -> str:
    """Extract text using pypdf as fallback."""
    from pypdf import PdfReader

    reader = PdfReader(file_path)
    parts = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            parts.append(f"--- Page {i + 1} ---\n{text}")
    return "\n\n".join(parts)


def read_docx(file_path: str) -> str:
    """Extract full text from a DOCX file."""
    from docx import Document

    doc = Document(file_path)
    parts = []

    for element in doc.element.body:
        tag = element.tag.split("}")[-1] if "}" in element.tag else element.tag
        if tag == "p":
            # Paragraph
            from docx.oxml.ns import qn
            para_text = "".join(node.text or "" for node in element.iter() if node.tag.endswith("}t"))
            if para_text.strip():
                parts.append(para_text)
        elif tag == "tbl":
            # Table — extract as pipe-delimited text
            rows = []
            for row in element.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tr"):
                cells = []
                for cell in row.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tc"):
                    cell_text = "".join(
                        node.text or "" for node in cell.iter()
                        if node.tag.endswith("}t")
                    ).strip()
                    cells.append(cell_text)
                rows.append(" | ".join(cells))
            if rows:
                parts.append("\n".join(rows))

    return "\n\n".join(parts)


def read_document(file_path: str) -> tuple[str, str]:
    """
    Read a PDF or DOCX file and return (text, file_type).
    Tries pdfplumber first for PDFs, falls back to pypdf.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Document not found: {file_path}")

    suffix = path.suffix.lower()
    if suffix == ".pdf":
        try:
            text = read_pdf(file_path)
            if len(text.strip()) < 100:
                # PDF might be scanned — try pypdf
                text = read_pdf_pypdf(file_path)
        except Exception:
            text = read_pdf_pypdf(file_path)
        return text, "pdf"
    elif suffix in (".docx", ".doc"):
        return read_docx(file_path), "docx"
    else:
        raise ValueError(f"Unsupported file type: {suffix}. Use .pdf or .docx")
