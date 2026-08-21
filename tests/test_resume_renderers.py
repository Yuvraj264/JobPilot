import os
import pytest
from app.services.tailoring.renderers.standard_pdf_renderer import StandardPDFRenderer
from app.services.tailoring.renderers.standard_docx_renderer import StandardDOCXRenderer


def test_resume_renderers():
    doc_data = {
        "header": {
            "full_name": "Test Candidate",
            "email": "test@example.com",
            "phone": "555-0199",
            "location": "Bangalore, India"
        },
        "summary": "Results-driven QA Engineer with 3.0 years of experience.",
        "skills": [{"name": "Python"}, {"name": "SQL"}, {"name": "Selenium"}],
        "projects": [
            {"name": "Test Automation Suite", "description": "Automated regression tests", "technologies": "Python, Selenium"}
        ],
        "education": [
            {"degree": "Bachelor of Technology", "field_of_study": "Computer Science", "institution": "Tech University"}
        ]
    }

    os.makedirs("./storage/test_output", exist_ok=True)
    pdf_path = "./storage/test_output/test_resume.pdf"
    docx_path = "./storage/test_output/test_resume.docx"

    # 1. Render PDF
    res_pdf = StandardPDFRenderer.render_pdf(doc_data, pdf_path)
    assert os.path.exists(res_pdf)
    assert os.path.getsize(res_pdf) > 0

    # 2. Render DOCX
    res_docx = StandardDOCXRenderer.render_docx(doc_data, docx_path)
    assert os.path.exists(res_docx)
    assert os.path.getsize(res_docx) > 0
