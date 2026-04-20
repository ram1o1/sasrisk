import os
import re
import pandas as pd


# --- Configuration ---
# Skip tables smaller than this (too small to be useful structured data)
MIN_ROWS = 2
MIN_COLS = 2


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


def _has_numeric_columns(df):
    """Check if all column names are just numeric indices (0, 1, 2, ...)."""
    for col in df.columns:
        col_str = str(col).strip()
        if not col_str.isdigit():
            return False
    return True


def _promote_first_row_to_header(df):
    """Use the first row as the column header when columns are generic (0, 1, 2, ...).
    
    This fixes tables where Docling didn't detect the header row.
    """
    if len(df) < 2:
        return df

    if _has_numeric_columns(df):
        new_header = df.iloc[0].astype(str)
        df = df[1:].reset_index(drop=True)
        df.columns = new_header
    return df


def _clean_column_name(name):
    """Clean up mangled Docling multi-level column names.
    
    Fixes things like:
      "Standalone.FY 2025..57,789.81." -> "Standalone FY 2025"
      "( ` crore).Consolidated.FY 2025..59,358.05." -> "Consolidated FY 2025 (₹ crore)"
      "Particulars..." -> "Particulars"
    """
    s = str(name)

    # Remove numeric values that got embedded in headers (e.g., "..57,789.81.")
    # Pattern: two or more dots followed by a number (possibly with commas and decimals)
    s = re.sub(r'\.{2,}[\d,]+\.?\d*\.?', '', s)

    # Replace dots used as separators with spaces
    s = re.sub(r'\.+', ' ', s)

    # Clean up "( ` in crore)" style prefixes — normalize currency notation
    s = s.replace('( ` in crore)', '(₹ crore)')
    s = s.replace('( ` crore)', '(₹ crore)')
    s = s.replace('(in ` )', '(₹)')

    # Clean up excessive whitespace  
    s = re.sub(r'\s+', ' ', s).strip()

    # Remove trailing/leading parentheses with only whitespace
    s = re.sub(r'^\(\s*\)$', '', s).strip()

    return s if s else "Unnamed"


def _clean_dataframe(df):
    """Apply all cleaning steps to a dataframe."""
    # Drop columns that are completely empty
    df = df.dropna(axis=1, how='all')

    # Drop rows that are completely empty
    df = df.dropna(axis=0, how='all')

    # Promote first row to header if columns are generic numbers
    df = _promote_first_row_to_header(df)

    # Clean up column names
    df.columns = [_clean_column_name(c) for c in df.columns]

    # Deduplicate column names
    df = _make_columns_unique(df)

    return df


def _is_meaningful_table(df):
    """Filter out tables that are too small to be useful."""
    if len(df) < MIN_ROWS:
        return False
    if len(df.columns) < MIN_COLS:
        return False

    # Skip tables where most cells are empty
    total_cells = df.shape[0] * df.shape[1]
    non_empty = df.notna().sum().sum()
    # Also count empty strings as empty
    non_blank = (df.astype(str).replace('', pd.NA).notna()).sum().sum()

    if total_cells > 0 and (non_blank / total_cells) < 0.3:
        return False

    return True


def save_structured_data(document, output_dir):
    """Exports all detected tables to cleaned, structured JSON files.
    
    Applies cleaning: promotes headers, cleans column names, filters junk tables.
    """
    data_dir = os.path.join(output_dir, "structured_data")
    os.makedirs(data_dir, exist_ok=True)

    saved_paths = []
    skipped = 0
    table_num = 0

    for i, table in enumerate(document.tables):
        # Export from docling
        df = table.export_to_dataframe(document)

        # Clean the dataframe
        df = _clean_dataframe(df)

        # Skip junk tables
        if not _is_meaningful_table(df):
            skipped += 1
            continue

        table_num += 1
        json_path = os.path.join(data_dir, f"table_{table_num}.json")
        df.to_json(json_path, orient="records", indent=4, force_ascii=False)
        saved_paths.append(json_path)

    if skipped > 0:
        print(f"   ℹ️  Skipped {skipped} tables (too small or mostly empty).")

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