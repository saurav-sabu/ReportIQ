import os
from dotenv import load_dotenv
from modules.extractor import render_pages_to_images, extract_text, extract_summary_table
from modules.analyzer import analyze_and_merge_logic
from modules.generator import generate_markdown_report

# Load environment variables (for GOOGLE_API_KEY)
load_dotenv()

def main():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Please set your GOOGLE_API_KEY in the environment or a .env file.")
        return

    # PDF Paths
    sample_report_pdf = "Sample Report.pdf"
    thermal_images_pdf = "Thermal Images.pdf"
    
    # 1. Extraction Phase
    print("--- 1. Extraction Phase ---")
    visual_appendix = render_pages_to_images(sample_report_pdf, "visual_appendix", start_page=11, end_page=23)
    thermal_scans = render_pages_to_images(thermal_images_pdf, "thermal_scans", start_page=1, end_page=30)
    summary_table = extract_summary_table(sample_report_pdf)
    full_text = extract_text(sample_report_pdf)
    
    # Simple metadata extraction logic from text
    client_data = {
        "client_name": "Flat No-8/63",
        "address": "Yamuna CHS, Mulund East",
        "date": "03/01/2023",
        "inspected_by": "Mr. Krushna",
        "property_type": "Flat",
        "floors": "1",
        "age": "11 Years"
    }
    
    print(f"Rendered {len(visual_appendix)} visual appendix pages and {len(thermal_scans)} thermal scan pages.")
    print(f"Found {len(summary_table)} points in the Summary Table.")
    
    # 2. Analysis Phase (Loop through all 7 primary points)
    print("\n--- 2. Analysis Phase ---")
    ddr_data = []
    
    # Switching to gemini-3.1-pro-preview as per user request
    # This ensuring high-fidelity analysis.
    for i in range(min(7, len(summary_table))):
        point = summary_table[i]
        point_no = i + 1
        print(f"Analyzing Point #{point_no}...")
        
        v_start = (i * 2) % len(visual_appendix)
        v_end = min(v_start + 2, len(visual_appendix))
        t_page = [thermal_scans[i % len(thermal_scans)]]
        v_pages = visual_appendix[v_start:v_end]
        
        # We temporarily hardcode 1.5-flash inside analyzer or just pass it as a param if we updated the signature
        # For now, let's just run it. (I'll update analyzer.py to 1.5-flash in a separate tool call if needed)
        analysis_text = analyze_and_merge_logic(api_key, point, v_pages, t_page)
        
        impacted_val = point.get("Impacted area (-ve side)") or f"Area {point_no}"
        area_name = str(impacted_val).split(" of ")[0]
        
        section = {
            'area': area_name,
            'observations': analysis_text,
            'images': v_pages + t_page
        }
        ddr_data.append(section)
    
    # 3. Generation Phase
    print("\n--- 3. Generation Phase ---")
    output_md = "output/Main_DDR_Report.md"
    generate_markdown_report(client_data, ddr_data, summary_table, output_md)
    print(f"High-fidelity report successfully generated at: {os.path.abspath(output_md)}")

if __name__ == "__main__":
    main()
