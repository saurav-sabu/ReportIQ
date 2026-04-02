import os
import fitz # PyMuPDF
import pdfplumber
import pandas as pd

def extract_images(pdf_path, output_subfolder):
    """
    Extracts all images from the PDF and saves them to temp/<output_subfolder>/
    """
    doc = fitz.open(pdf_path)
    output_dir = os.path.join("temp", output_subfolder)
    os.makedirs(output_dir, exist_ok=True)
    
    image_list = []
    
    for page_index in range(len(doc)):
        page = doc[page_index]
        images = page.get_images(full=True)
        
        for img_index, img in enumerate(images):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            ext = base_image["ext"]
            
            filename = f"page{page_index+1}_img{img_index+1}.{ext}"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, "wb") as f:
                f.write(image_bytes)
            
            image_list.append({
                "page": page_index + 1,
                "path": filepath,
                "filename": filename
            })
            
    doc.close()
    return image_list

def render_pages_to_images(pdf_path, output_subfolder, start_page=1, end_page=None):
    """
    Renders specified pages of a PDF as full images and saves to temp/<output_subfolder>/.
    Returns a list of image file paths.
    """
    doc = fitz.open(pdf_path)
    output_dir = os.path.join("temp", output_subfolder)
    os.makedirs(output_dir, exist_ok=True)
    
    image_paths = []
    
    if end_page is None:
        end_page = len(doc)
    
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
        df = pd.DataFrame(table[1:], columns=table[0])
        # The table has Impacted area (-ve side) and Exposed area (+ve side)
        # We need to clean the newlines in the cells
        df = df.replace('\n', ' ', regex=True)
        
        return df.to_dict(orient='records')

if __name__ == "__main__":
    # Quick test
    # print(extract_summary_table("Sample Report.pdf"))
    pass
