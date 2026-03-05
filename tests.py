"""
Tests for GMP CV Generator application.
"""

import io
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure project root is on the path
sys.path.insert(0, str(Path(__file__).parent))

from app import allowed_file, parse_cv_text, extract_email, extract_phone, extract_linkedin
from cv_generator import generate_gmp_cv


# ---------------------------------------------------------------------------
# Unit tests – helper functions
# ---------------------------------------------------------------------------

class TestAllowedFile:
    def test_pdf_allowed(self):
        assert allowed_file("resume.pdf") is True

    def test_docx_allowed(self):
        assert allowed_file("cv.docx") is True

    def test_txt_not_allowed(self):
        assert allowed_file("resume.txt") is False

    def test_no_extension(self):
        assert allowed_file("resume") is False

    def test_uppercase_extension(self):
        assert allowed_file("resume.PDF") is True


class TestExtractContact:
    def test_extract_email(self):
        assert extract_email("Contact: john.doe@example.com today") == "john.doe@example.com"

    def test_extract_email_missing(self):
        assert extract_email("No email here") == ""

    def test_extract_phone_uk(self):
        phone = extract_phone("Call me on +44 7700 900123 anytime")
        assert phone != ""

    def test_extract_phone_missing(self):
        assert extract_phone("No phone here") == ""

    def test_extract_linkedin(self):
        result = extract_linkedin("Visit linkedin.com/in/johndoe for my profile")
        assert result == "linkedin.com/in/johndoe"

    def test_extract_linkedin_missing(self):
        assert extract_linkedin("No LinkedIn") == ""


class TestParseCvText:
    SAMPLE_CV = """John Doe
john.doe@email.com | +44 7700 900123 | linkedin.com/in/johndoe

Summary
Experienced software engineer with 8+ years building scalable web applications.

Skills
Python, JavaScript, React, AWS, Docker

Experience
Senior Software Engineer – TechCorp (2020–Present)
Led architecture of microservices platform
Reduced cloud costs by 30%

Education
BSc Computer Science – University of Manchester (2014–2018)

Certifications
AWS Certified Solutions Architect
"""

    def test_name_extracted(self):
        data = parse_cv_text(self.SAMPLE_CV)
        assert data["name"] == "John Doe"

    def test_email_extracted(self):
        data = parse_cv_text(self.SAMPLE_CV)
        assert data["email"] == "john.doe@email.com"

    def test_phone_extracted(self):
        data = parse_cv_text(self.SAMPLE_CV)
        assert data["phone"] != ""

    def test_linkedin_extracted(self):
        data = parse_cv_text(self.SAMPLE_CV)
        assert "johndoe" in data["linkedin"]

    def test_summary_extracted(self):
        data = parse_cv_text(self.SAMPLE_CV)
        assert len(data["summary"]) > 0
        assert "software engineer" in data["summary"][0].lower()

    def test_skills_extracted(self):
        data = parse_cv_text(self.SAMPLE_CV)
        assert "Python" in data["skills"]
        assert "AWS" in data["skills"]

    def test_experience_extracted(self):
        data = parse_cv_text(self.SAMPLE_CV)
        assert len(data["experience"]) > 0
        assert "TechCorp" in data["experience"][0]

    def test_education_extracted(self):
        data = parse_cv_text(self.SAMPLE_CV)
        assert len(data["education"]) > 0
        assert "Manchester" in data["education"][0]

    def test_certifications_extracted(self):
        data = parse_cv_text(self.SAMPLE_CV)
        assert len(data["certifications"]) > 0

    def test_minimal_cv(self):
        """Parser should not crash on minimal input."""
        data = parse_cv_text("Jane Smith\njane@example.com")
        assert data["name"] == "Jane Smith"
        assert data["email"] == "jane@example.com"

    def test_empty_cv(self):
        """Parser should not crash on empty input."""
        data = parse_cv_text("")
        assert data["name"] == ""
        assert data["skills"] == []


# ---------------------------------------------------------------------------
# Unit tests – PDF generation
# ---------------------------------------------------------------------------

class TestGenerateGmpCv:
    def _minimal_data(self) -> dict:
        return {
            "name": "Test Candidate",
            "email": "test@example.com",
            "phone": "+1 555 0100",
            "linkedin": "linkedin.com/in/testcandidate",
            "summary": ["Experienced professional."],
            "skills": ["Python", "Leadership", "Communication"],
            "experience": ["Software Engineer – Acme Corp\nBuilt things\nFixed bugs"],
            "education": ["BSc Computer Science – Test University (2015–2019)"],
            "certifications": ["AWS Certified"],
            "projects": [],
        }

    def test_pdf_created(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            path = tmp.name
        try:
            generate_gmp_cv(self._minimal_data(), path)
            assert Path(path).exists()
            assert Path(path).stat().st_size > 1000  # non-trivial PDF
        finally:
            os.unlink(path)

    def test_pdf_valid_header(self):
        """Generated file should start with the PDF magic bytes."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            path = tmp.name
        try:
            generate_gmp_cv(self._minimal_data(), path)
            with open(path, "rb") as f:
                header = f.read(4)
            assert header == b"%PDF"
        finally:
            os.unlink(path)

    def test_empty_sections_do_not_crash(self):
        """Generator should handle all-empty sections gracefully."""
        data = {k: [] for k in
                ["summary", "skills", "experience", "education", "certifications", "projects"]}
        data["name"] = ""
        data["email"] = ""
        data["phone"] = ""
        data["linkedin"] = ""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            path = tmp.name
        try:
            generate_gmp_cv(data, path)
            assert Path(path).exists()
        finally:
            os.unlink(path)

    def test_many_skills(self):
        """Odd number of skills should not crash the two-column layout."""
        data = self._minimal_data()
        data["skills"] = [f"Skill {i}" for i in range(1, 12)]  # 11 skills – odd
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            path = tmp.name
        try:
            generate_gmp_cv(data, path)
            assert Path(path).exists()
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# Integration tests – Flask routes
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    import app as flask_app
    flask_app.app.config["TESTING"] = True
    flask_app.app.config["WTF_CSRF_ENABLED"] = False
    with flask_app.app.test_client() as client:
        yield client


class TestFlaskRoutes:
    def test_index_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"GMP" in resp.data

    def test_upload_no_file_redirects(self, client):
        resp = client.post("/upload", data={})
        assert resp.status_code == 302  # redirect back to index

    def test_upload_empty_filename_redirects(self, client):
        data = {"cv_file": (io.BytesIO(b""), "")}
        resp = client.post("/upload", data=data, content_type="multipart/form-data")
        assert resp.status_code == 302

    def test_upload_unsupported_type_redirects(self, client):
        data = {"cv_file": (io.BytesIO(b"hello"), "resume.txt")}
        resp = client.post("/upload", data=data, content_type="multipart/form-data")
        assert resp.status_code == 302

    def test_upload_valid_pdf(self, client):
        """Upload the sample CV and verify a generated PDF is produced."""
        sample_pdf = Path(__file__).parent / "sample_cvs" / "original_cv_john_doe.pdf"
        if not sample_pdf.exists():
            pytest.skip("Sample CV not present")
        with open(sample_pdf, "rb") as f:
            data = {"cv_file": (f, "original_cv_john_doe.pdf")}
            resp = client.post("/upload", data=data, content_type="multipart/form-data")
        # Should redirect to /preview/<filename>
        assert resp.status_code == 302
        location = resp.headers.get("Location", "")
        assert "preview" in location

    def test_download_nonexistent_file_404(self, client):
        resp = client.get("/download/nonexistent_file.pdf")
        assert resp.status_code == 404
