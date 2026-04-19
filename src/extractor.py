import os
from docling.document_converter import DocumentConverter

class FinancialExtractor:
    def __init__(self):
        print("Initializing Docling Models...")
        self.converter = DocumentConverter()

    def parse_pdf(self, file_path):
        """Converts a PDF path into a Docling Document object."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Could not find PDF at: {file_path}")
            
        print(f"Extracting layout and text from: {os.path.basename(file_path)}")
        result = self.converter.convert(file_path)
        return result.document