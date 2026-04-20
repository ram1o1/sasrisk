import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

# ~100K tokens worth of text per chunk, leaving room for prompt + response
MAX_CHARS_PER_CHUNK = 400_000

EXTRACTION_PROMPT = """
You are an expert quantitative financial analyst AI extracting data for machine learning and algorithmic analysis.
Read the following annual report text (or chunk of it) and extract ONLY hard quantitative data, financial metrics, 
and material business risk factors into a structured JSON object.

EXCLUSIONS (DO NOT EXTRACT ANY OF THIS):
- Table of contents, index pages, or boilerplate corporate governance text.
- Letters to shareholders, "Message from the CEO", or generic mission/vision statements.
- Corporate Social Responsibility (CSR), awards, employee welfare, or environmental fluff 
  (unless it represents a material cost or liability).
- Board of directors lists, committee meetings, or statutory auditor details.

Always extract these strict financial standard fields (use null if not found in this chunk):
- "company_name": String
- "fiscal_year": String
- "core_financials": Object containing key aggregated metrics (e.g., "total_revenue", "ebitda", "net_profit", "basic_eps", "diluted_eps") with their absolute numeric values and currencies.
- "financial_ratios": Object containing extracted ratios (e.g., "debt_to_equity", "current_ratio", "inventory_turnover", "roce", "roe", "operating_margin").
- "operational_metrics": Object containing business KPIs (e.g., "total_store_count", "new_stores_added", "total_retail_area_sqft", "revenue_per_sqft", "total_bill_cuts").
- "material_risk_factors": Array of Strings. ONLY extract specific, material operational or financial risks (e.g., supply chain concentration, specific regulatory exposure, interest rate risks). Ignore generic risks like "general economic downturns" or "pandemic risks".
- "future_commitments_and_liabilities": Object containing hard numbers on future capital expenditure plans, contingent liabilities, or lease liabilities.

If you find other highly specific numeric financial data (e.g., segment-wise revenue, debt maturity profiles), add it to the relevant object.

Document Chunk Content:
{document_text}
"""

MERGE_PROMPT = """
You are an expert quantitative financial analyst algorithm.
Below are multiple partial JSON data extractions from different chunks of the SAME annual report.
Merge them into ONE final, deduplicated, and comprehensive JSON payload.

Rules for merging:
1. "core_financials", "financial_ratios", and "operational_metrics": Merge all keys. If there are conflicting values for the same metric across chunks, keep the most precise/detailed numeric value (usually from the consolidated financial statements section).
2. "material_risk_factors": Combine into a single, deduplicated array. Standardize wording if similar risks are mentioned.
3. Completely strip out any non-quantitative "fluff" that might have accidentally been extracted by the chunk processors. We ONLY want numbers, ratios, and hard business facts.

Partial Extractions to Merge:
{partial_results}
"""


def _split_into_chunks(text, max_chars):
    """Split text into chunks, trying to break at markdown headers or paragraphs."""
    if len(text) <= max_chars:
        return [text]

    chunks = []
    current_chunk = ""

    for line in text.split('\n'):
        # If adding this line would exceed the limit, start a new chunk
        if len(current_chunk) + len(line) + 1 > max_chars:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = line + '\n'
        else:
            current_chunk += line + '\n'

    if current_chunk.strip():
        chunks.append(current_chunk)

    return chunks


def _call_llm(client, prompt):
    """Make a single LLM call and return parsed JSON."""
    response = client.models.generate_content(
        model='gemma-4-31b-it',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )
    return json.loads(response.text)


def _save_json(data, md_file_path):
    """Save the final JSON output next to the markdown file."""
    output_dir = os.path.dirname(md_file_path)
    analysis_path = os.path.join(output_dir, "llm_extracted_report.json")

    with open(analysis_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    return analysis_path


def extract_structured_report(md_file_path, report_name):
    """Feeds Markdown to the LLM to extract structured JSON data.
    
    Automatically chunks large documents that exceed the model's token limit.
    """
    print(f"   🧠 Asking LLM to extract structured data from {report_name}...")

    # 1. Get API key
    my_api_key = os.environ.get("GEMINI_API_KEY")
    if not my_api_key:
        print("   ❌ Error: GEMINI_API_KEY not found in .env file.")
        return None

    client = genai.Client(api_key=my_api_key)

    # 2. Read the markdown
    if not os.path.exists(md_file_path):
        print("   ❌ Markdown file not found for LLM analysis.")
        return None

    with open(md_file_path, "r", encoding="utf-8") as f:
        document_text = f.read()

    # 3. Chunk if necessary
    chunks = _split_into_chunks(document_text, MAX_CHARS_PER_CHUNK)

    if len(chunks) == 1:
        # --- Single-pass extraction (document fits in context) ---
        try:
            prompt = EXTRACTION_PROMPT.format(document_text=document_text)
            result = _call_llm(client, prompt)
            return _save_json(result, md_file_path)
        except Exception as e:
            print(f"   ❌ LLM Extraction failed: {e}")
            return None
    else:
        # --- Chunked extraction + merge ---
        print(f"   📄 Document too large for single request ({len(document_text):,} chars). "
              f"Splitting into {len(chunks)} chunks...")

        partial_results = []
        for i, chunk in enumerate(chunks):
            print(f"   ⏳ Processing chunk {i+1}/{len(chunks)}...")
            try:
                prompt = EXTRACTION_PROMPT.format(document_text=chunk)
                parsed = _call_llm(client, prompt)
                partial_results.append(parsed)
                print(f"   ✅ Chunk {i+1}/{len(chunks)} done.")
            except Exception as e:
                print(f"   ⚠️  Chunk {i+1} failed: {e}. Skipping...")
                continue

        if not partial_results:
            print("   ❌ All chunks failed. No data extracted.")
            return None

        # If only one chunk succeeded, use it directly
        if len(partial_results) == 1:
            return _save_json(partial_results[0], md_file_path)

        # Merge partial results using the LLM
        print(f"   🔀 Merging {len(partial_results)} partial extractions...")
        try:
            merge_prompt = MERGE_PROMPT.format(
                partial_results=json.dumps(partial_results, indent=2)
            )
            merged = _call_llm(client, merge_prompt)
            return _save_json(merged, md_file_path)
        except Exception as e:
            print(f"   ⚠️  Merge failed: {e}. Saving first chunk result as fallback.")
            return _save_json(partial_results[0], md_file_path)