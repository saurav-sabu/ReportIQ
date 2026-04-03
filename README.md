# ReportIQ
ReportIQ is an AI-powered diagnostic tool explicitly designed to ingest raw tabular data, thermal photographs, and visual inspections extracting them natively into high-fidelity markdown structured diagnosis files efficiently and deterministically at scale.

## Prerequisites
- `Python 3.9+`
- A valid Google Gemini API Key

## Installation
1. Clone this repository locally.
2. Install standard Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy the `.env.example` file to `.env`:
   ```bash
   cp .env.example .env
   ```
4. Modify your `.env` configuration mapping the `GOOGLE_API_KEY` alongside any configuration bounds mapping.

## Usage
Simply drop in your raw `.pdf` documents directly into the base repository directory mapping their names exactly to the `.env` references matching `SAMPLE_PDF` and `THERMAL_PDF` values!

Once they are configured execute the pipeline:
```bash
python main.py
```

To automatically bypass any transient `.json` cache history from previous builds manually, simply execute: 
```bash
python main.py --fresh
```

All generated logic files will be stored directly underneath the `output/` dynamically generated artifact directory upon successful extraction rendering.

## Project Structure
- `main.py` - Core execution loop invoking dependencies and saving generated data sets via Checkpoint bindings natively.
- `modules/extractor.py` - Interacts natively with pdfplumber mapping boundaries securely extracting dictionaries alongside high fidelity PyMuPDF rendered assets.
- `modules/analyzer.py` - Encapsulates deterministic text-prompt alignment parsing against the Google Gemini API using native base64 mappings. 
- `modules/generator.py` - Compiles generated context vectors directly into statically templated markdown formats mapping local visual imagery deterministically. 

## License
MIT License