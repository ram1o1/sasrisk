# Financial Data Extraction Pipeline (sasrisk)

## 📌 Project Overview
This project is an automated, high-throughput pipeline designed to extract highly structured, quantitative financial and operational data from complex corporate Annual Reports (PDFs). 

It converts massive, hundreds-of-pages-long financial documents into clean machine-readable data (Markdown, JSON tables) and feeds them into Large Language Models (LLMs) to construct a strict JSON payload containing core financials, operational metrics, ratios, and material risk factors. This resulting data is tailored specifically for downstream machine learning datasets, quantitative analysis, and financial dashboards.

---

## 🛠️ Tech Stack & Tools Used
*   **Python:** The core programming language used to build the pipeline.
*   **[Docling](https://github.com/ds4sd/docling):** An advanced document understanding library used to parse PDFs, detect structures (tables, paragraphs), and run OCR on images.
*   **[Google GenAI SDK (Gemini)](https://ai.google.dev/gemini-api/docs/models/gemini):** Specifically using the `gemma-4-31b-it` model to intelligently extract specific metrics from unstructured markdown chunks.
*   **Pandas:** Used for robust data manipulation, cleaning up complex Docling tabular outputs, and deduplicating column headers before exporting to JSON.
*   **RapidOCR:** Under the hood of Docling, it processes scanned or image-based pages within the PDFs.

---

## 🔄 Pipeline Architecture & Steps

The pipeline operates in a batch process, scanning the `data/raw/` directory for PDFs and orchestrating a 3-stage extraction flow, managed by `main.py` and `src/pipeline.py`.

### Step 1: PDF Parsing & Text Extraction (`extractor.py`)
*   **What it does:** Reads the raw PDF file and deeply understands its layout.
*   **How it works:** It uses `Docling`'s `DocumentConverter`. Unlike simple PDF text scrapers (like PyPDF2), Docling understands the visual layout of the page. It determines what is a heading, what is a paragraph, and most importantly, identifies grid structures that signify tables. If a page is scanned, it relies on `RapidOCR` to extract the text. The output is a highly structured `Document` object in memory.

### Step 2: Data Cleaning & Table Export (`processor.py`)
*   **What it does:** Takes the `Document` object and saves it out to disk, heavily cleaning the tabular data.
*   **How it works:**
    *   **Markdown Export:** The entire document text is exported sequentially into a `full_text.md` file.
    *   **Tabular Cleaning:** Financial reports often have messy, multi-level headers or tables without clear headers. The processor extracts each table into a Pandas DataFrame and applies rigorous cleaning:
        *   It promotes the first row to a header if Docling assigns generic numeric column names (`0`, `1`, `2`).
        *   It uses Regex to clean "mangled" column names where data values get accidentally embedded in the header string (e.g., changing `"Standalone.FY 2025..57,789.81."` to just `"Standalone FY 2025"`).
        *   It deduplicates columns so JSON serialization doesn't crash.
    *   **Junk Filtering:** It filters out "tables" that are too small (<2 rows or cols) or mostly empty, saving only meaningful tabular data as `table_X.json`.

### Step 3: LLM Quantitative Analysis (`llm_analyzer.py`)
*   **What it does:** Uses a Large Language Model to read the Markdown and extract specific, hard numbers and risk factors into a final JSON payload.
*   **How it works (The Chunking Strategy):** 
    *   Annual reports are notoriously massive, easily exceeding an LLM's token context window.
    *   The analyzer **splits** the `full_text.md` file into manageable chunks (roughly 400,000 characters).
    *   It sends *each chunk* to the Gemma model with an `EXTRACTION_PROMPT` heavily tuned to ignore corporate fluff (CSR, Board of Director names, indices) and explicitly hunt for: Core Financials (EBITDA, EPS), Operational Metrics (store counts, bill cuts), Financial Ratios, and Material Risk Factors.
    *   After all chunks are processed, a `MERGE_PROMPT` is sent to the LLM containing the partial extractions. The LLM resolves any conflicts (picking the most accurate numbering, usually from consolidated statements), deduplicates arrays, and returns a single, unified `llm_extracted_report.json`.

---

## 📂 Directory Structure

```text
sasrisk/
│
├── .env                  # Contains API keys (GEMINI_API_KEY)
├── requirements.txt      # Python dependencies
├── main.py               # Application entry point
│
├── data/
│   ├── raw/              # Drop annual report PDFs here
│   └── processed/        # Pipeline output goes here (auto-generated)
│       └── [Report Name]/
│           ├── full_text.md              # Full docling text extraction
│           ├── llm_extracted_report.json # Final LLM quantitative payload
│           └── structured_data/          # Folder containing cleaned tables
│               ├── table_1.json
│               ├── table_2.json
│               └── ...
│
└── src/
    ├── config.py         # Directory paths configuration
    ├── extractor.py      # Docling PDF parser
    ├── processor.py      # Pandas cleaning and file export
    ├── llm_analyzer.py   # Token chunking and Gemini integration
    └── pipeline.py       # Orchestrator hooking the steps together
```

---

## 🚀 How to Run

1.  **Dependencies:** Ensure all required modules are installed (`gradio docling google-genai python-dotenv pandas`).
2.  **Environment Setup:** Create a `.env` file in the root directory and add your Google API key:
    ```env
    GEMINI_API_KEY=your_google_api_key_here
    ```
3.  **Add Data:** Place target PDF Annual Reports into the `data/raw/` directory.
4.  **Execute:** Run the pipeline from the root directory:
    ```bash
    python main.py
    ```
    *(or `uv run main.py` if using `uv` environment manager)*
5.  **Output:** Check `data/processed/` for the results per PDF.

---

## 🎯 Design Goals
*   **Total Automation:** Minimal human intervention required.
*   **High Fidelity Data:** The table cleaning logic aims to provide accurate schema mapping so tables can be used programmatically.
*   **AI Resilience:** The chunk-and-merge strategy ensures that massive PDFs don't cause fatal token-limit crashes.
*   **Strict Extraction Focus:** The LLM prompts are deliberately abrasive towards standard corporate puffery, guaranteeing output JSONs are dense with actual data points useful for quantitative assessment.
