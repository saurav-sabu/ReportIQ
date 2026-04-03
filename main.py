import os
import json
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from modules.extractor import render_pages_to_images, extract_text, extract_summary_table, extract_client_metadata
from modules.analyzer import analyze_and_merge_logic
from modules.generator import generate_markdown_report

# Load environment variables (for GOOGLE_API_KEY)
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Please set your GOOGLE_API_KEY in the environment or a .env file.")
        return

    # PDF Paths
    sample_report_pdf = os.path.join(BASE_DIR, "Sample Report.pdf")
    thermal_images_pdf = os.path.join(BASE_DIR, "Thermal Images.pdf")
    
    for pdf in [sample_report_pdf, thermal_images_pdf]:
        if not os.path.exists(pdf):
            print(f"ERROR: Required file '{pdf}' not found.")
            return

    # 1. Extraction Phase
    print("--- 1. Extraction Phase ---")
    visual_appendix = render_pages_to_images(sample_report_pdf, "visual_appendix", start_page=11, end_page=23)
    thermal_scans = render_pages_to_images(thermal_images_pdf, "thermal_scans", start_page=1, end_page=30)
    summary_table = extract_summary_table(sample_report_pdf)
    if not summary_table:
        print("ERROR: Could not extract summary table from the PDF.")
        return
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
    
    for i in range(min(7, len(summary_table))):
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
            json.dump(ddr_data, f, indent=2)
    
    # 3. Generation Phase
    print("\n--- 3. Generation Phase ---")
    output_md = os.path.join(BASE_DIR, "output", "Main_DDR_Report.md")
    generate_markdown_report(client_data, ddr_data, summary_table, output_md)
    print(f"High-fidelity report successfully generated at: {os.path.abspath(output_md)}")

if __name__ == "__main__":
    main()
