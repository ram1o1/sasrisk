from docling.document_converter import DocumentConverter

def convert_financial_report(pdf_path: str, output_path: str):
    print(f"Starting ingestion for: {pdf_path}")
    
    # Initialize the Docling converter
    converter = DocumentConverter()
    
    # Process the PDF (this handles OCR, table detection, and layout parsing)
    result = converter.convert(pdf_path)
    
    # Export the parsed document to Markdown
    markdown_text = result.document.export_to_markdown()
    
    # Save the structured text to a file
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(markdown_text)
        
    print(f"Extraction complete! Markdown saved to: {output_path}")

if __name__ == "__main__":
    # Replace with the path to your actual financial document
    INPUT_PDF = "/home/sriram1o1/sasrisk/AR_27036_DMART_2024_2025_A_19072025202320.pdf" 
    OUTPUT_MD = "dmart_anuala_report.md"
    
    convert_financial_report(INPUT_PDF, OUTPUT_MD)