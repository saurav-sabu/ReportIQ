import os
import shutil
import fitz # PyMuPDF
import pdfplumber
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def render_pages_to_images(pdf_path, output_subfolder, start_page=1, end_page=None):
    """
    Renders specified pages of a PDF as full images and saves to temp/<output_subfolder>/.
    Returns a list of image file paths.
    """
    if start_page < 1:
        raise ValueError(f"start_page must be >= 1, got {start_page}")
        
    doc = fitz.open(pdf_path)
    output_dir = os.path.join(BASE_DIR, "temp", output_subfolder)
    
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    image_paths = []
    
    if end_page is None:
        end_page = len(doc)
    else:
        end_page = min(end_page, len(doc))
    
    # PDF page index is 0-based
    for page_index in range(start_page - 1, end_page):
        page = doc[page_index]
        # High-resolution pixmap (2.0 zoom factor)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        
        filename = f"page{page_index+1}.png"
        filepath = os.path.join(output_dir, filename)
        pix.save(filepath)
        image_paths.append(filepath)
        
    doc.close()
    return image_paths

def extract_text(pdf_path):
    """
    Extracts all text from the PDF.
    """
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    doc.close()
    return full_text

def extract_summary_table(pdf_path):
    """
    Extracts the Summary Table from Page 10 of Sample Report.pdf
    """
    summary_page = int(os.getenv("SUMMARY_PAGE", "10"))
    page_index = summary_page - 1
    
    with pdfplumber.open(pdf_path) as pdf:
        if len(pdf.pages) < summary_page:
            return None
        
        page = pdf.pages[page_index]
        table = page.extract_table()
        
        if not table:
            return None
            
        # Clean the table data
        def normalize(h):
            return re.sub(r'\s+', ' ', h.strip().lower())

        HEADER_ALIASES = {
            "point no": "Point No",
            "impacted area (-ve side)": "Impacted area (-ve side)",
            "impacted area": "Impacted area (-ve side)",
            "exposed area (+ve side)": "Exposed area (+ve side)",
            "exposed area": "Exposed area (+ve side)",
        }
        headers = [HEADER_ALIASES.get(normalize(h), h.strip()) if h else f"col_{i}" for i, h in enumerate(table[0])]
        
        rows = []
        for row in table[1:]:
            padded = row + [None] * (len(headers) - len(row))
            cleaned = {headers[i]: (cell or "").replace('\n', ' ').strip() for i, cell in enumerate(padded)}
            rows.append(cleaned)
        return rows

def extract_client_metadata(text):
    """Extract client metadata from report text using pattern matching."""
    def find(pattern, default="N/A"):
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else default

    return {
        "client_name": find(r"Customer\s*Name[:\s]+(.+?)(?:\n|$)"),
        "address": find(r"Site\s*Address[:\s]+(.+?)(?:\n|$)"),
        "date": find(r"Date\s*of\s*Inspection[:\s]+(.+?)(?:\n|$)"),
        "inspected_by": find(r"Inspected\s*By[:\s]+(.+?)(?:\n|$)"),
        "property_type": find(r"Type\s*of\s*structure[:\s]+(.+?)(?:\n|$)"),
        "floors": find(r"Floors?[:\s]+(\d+)"),
        "age": find(r"Age\s*of\s*Building[:\s]+(.+?)(?:\n|$)")
    }

if __name__ == "__main__":
    # Quick test
    # print(extract_summary_table("Sample Report.pdf"))
    pass
