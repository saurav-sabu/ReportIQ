import os
import base64
import mimetypes
import textwrap
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from tenacity import retry, wait_exponential, stop_after_attempt

@retry(wait=wait_exponential(min=2, max=30), stop=stop_after_attempt(3))
def call_llm(llm, message):
    return llm.invoke([message])
def encode_image(image_path):
    if not os.path.exists(image_path):
        print(f"WARNING: Image not found: {image_path}")
        return None
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def analyze_and_merge_logic(llm, point_data, visual_pages, thermal_pages):
    """
    Core vision analysis logic for a single DDR point.
    """
    point_no = point_data.get("Point No", "") or point_data.get("PointNo", "")
    impacted = point_data.get("Impacted area (-ve side)", "") or point_data.get("Impacted area", "")
    exposed = point_data.get("Exposed area (+ve side)", "") or point_data.get("Exposed area", "")
    
    prompt = textwrap.dedent(f"""\
    You are an expert Property Diagnostic Inspector.
    
    Analyzing ISSUE POINT #{point_no}:
    - IMPACTED AREA: {impacted}
    - EXPOSED SOURCE AREA: {exposed}
    
    I am providing 2-3 pages from the Visual Appendix and the corresponding Thermal Report page.
    
    YOUR TASK:
    1. Identify the specific 'Photo #' in the Visual Appendix that shows the damage described.
    2. Identify the matching Thermal scan page.
    3. Provide a Detailed Observation: Describe exactly what is seen in both.
    4. State the Probable Root Cause: Link the exposed source to the impacted area.
    5. Severity Assessment: Low, Medium, or High with reasoning.
    6. Recommended Actions: Provide 2-3 professional, actionable steps.
    
    Format the response clearly in sections. 
    If a photo is not clearly found, mention "Photo Not Available" and describe the likely situation based on the technical input.
    """)
    
    # Combine relevant pages
    all_paths = visual_pages + thermal_pages
    content = [{"type": "text", "text": prompt}]
    
    for path in all_paths:
        image_data = encode_image(path)
        if not image_data:
            continue
            
        mime_type = mimetypes.guess_type(path)[0] or "image/png"
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:{mime_type};base64,{image_data}"}
        })
        
    message = HumanMessage(content=content)
    try:
        response = call_llm(llm, message)
    except Exception as e:
        print(f"ERROR: Gemini API call failed for Point #{point_no}: {e}")
        return f"Analysis unavailable due to API error: {e}"
    
    if isinstance(response.content, list):
        return "".join([m.get("text", "") for m in response.content if isinstance(m, dict) and m.get("type") == "text"])
    return response.content
