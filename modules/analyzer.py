import os
import base64
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from typing import List, Optional

class ObservationMatch(BaseModel):
    is_match: bool = Field(description="True if the visual and thermal images match the same location.")
    confidence: float = Field(description="Confidence score from 0 to 1.")
    area_name: str = Field(description="The name of the area (e.g., Hall, Bathroom).")
    findings: str = Field(description="Detailed findings from the comparison.")

class DDRSection(BaseModel):
    area: str
    issue_summary: str
    observations: str
    root_cause: str
    severity: str
    reasoning: str
    actions: str
    images: List[str] # Paths to images

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def analyze_and_merge_logic(api_key, point_data, visual_pages, thermal_pages):
    """
    Core vision analysis logic for a single DDR point.
    """
    model_name = os.getenv("MODEL_NAME", "gemini-3.1-pro-preview")
    llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key)
    
    point_no = point_data.get("Point No", "") or point_data.get("PointNo", "")
    impacted = point_data.get("Impacted area (-ve side)", "") or point_data.get("Impacted area", "")
    exposed = point_data.get("Exposed area (+ve side)", "") or point_data.get("Exposed area", "")
    
    prompt = f"""
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
    """
    
    # Combine relevant pages
    all_paths = visual_pages + thermal_pages
    content = [{"type": "text", "text": prompt}]
    
    for path in all_paths:
        image_data = encode_image(path)
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
        })
        
    message = HumanMessage(content=content)
    response = llm.invoke([message])
    
    if isinstance(response.content, list):
        return "".join([m.get("text", "") for m in response.content if isinstance(m, dict) and m.get("type") == "text"])
    return response.content
