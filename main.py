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
    # Rendering appendix and thermal pages as full images (Fix for missing site photos)
    visual_appendix = render_pages_to_images(sample_report_pdf, "visual_appendix", start_page=11, end_page=23)
    thermal_scans = render_pages_to_images(thermal_images_pdf, "thermal_scans", start_page=1, end_page=30)
    summary_table = extract_summary_table(sample_report_pdf)
    
    print(f"Rendered {len(visual_appendix)} visual appendix pages and {len(thermal_scans)} thermal scan pages.")
    print(f"Found {len(summary_table)} points in the Summary Table.")
    
    # 2. Analysis Phase (Loop through all 7 primary points)
    print("\n--- 2. Analysis Phase ---")
    ddr_data = []
    
    # Process only the first 7 primary points as per assignment
    for i in range(min(7, len(summary_table))):
        point = summary_table[i]
        point_no = i + 1
        print(f"Analyzing Point #{point_no}...")
        
        # Heuristic mapping for MVP:
        # Each 'Area' in the sample report typically maps to a few pages in the appendix
        # And 1-2 pages in the thermal report.
        v_start = (i * 2) % len(visual_appendix)
        v_end = min(v_start + 2, len(visual_appendix))
        
        # Thermal pages are usually 1:1 with points
        t_page = [thermal_scans[i % len(thermal_scans)]]
        v_pages = visual_appendix[v_start:v_end]
        
        analysis_text = analyze_and_merge_logic(api_key, point, v_pages, t_page)
        
        impacted_val = point.get("Impacted area (-ve side)") or f"Area {point_no}"
        area_name = str(impacted_val).split(" of ")[0]
        
        # Parse analysis_text for structured sections (simplified for MVP)
        section = {
            'area': area_name,
            'observations': analysis_text,
            'root_cause': "See analysis above.",
            'severity': "See analysis above.",
            'reasoning': "Derived from visual and thermal mapping.",
            'actions': "See recommendations above.",
            'images': v_pages + t_page
        }
        ddr_data.append(section)
    
    # 3. Generation Phase
    print("\n--- 3. Generation Phase ---")
    output_md = "output/Main_DDR_Report.md"
    generate_markdown_report(ddr_data, output_md)
    print(f"Full 7-point report successfully generated at: {os.path.abspath(output_md)}")

if __name__ == "__main__":
    main()
