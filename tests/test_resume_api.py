import io
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_resume_api_full_flow():
    """Test full API lifecycle: upload -> status -> parsed -> quality -> consistency -> set-default -> download -> delete."""
    # 1. Upload PDF Resume
    pdf_fixture = "tests/fixtures/sample_resume_one_page.pdf"
    with open(pdf_fixture, "rb") as f:
        file_bytes = f.read()

    res_upload = client.post(
        "/api/resumes",
        data={"name": "API Test Resume"},
        files={"file": ("sample_resume_one_page.pdf", io.BytesIO(file_bytes), "application/pdf")},
    )
    assert res_upload.status_code == 201
    resume_id = res_upload.json()["id"]

    # 2. List Resumes
    res_list = client.get("/api/resumes")
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1

    # 3. Get Resume Status
    res_status = client.get(f"/api/resumes/{resume_id}/status")
    assert res_status.status_code == 200
    assert res_status.json()["processing_status"] == "PROCESSED"

    # 4. Get Parsed Data
    res_parsed = client.get(f"/api/resumes/{resume_id}/parsed")
    assert res_parsed.status_code == 200
    parsed_data = res_parsed.json()
    assert len(parsed_data["skills"]) > 0

    # 5. Get Quality Score
    res_qual = client.get(f"/api/resumes/{resume_id}/quality")
    assert res_qual.status_code == 200
    assert res_qual.json()["score"] > 50

    # 6. Get Consistency Report
    res_cons = client.get(f"/api/resumes/{resume_id}/consistency")
    assert res_cons.status_code == 200
    assert "status" in res_cons.json()

    # 7. Set Default
    res_def = client.post(f"/api/resumes/{resume_id}/set-default")
    assert res_def.status_code == 200
    assert res_def.json()["is_default"] is True

    # 8. Reprocess
    res_reproc = client.post(f"/api/resumes/{resume_id}/reprocess")
    assert res_reproc.status_code == 200
    assert res_reproc.json()["processing_status"] == "PROCESSED"

    # 9. Download
    res_dl = client.get(f"/api/resumes/{resume_id}/download")
    assert res_dl.status_code == 200
    assert res_dl.headers["content-type"] == "application/pdf"

    # 10. Delete
    res_del = client.delete(f"/api/resumes/{resume_id}")
    assert res_del.status_code == 204
