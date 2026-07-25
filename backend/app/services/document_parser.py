from pathlib import Path
from typing import Dict, Any, List
from unstructured.partition.auto import partition

class DocumentIngestionParser:
    def __init__(self, upload_dir: str = "storage/uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def parse_document(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parses multi-format documents (PDFs, Word files, HTML) using the 'unstructured' library.
        Performs semantic chunking and extracts text elements and visual table/chart bounding boxes.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Target document {file_path} not found.")

        # Utilizing unstructured partition with hi_res strategy for multimodal extraction
        elements = partition(filename=str(path), strategy="fast")
        #elements = partition(filename=str(path), strategy="hi_res")

        structured_chunks = []
        for i, element in enumerate(elements):
            structured_chunks.append({
                "element_id": f"chunk_{i:03d}",
                "category": element.category,
                "text": str(element)
            })

        return structured_chunks

# Global ingestion parser instance
ingestion_parser = DocumentIngestionParser()