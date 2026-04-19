import os
import pandas as pd

def save_markdown(document, output_dir):
    """Exports the entire document to Markdown for LLM/NLP use."""
    md_text = document.export_to_markdown()
    md_path = os.path.join(output_dir, "full_text.md")
    
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_text)
    return md_path

def save_tables(document, output_dir):
    """Exports all detected tables to cleaned CSV files."""
    tables_dir = os.path.join(output_dir, "tables")
    os.makedirs(tables_dir, exist_ok=True)
    
    saved_paths = []
    for i, table in enumerate(document.tables):
        df = table.export_to_dataframe()
        
        # Optional: Add simple Pandas data cleaning here
        # Example: Drop columns that are completely empty
        df = df.dropna(axis=1, how='all') 
        
        csv_path = os.path.join(tables_dir, f"table_{i+1}.csv")
        df.to_csv(csv_path, index=False)
        saved_paths.append(csv_path)
        
    return saved_paths

def process_document(document, report_name, base_output_dir):
    """Orchestrates the saving of both Markdown and Tables."""
    report_out_dir = os.path.join(base_output_dir, report_name)
    os.makedirs(report_out_dir, exist_ok=True)
    
    md_path = save_markdown(document, report_out_dir)
    table_paths = save_tables(document, report_out_dir)
    
    return {
        "report_dir": report_out_dir,
        "markdown_file": md_path,
        "tables_extracted": len(table_paths)
    }