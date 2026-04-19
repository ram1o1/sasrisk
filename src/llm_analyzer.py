import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

def extract_structured_report(md_file_path, report_name):
    """Feeds Markdown to the LLM to extract structured JSON data."""
    print(f"   🧠 Asking LLM to extract structured data from {report_name}...")
    
    # 1. Explicitly grab the key we KNOW works from the .env file
    my_api_key = os.environ.get("GEMINI_API_KEY")
    
    if not my_api_key:
        print("   ❌ Error: GEMINI_API_KEY not found in .env file.")
        return None

    # 2. Force the client to use THIS key (ignoring system GOOGLE_API_KEY)
    # We initialize it inside the function to ensure it loads after dotenv
    client = genai.Client(api_key=my_api_key)

    if not os.path.exists(md_file_path):
        print("   ❌ Markdown file not found for LLM analysis.")
        return None

    with open(md_file_path, "r", encoding="utf-8") as f:
        document_text = f.read()

    prompt = f"""
    You are an expert financial data extraction AI. Read the following annual report text 
    and extract the information into a structured JSON object.
    
    Always try to fill out these standard fields (use null if not found):
    - "company_name": String
    - "fiscal_year": String
    - "executive_summary": String (A brief 2-3 sentence overview)
    - "total_revenue": String (Include currency and scale, e.g., "₹ 10,000 Crores")
    - "net_profit": String
    - "key_risk_factors": Array of Strings
    
    For any NEW, unique, or company-specific metrics you find (e.g., "store count", 
    "active users", "ESG goals", "debt ratios"), put them inside this field:
    - "additional_insights": Object (Key-Value pairs of whatever you find)

    Document Content:
    {document_text}
    """

    try:
        response = client.models.generate_content(
            model='gemma-4-31b-it',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        
        output_dir = os.path.dirname(md_file_path)
        analysis_path = os.path.join(output_dir, "llm_extracted_report.json")
        
        parsed_json = json.loads(response.text)
        with open(analysis_path, "w", encoding="utf-8") as f:
            json.dump(parsed_json, f, indent=4)
            
        return analysis_path

    except Exception as e:
        print(f"   ❌ LLM Extraction failed: {e}")
        return None