import os
import shutil
import fitz # PyMuPDF
import pdfplumber

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def render_pages_to_images(pdf_path, output_subfolder, start_page=1, end_page=None):
    """
    Renders specified pages of a PDF as full images and saves to temp/<output_subfolder>/.
    Returns a list of image file paths.
    """
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
    with pdfplumber.open(pdf_path) as pdf:
        # Page 10 is index 9
        if len(pdf.pages) < 10:
            return None
        
        page = pdf.pages[9]
        table = page.extract_table()
        
        if not table:
            return None
            
        # Clean the table data
        headers = [h.strip() if h else f"col_{i}" for i, h in enumerate(table[0])]
        rows = []
        for row in table[1:]:
            cleaned = {headers[i]: (cell or "").replace('\n', ' ').strip() for i, cell in enumerate(row)}
            rows.append(cleaned)
        return rows

import re

def extract_client_metadata(text):
    """Extract client metadata from report text using pattern matching."""
    def find(pattern, default="N/A"):
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else default

    return {
        "client_name": find(r"Customer\s*Name[:\s]+(.+)"),
        "address": find(r"Site\s*Address[:\s]+(.+)"),
        "date": find(r"Date\s*of\s*Inspection[:\s]+(.+)"),
        "inspected_by": find(r"Inspected\s*By[:\s]+(.+)"),
        "property_type": find(r"Type\s*of\s*structure[:\s]+(.+)"),
        "floors": find(r"Floors?[:\s]+(\d+)"),
        "age": find(r"Age\s*of\s*Building[:\s]+(.+)")
    }

if __name__ == "__main__":
    # Quick test
    # print(extract_summary_table("Sample Report.pdf"))
    pass
