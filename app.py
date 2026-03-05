"""
GMP CV Generator
Accepts uploaded CVs (PDF/DOCX), parses them, and generates a
new CV using the GMP standard template.
"""

import os
import re
import uuid
from pathlib import Path

import pdfplumber
from docx import Document
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)

from cv_generator import generate_gmp_cv

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "gmp-cv-secret-key")

BASE_DIR = Path(__file__).parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
GENERATED_FOLDER = BASE_DIR / "generated"
ALLOWED_EXTENSIONS = {"pdf", "docx"}

UPLOAD_FOLDER.mkdir(exist_ok=True)
GENERATED_FOLDER.mkdir(exist_ok=True)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------------------------------------------------------------------------
# CV Parsing helpers
# ---------------------------------------------------------------------------

def extract_email(text: str) -> str:
    match = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)
    return match.group(0) if match else ""


def extract_phone(text: str) -> str:
    match = re.search(
        r"(\+?\d[\d\s\-().]{7,}\d)", text
    )
    return match.group(0).strip() if match else ""


def extract_linkedin(text: str) -> str:
    match = re.search(r"linkedin\.com/in/[A-Za-z0-9\-_%]+", text, re.IGNORECASE)
    return match.group(0) if match else ""


_SECTION_HEADERS = {
    "summary": re.compile(
        r"^(summary|profile|objective|about me|professional summary)\s*$", re.I
    ),
    "skills": re.compile(
        r"^(skills|technical skills|core competencies|key skills|expertise)\s*$", re.I
    ),
    "experience": re.compile(
        r"^(experience|work experience|professional experience|employment history|career history)\s*$",
        re.I,
    ),
    "education": re.compile(
        r"^(education|academic background|qualifications|academic qualifications)\s*$", re.I
    ),
    "certifications": re.compile(
        r"^(certifications|certificates|professional development|courses|training)\s*$", re.I
    ),
    "projects": re.compile(r"^(projects|key projects|notable projects)\s*$", re.I),
}


def _classify_line(line: str) -> str | None:
    """Return the section key if *line* looks like a section header."""
    stripped = line.strip()
    for key, pattern in _SECTION_HEADERS.items():
        if pattern.match(stripped):
            return key
    return None


def parse_cv_text(text: str) -> dict:
    """Parse raw CV text and return a structured dictionary."""
    lines = [ln.rstrip() for ln in text.splitlines()]
    non_empty = [ln for ln in lines if ln.strip()]

    data: dict = {
        "name": "",
        "email": extract_email(text),
        "phone": extract_phone(text),
        "linkedin": extract_linkedin(text),
        "summary": [],
        "skills": [],
        "experience": [],
        "education": [],
        "certifications": [],
        "projects": [],
    }

    # Heuristic: the candidate name is the first non-empty, non-contact line
    for ln in non_empty[:5]:
        stripped = ln.strip()
        if (
            stripped
            and not extract_email(stripped)
            and not extract_phone(stripped)
            and not re.search(r"(linkedin|github|http)", stripped, re.I)
            and len(stripped.split()) <= 6
        ):
            data["name"] = stripped
            break

    # Segment the text into sections
    current_section: str | None = None
    buffer: list[str] = []

    def _flush(section: str | None, buf: list[str]) -> None:
        if section and buf:
            content = "\n".join(buf).strip()
            if content:
                data[section].append(content)

    for ln in lines:
        section_key = _classify_line(ln)
        if section_key:
            _flush(current_section, buffer)
            current_section = section_key
            buffer = []
        else:
            if current_section and ln.strip():
                buffer.append(ln)

    _flush(current_section, buffer)

    # Flatten skills into a list of individual skill tokens
    raw_skills: list[str] = []
    for block in data["skills"]:
        # Split on common delimiters
        for part in re.split(r"[,•|\n/]+", block):
            skill = part.strip()
            if skill and len(skill) < 60:
                raw_skills.append(skill)
    data["skills"] = raw_skills

    return data


def parse_pdf(filepath: str) -> dict:
    text_parts: list[str] = []
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return parse_cv_text("\n".join(text_parts))


def parse_docx(filepath: str) -> dict:
    doc = Document(filepath)
    full_text = "\n".join(para.text for para in doc.paragraphs)
    return parse_cv_text(full_text)


def parse_uploaded_cv(filepath: str) -> dict:
    ext = Path(filepath).suffix.lower()
    if ext == ".pdf":
        return parse_pdf(filepath)
    elif ext == ".docx":
        return parse_docx(filepath)
    raise ValueError(f"Unsupported file type: {ext}")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_cv():
    if "cv_file" not in request.files:
        flash("No file part in the request.", "error")
        return redirect(url_for("index"))

    file = request.files["cv_file"]
    if file.filename == "":
        flash("No file selected.", "error")
        return redirect(url_for("index"))

    if not allowed_file(file.filename):
        flash("Only PDF and DOCX files are supported.", "error")
        return redirect(url_for("index"))

    # Save the uploaded file
    unique_id = uuid.uuid4().hex[:8]
    safe_name = f"{unique_id}_{Path(file.filename).name}"
    upload_path = UPLOAD_FOLDER / safe_name
    file.save(str(upload_path))

    # Parse the CV
    try:
        cv_data = parse_uploaded_cv(str(upload_path))
    except Exception as exc:
        flash(f"Could not parse the uploaded CV: {exc}", "error")
        return redirect(url_for("index"))

    # Generate the GMP CV
    output_filename = f"GMP_CV_{unique_id}.pdf"
    output_path = GENERATED_FOLDER / output_filename
    try:
        generate_gmp_cv(cv_data, str(output_path))
    except Exception as exc:
        flash(f"Could not generate the GMP CV: {exc}", "error")
        return redirect(url_for("index"))

    flash("CV successfully generated!", "success")
    return redirect(url_for("preview_cv", filename=output_filename))


@app.route("/preview/<filename>")
def preview_cv(filename: str):
    return render_template("preview.html", filename=filename)


@app.route("/download/<filename>")
def download_cv(filename: str):
    return send_from_directory(str(GENERATED_FOLDER), filename, as_attachment=True)


if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug_mode, port=5000)
