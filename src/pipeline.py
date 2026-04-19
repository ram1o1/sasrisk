import os
import glob
from src import config
from src.extractor import FinancialExtractor
from src.processor import process_document

def run_batch_pipeline():
    # 1. Setup paths
    input_dir = config.RAW_DATA_DIR
    output_dir = config.PROCESSED_DATA_DIR
    
    pdf_files = glob.glob(os.path.join(input_dir, "*.pdf"))
    
    if not pdf_files:
        print(f"No PDFs found in {input_dir}. Please add some and try again.")
        return

    print(f"Found {len(pdf_files)} PDFs to process.")
    
    # 2. Initialize Extractor (loads models once)
    extractor = FinancialExtractor()
    
    # 3. Process Loop
    success_count = 0
    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        report_name = filename.replace(".pdf", "")
        
        print(f"\n--- Starting: {report_name} ---")
        
        try:
            # Extract
            doc = extractor.parse_pdf(pdf_path)
            
            # Process & Save
            results = process_document(doc, report_name, output_dir)
            
            print(f"✅ Success! Saved to {results['report_dir']}")
            print(f"   Found {results['tables_extracted']} tables.")
            success_count += 1
            
        except Exception as e:
            print(f"❌ Failed to process {filename}. Error: {e}")
            
    print(f"\nPipeline Complete! Successfully processed {success_count}/{len(pdf_files)} reports.")