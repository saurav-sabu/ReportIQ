import os
import shutil
def generate_markdown_report(client_data, ddr_data, summary_table_rows, output_path, max_points=7):
    """
    Generates a high-fidelity Markdown report mirroring 'Main DDR.pdf'.
    Images are copied to output/images/ and linked via relative paths.
    """
    
    branding_company = os.getenv("COMPANY_NAME", "UrbanRoof Private Limited")
    branding_welcome = os.getenv("WELCOME_TEXT", "Thank you for choosing UrbanRoof to help you navigate the health of your property. We have put together this report based on inspection data and its analysis.")
    branding_about = os.getenv("ABOUT_US_TEXT", "The idea, UrbanRoof, was born in 2016 to provide a transparent and straightforward process for the diagnosis & treatment of building constructions. We are obsessed with solving the smallest to the biggest issues of constructed properties.")
    branding_disclaimer = os.getenv("LEGAL_DISCLAIMER", "UrbanRoof has performed a visual and non-destructive test inspection. We accept no responsibility for misuse or misinterpretation by third parties.")
    
    intro_background = os.getenv("INTRO_BACKGROUND", "The site investigation was conducted to carry out a preliminary Health Assessment of the Flat based on testing and visual inspection.")
    intro_objective = os.getenv("INTRO_OBJECTIVE", "- To facilitate detection of all possible flaws and analyze cause-effects.\n- To prioritize immediate repair and protection measures.\n- To evaluate accurate scope of work for execution/treatment.")
    intro_scope = os.getenv("INTRO_SCOPE", "Conducting visual site inspection using necessary assessment tools like Tapping Hammer, Crack gauge, IR Thermography, and Moisture meters.")
    data_disclaimer = os.getenv("DATA_DISCLAIMER", "This property inspection is not an exhaustive inspection of the structure, systems, or components. A health checkup helps to reduce some of the risk involved, but it cannot eliminate these risks.")
    limitation_note = os.getenv("LIMITATION_NOTE", "The information provided is an opinion based on a visual examination of readily accessible features. It does not include identifying defects hidden behind walls, floors, or ceilings.")

    # 1. FRONT MATTER & COVER
    report = f"""# Detailed Diagnosis Report (DDR)
**{branding_company}**

---

**Report Date:** {client_data.get('date', 'N/A')}  
**Prepared For:** {client_data.get('client_name', 'N/A')}  
**Inspected By:** {client_data.get('inspected_by', 'N/A')}

---

## Welcome
{branding_welcome}

## About Us
{branding_about}

---

## Data and Information Disclaimer
{data_disclaimer}

---

## TABLE OF CONTENTS
1. [SECTION 1: INTRODUCTION](#section-1-introduction)
2. [SECTION 2: GENERAL INFORMATION](#section-2-general-information)
3. [SECTION 3: ANALYSIS & SUGGESTIONS](#section-3-analysis--suggestions)
4. [SECTION 4: LIMITATION AND PRECAUTION NOTE](#section-4-limitation-and-precaution-note)

---

<div id="section-1-introduction"></div>

## SECTION 1: INTRODUCTION
### 1.1 BACKGROUND
{intro_background}

### 1.2 OBJECTIVE
{intro_objective}

### 1.3 SCOPE OF WORK
{intro_scope}

---

<div id="section-2-general-information"></div>

## SECTION 2: GENERAL INFORMATION
### 2.1 CLIENT & INSPECTION DETAILS
| Particular | Description |
| :--- | :--- |
| **Customer Name** | {client_data.get('client_name', 'N/A')} |
| **Site Address** | {client_data.get('address', 'N/A')} |
| **Date of Inspection** | {client_data.get('date', 'N/A')} |
| **Inspected By** | {client_data.get('inspected_by', 'N/A')} |

### 2.2 DESCRIPTION OF SITE
| Particular | Description |
| :--- | :--- |
| **Type of structure** | {client_data.get('property_type', 'N/A')} |
| **Floors** | {client_data.get('floors', 'N/A')} |
| **Age of Building** | {client_data.get('age', 'N/A')} |

---

<div id="section-3-analysis--suggestions"></div>

## SECTION 3: ANALYSIS & SUGGESTIONS
Site observations were recorded using high-resolution photography and thermal imaging to document areas of moisture ingress and structural distress.

### 3.1 SUMMARY TABLE
| Point No | Impacted area (-ve side) | Exposed area (+ve side) |
| :--- | :--- | :--- |
"""
    # Append summary table rows
    for row in summary_table_rows[:max_points]:
        p_no = row.get("Point No") or "N/A"
        neg = row.get("Impacted area (-ve side)") or "N/A"
        pos = row.get("Exposed area (+ve side)") or "N/A"
        report += f"| {p_no} | {neg} | {pos} |\n"

    report += """
---

### 3.2 THERMAL REFERENCES (IMPACTED AREAS)
This section contains high-resolution pairings of visual damage and their corresponding thermal signatures.
"""

    output_dir = os.path.dirname(os.path.abspath(output_path))
    img_out_dir = os.path.join(output_dir, "images")
    os.makedirs(img_out_dir, exist_ok=True)
    
    for section in ddr_data:
        report += f"""
#### Area: {section.get('area', 'Unknown')}
**Detailed Observations & Reasoning:**
{section.get('observations', 'N/A')}

**Images:**
"""
        for img_path in section.get('images', []):
            if os.path.exists(img_path):
                source_prefix = os.path.basename(os.path.dirname(img_path))
                unique_name = f"{source_prefix}_{os.path.basename(img_path)}"
                dest_path = os.path.join(img_out_dir, unique_name)
                shutil.copy(img_path, dest_path)
                rel_path = f"images/{unique_name}".replace(os.path.sep, '/')
                report += f"![Reference Image]({rel_path})\n\n"
            
        report += "\n---\n"
        
    report += f"""
<div id="section-4-limitation-and-precaution-note"></div>

## SECTION 4: LIMITATION AND PRECAUTION NOTE
{limitation_note}

## Legal Disclaimer
{branding_disclaimer}
"""
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
    
    return output_path
