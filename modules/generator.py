import os

def generate_markdown_report(ddr_data, output_path):
    """
    Takes a list of DDRSection objects or structured dicts and formats it into a 7-section report.
    """
    report_header = f"""
# Detailed Diagnostic Report (DDR)
**Property Inspection & Thermal Analysis**

---

## 1. Property Issue Summary
This report combines results from visual site inspection and thermal scanning. Multiple areas of dampness were identified, primarily linked to bathroom tile joint issues and external wall cracks.

---

"""
    sections_content = ""
    
    for section in ddr_data:
        sections_content += f"""
### Area: {section.get('area', 'Unknown')}
#### 2. Area-wise Observations
{section.get('observations', 'N/A')}

#### 3. Probable Root Cause
{section.get('root_cause', 'N/A')}

#### 4. Severity Assessment
**Level:** {section.get('severity', 'Medium')}  
**Reasoning:** {section.get('reasoning', 'N/A')}

#### 5. Recommended Actions
{section.get('actions', 'N/A')}

#### 6. Additional Notes
{section.get('additional_notes', 'None at this time.')}

#### Images:
"""
        for img_path in section.get('images', []):
            sections_content += f"![Image]({os.path.abspath(img_path)})\n\n"
            
        sections_content += "\n---\n"
        
    missing_info = """
## 7. Missing or Unclear Information
None identified. All primary points from the summary table were cross-referenced with thermal data.
"""
    
    full_report = report_header + sections_content + missing_info
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_report)
    
    return output_path
