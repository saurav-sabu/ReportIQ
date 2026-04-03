import os
import sys
import json
import argparse
import shutil
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from modules.extractor import render_pages_to_images, extract_text, extract_summary_table, extract_client_metadata
from modules.analyzer import analyze_and_merge_logic
from modules.generator import generate_markdown_report

# Load environment variables (for GOOGLE_API_KEY)
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    parser = argparse.ArgumentParser(description="ReportIQ Extractor")
    parser.add_argument("--fresh", action="store_true", help="Force a fresh run by ignoring checkpoint")
    args = parser.parse_args()
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Please set your GOOGLE_API_KEY in the environment or a .env file.")
        sys.exit(1)

    # PDF Paths
    sample_report_pdf = os.path.join(BASE_DIR, os.getenv("SAMPLE_PDF", "Sample Report.pdf"))
    thermal_images_pdf = os.path.join(BASE_DIR, os.getenv("THERMAL_PDF", "Thermal Images.pdf"))
    
    try:
        visual_start = int(os.getenv("VISUAL_START", "11"))
        visual_end = int(os.getenv("VISUAL_END", "23"))
        thermal_start = int(os.getenv("THERMAL_START", "1"))
        thermal_end = int(os.getenv("THERMAL_END", "30"))
        summary_page = int(os.getenv("SUMMARY_PAGE", "10"))
        max_points = int(os.getenv("MAX_POINTS", "7"))
    except ValueError as e:
        print(f"ERROR: Invalid integer in environment variables: {e}")
        sys.exit(1)
    
    for pdf in [sample_report_pdf, thermal_images_pdf]:
        if not os.path.exists(pdf):
            print(f"ERROR: Required file '{pdf}' not found.")
            sys.exit(1)

    # 1. Extraction Phase
    print("--- 1. Extraction Phase ---")
    visual_appendix = render_pages_to_images(sample_report_pdf, "visual_appendix", start_page=visual_start, end_page=visual_end)
    thermal_scans = render_pages_to_images(thermal_images_pdf, "thermal_scans", start_page=thermal_start, end_page=thermal_end)
    summary_table = extract_summary_table(sample_report_pdf, summary_page=summary_page)
    if not summary_table:
        print("ERROR: Could not extract summary table from the PDF.")
        sys.exit(1)
    full_text = extract_text(sample_report_pdf)
    
    # Extract metadata logic from text
    client_data = extract_client_metadata(full_text)
    
    print(f"Rendered {len(visual_appendix)} visual appendix pages and {len(thermal_scans)} thermal scan pages.")
    print(f"Found {len(summary_table)} points in the Summary Table.")
    
    # 2. Analysis Phase (Loop through all 7 primary points)
    print("\n--- 2. Analysis Phase ---")
    ddr_data = []
    
    model_name = os.getenv("MODEL_NAME", "gemini-3.1-pro-preview")
    llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key)
    
    checkpoint_dir = os.path.join(BASE_DIR, "output")
    os.makedirs(checkpoint_dir, exist_ok=True)
    checkpoint_path = os.path.join(checkpoint_dir, "checkpoint.json")
    
    if args.fresh and os.path.exists(checkpoint_path):
        os.remove(checkpoint_path)
        print("Starting a fresh execution (--fresh requested).")
    
    if os.path.exists(checkpoint_path):
        try:
            with open(checkpoint_path, "r") as f:
                ddr_data = json.load(f)
            print(f"Resuming from checkpoint: {len(ddr_data)} points already completed.")
        except json.JSONDecodeError:
            print("WARNING: Checkpoint is corrupted. Starting from scratch.")
            ddr_data = []
    
    num_points = min(max_points, len(summary_table))
    if len(visual_appendix) < 2 * num_points:
        print(f"WARNING: Only {len(visual_appendix)} visual pages for {num_points} points (expected {2*num_points})")
    if len(thermal_scans) < num_points:
        print(f"WARNING: Only {len(thermal_scans)} thermal pages for {num_points} points")

    for i in range(num_points):
        if i < len(ddr_data):
            print(f"Skipping Point #{i+1} (already in checkpoint)")
            continue

        point = summary_table[i]
        point_no = i + 1
        print(f"Analyzing Point #{point_no}...")
        
        v_start = i * 2
        v_end = min(v_start + 2, len(visual_appendix))
        v_pages = visual_appendix[v_start:v_end] if v_start < len(visual_appendix) else []
        t_page = [thermal_scans[i]] if i < len(thermal_scans) else []
        
        analysis_text = analyze_and_merge_logic(llm, point, v_pages, t_page)
        
        impacted_val = point.get("Impacted area (-ve side)") or f"Area {point_no}"
        parts = str(impacted_val).split(" of ")
        area_name = parts[-1].strip() if len(parts) > 1 else parts[0].strip()
        
        section = {
            'area': area_name,
            'observations': analysis_text,
            'images': v_pages + t_page
        }
        ddr_data.append(section)
        
        with open(checkpoint_path, "w") as f:
            json.dump(ddr_data, f, indent=2, default=str)
    
    # 3. Generation Phase
    print("\n--- 3. Generation Phase ---")
    output_md = os.path.join(BASE_DIR, "output", "Main_DDR_Report.md")
    generate_markdown_report(client_data, ddr_data, summary_table, output_md, max_points)
    print(f"High-fidelity report successfully generated at: {os.path.abspath(output_md)}")
    
    # 4. Cleanup Phase
    if os.path.exists(checkpoint_path):
        os.remove(checkpoint_path)
    temp_dir = os.path.join(BASE_DIR, "temp")
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
        print("Cleaned up temporary generation files.")

if __name__ == "__main__":
    main()
