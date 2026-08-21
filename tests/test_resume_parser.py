import os
import pytest
from app.services.parser.text_extractor import TextExtractor
from app.services.parser.deterministic_parser import DeterministicParser
from app.services.parser.resume_parser import ResumeParser


def test_pdf_text_extraction():
    """Test text extraction from synthetic PDF resume fixture."""
    pdf_path = "tests/fixtures/sample_resume_one_page.pdf"
    assert os.path.exists(pdf_path)

    text = TextExtractor.extract_pdf(pdf_path)
    assert "Alice Smith" in text
    assert "alice.smith@example.com" in text
    assert "Python" in text


def test_docx_text_extraction():
    """Test text extraction from synthetic DOCX resume fixture."""
    docx_path = "tests/fixtures/sample_resume_technical.docx"
    assert os.path.exists(docx_path)

    text = TextExtractor.extract_docx(docx_path)
    assert "John Dev" in text
    assert "john.dev@example.com" in text
    assert "FastAPI" in text


def test_deterministic_parser():
    """Test deterministic section parsing."""
    sample_text = """
    Jane Developer
    Email: jane.dev@example.com | Phone: 555-019-9988
    LinkedIn: linkedin.com/in/janedev

    PROFESSIONAL SUMMARY
    Senior Software Engineer with 5 years experience in Python, PostgreSQL, and React.

    SKILLS
    Python, FastAPI, React, PostgreSQL, Docker, Git

    EDUCATION
    State University - B.S. Computer Science (2018 - 2022)
    """

    parsed = DeterministicParser.parse(sample_text)
    assert parsed["contact"]["email"] == "jane.dev@example.com"
    assert parsed["contact"]["phone"] == "555-019-9988"
    assert len(parsed["skills"]) >= 4
    skill_names = [s["name"] for s in parsed["skills"]]
    assert "Python" in skill_names
    assert "React" in skill_names
