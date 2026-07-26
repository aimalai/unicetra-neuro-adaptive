from pathlib import Path
from typing import Dict, Any, List
from unstructured.partition.auto import partition

class DocumentIngestionParser:
    def __init__(self, upload_dir: str = "storage/uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def parse_document(self, file_path: str, doc_name: str = "default_doc") -> List[Dict[str, Any]]:
        """
        Parses multi-format documents (PDFs, Word, HTML) using 'unstructured'.
        Extracts text elements and tracks active layout headers to build a hierarchical tree.
        Uses `doc_name` to construct unique node IDs across enterprise multi-doc uploads.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Target document {file_path} not found.")

        elements = partition(filename=str(path), strategy="fast")

        structured_chunks = []
        current_section = "Document Preamble"

        for i, element in enumerate(elements):
            text = str(element).strip()
            if not text:
                continue

            category = getattr(element, "category", "NarrativeText")

            # Format-agnostically detect structural headers (Articles, Chapters, Titles)
            if category in ["Title", "Header"] or text.startswith("Article ") or text.startswith("CHAPTER "):
                current_section = text[:150]  # Clean section header tag

            structured_chunks.append({
                "element_id": f"{doc_name}_chunk_{i:04d}",
                "category": category,
                "section_header": current_section,
                "text": text
            })

        return structured_chunks

# Global ingestion parser instance
ingestion_parser = DocumentIngestionParser()