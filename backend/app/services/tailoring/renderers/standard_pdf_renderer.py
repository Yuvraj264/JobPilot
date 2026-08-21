import os
from typing import Dict, Any

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


class StandardPDFRenderer:
    """
    Standard PDF Renderer generating clean, ATS-scannable PDF documents with selectable text.
    """

    @staticmethod
    def _to_str(val: Any) -> str:
        if not val:
            return ""
        if isinstance(val, list):
            return ", ".join([str(x) for x in val])
        return str(val)

    @classmethod
    def render_pdf(cls, doc_data: Dict[str, Any], output_path: str) -> str:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        if HAS_REPORTLAB:
            doc = SimpleDocTemplate(output_path, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
            styles = getSampleStyleSheet()

            story = []

            # Header
            header = doc_data.get("header", {})
            story.append(Paragraph(f"<b><font size=16>{header.get('full_name', '')}</font></b>", styles["Heading1"]))
            contact_str = f"Email: {header.get('email', '')} | Phone: {header.get('phone', 'N/A')} | Location: {header.get('location', 'N/A')}"
            story.append(Paragraph(contact_str, styles["Normal"]))
            story.append(Spacer(1, 10))

            # Summary
            story.append(Paragraph("<b>PROFESSIONAL SUMMARY</b>", styles["Heading2"]))
            story.append(Paragraph(doc_data.get("summary", ""), styles["Normal"]))
            story.append(Spacer(1, 10))

            # Skills
            story.append(Paragraph("<b>TECHNICAL SKILLS</b>", styles["Heading2"]))
            skills_list = [s.get("name", "") if isinstance(s, dict) else str(s) for s in doc_data.get("skills", [])]
            story.append(Paragraph(", ".join(skills_list), styles["Normal"]))
            story.append(Spacer(1, 10))

            # Projects
            projects = doc_data.get("projects", [])
            if projects:
                story.append(Paragraph("<b>PROJECTS</b>", styles["Heading2"]))
                for p in projects:
                    techs = cls._to_str(p.get("technologies"))
                    p_title = f"<b>{p.get('name')}</b> ({techs})"
                    story.append(Paragraph(p_title, styles["Normal"]))
                    if p.get("description"):
                        story.append(Paragraph(cls._to_str(p.get("description")), styles["Normal"]))
                    story.append(Spacer(1, 5))
                story.append(Spacer(1, 5))

            # Education
            education = doc_data.get("education", [])
            if education:
                story.append(Paragraph("<b>EDUCATION</b>", styles["Heading2"]))
                for ed in education:
                    ed_str = f"{ed.get('degree')} in {ed.get('field_of_study', '')} - {ed.get('institution')}"
                    story.append(Paragraph(ed_str, styles["Normal"]))

            doc.build(story)
            return output_path

        # Fallback PDF generator using raw PDF stream syntax if ReportLab is absent
        header = doc_data.get("header", {})
        summary = doc_data.get("summary", "")
        skills_str = ", ".join([s.get("name", "") if isinstance(s, dict) else str(s) for s in doc_data.get("skills", [])])

        pdf_content = (
            f"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
            f"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n"
            f"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<</Font<</F1 4 0 R>>>>/Contents 5 0 R>>endobj\n"
            f"4 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
            f"5 0 obj<</Length 250>>stream\nBT /F1 14 Tf 50 720 TD ({header.get('full_name', '')}) Tj ET\n"
            f"BT /F1 10 Tf 50 700 TD (Email: {header.get('email', '')}) Tj ET\n"
            f"BT /F1 10 Tf 50 670 TD (SUMMARY: {summary[:60]}) Tj ET\n"
            f"BT /F1 10 Tf 50 640 TD (SKILLS: {skills_str[:60]}) Tj ET\n"
            f"endstream\nendobj\nxref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000052 00000 n \n0000000052 00000 n \n0000000102 00000 n \n0000000212 00000 n \n0000000282 00000 n \ntrailer<</Size 6/Root 1 0 R>>\nstartxref\n580\n%%EOF"
        )
        with open(output_path, "w", encoding="latin-1") as f:
            f.write(pdf_content)

        return output_path
