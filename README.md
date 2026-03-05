# GMP CV Generator

A web application that automatically converts uploaded CVs into the **GMP standard template**.

## Features

- Upload a CV in **PDF** or **DOCX** format
- Automatically extracts candidate name, contact details, summary, skills, experience, education, certifications, and projects
- Generates a polished, GMP-branded **PDF CV** instantly
- Download the generated CV with a single click

## Sample Reference CVs

The `sample_cvs/` directory contains two reference files:

| File | Description |
|------|-------------|
| `original_cv_john_doe.pdf` | Original candidate CV (example input) |
| `gmp_cv_john_doe.pdf` | Generated GMP-template CV (example output) |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

Open your browser at **http://localhost:5000** and upload a CV.

## Project Structure

```
.
├── app.py              # Flask web application & CV parser
├── cv_generator.py     # ReportLab-based GMP PDF generator
├── requirements.txt    # Python dependencies
├── templates/
│   ├── index.html      # Upload form
│   └── preview.html    # Download/preview page
├── static/
│   └── style.css       # GMP-branded styles
├── sample_cvs/         # Reference CVs (input & output examples)
├── uploads/            # Uploaded CVs (runtime, git-ignored)
└── generated/          # Generated GMP CVs (runtime, git-ignored)
```

## How It Works

1. **Upload** – candidate uploads a PDF or DOCX CV through the web interface
2. **Parse** – the system extracts structured information (name, contact, skills, experience, etc.)
3. **Generate** – a new PDF is produced using the GMP standard template with consistent branding
4. **Download** – the candidate or recruiter downloads the finished GMP CV

## Running Tests

```bash
pip install pytest
python -m pytest tests.py -v
```
