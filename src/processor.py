import os
import pandas as pd

def save_markdown(document, output_dir):
    """Exports the entire document to Markdown for LLM/NLP use."""
    md_text = document.export_to_markdown()
    md_path = os.path.join(output_dir, "full_text.md")
    
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_text)
    return md_path

def _make_columns_unique(df):
    """Helper to ensure all DataFrame columns are unique strings."""
    cols = []
    seen = {}
    for c in df.columns:
        # Convert empty/NaN headers to 'Unnamed'
        c_str = str(c) if pd.notna(c) and str(c).strip() != "" else "Unnamed"
        
        # Append a number if the column name already exists
        if c_str in seen:
            seen[c_str] += 1
            cols.append(f"{c_str}_{seen[c_str]}")
        else:
            seen[c_str] = 0
            cols.append(c_str)
            
    df.columns = cols
    return df

def save_structured_data(document, output_dir):
    """Exports all detected tables to cleaned, structured JSON files."""
    data_dir = os.path.join(output_dir, "structured_data")
    os.makedirs(data_dir, exist_ok=True)
    
    saved_paths = []
    for i, table in enumerate(document.tables):
        # FIX 1: Pass 'document' to resolve the docling deprecation warning
        df = table.export_to_dataframe(document)
        
        # Drop columns that are completely empty
        df = df.dropna(axis=1, how='all') 
        
        # FIX 2: Deduplicate column names so Pandas can export to JSON
        df = _make_columns_unique(df)
        
        json_path = os.path.join(data_dir, f"table_{i+1}.json")
        df.to_json(json_path, orient="records", indent=4)
        saved_paths.append(json_path)
        
    return saved_paths

def process_document(document, report_name, base_output_dir):
    """Orchestrates the saving of both Markdown and structured Data."""
    report_out_dir = os.path.join(base_output_dir, report_name)
    os.makedirs(report_out_dir, exist_ok=True)
    
    md_path = save_markdown(document, report_out_dir)
    structured_paths = save_structured_data(document, report_out_dir)
    
    return {
        "report_dir": report_out_dir,
        "markdown_file": md_path,
        "structured_data_extracted": len(structured_paths)
    }