"""
GMP CV Generator
Generates a PDF CV using the GMP (Global Management Partners) standard template.
"""

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ---------------------------------------------------------------------------
# GMP Brand colours
# ---------------------------------------------------------------------------
GMP_DARK_BLUE = colors.HexColor("#003366")   # header / section titles
GMP_MID_BLUE = colors.HexColor("#005B99")    # sub-headings
GMP_ACCENT = colors.HexColor("#0077CC")      # links / accent lines
GMP_LIGHT_GREY = colors.HexColor("#F4F6F8")  # shaded rows
GMP_TEXT = colors.HexColor("#222222")        # body text
GMP_MUTED = colors.HexColor("#666666")       # secondary text


def _build_styles() -> dict:
    base = getSampleStyleSheet()

    styles = {
        "name": ParagraphStyle(
            "name",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=22,
            textColor=GMP_DARK_BLUE,
            leading=26,
            alignment=TA_LEFT,
        ),
        "contact": ParagraphStyle(
            "contact",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            textColor=GMP_MUTED,
            leading=13,
            alignment=TA_LEFT,
        ),
        "section_title": ParagraphStyle(
            "section_title",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            textColor=GMP_DARK_BLUE,
            leading=14,
            spaceBefore=6,
            spaceAfter=2,
            alignment=TA_LEFT,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            textColor=GMP_TEXT,
            leading=14,
            alignment=TA_JUSTIFY,
        ),
        "body_bold": ParagraphStyle(
            "body_bold",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9.5,
            textColor=GMP_TEXT,
            leading=14,
        ),
        "bullet": ParagraphStyle(
            "bullet",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            textColor=GMP_TEXT,
            leading=14,
            leftIndent=12,
            bulletIndent=0,
            spaceBefore=1,
        ),
        "skill_chip": ParagraphStyle(
            "skill_chip",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            textColor=GMP_MID_BLUE,
            leading=13,
        ),
        "footer": ParagraphStyle(
            "footer",
            parent=base["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=8,
            textColor=GMP_MUTED,
            leading=10,
            alignment=TA_CENTER,
        ),
    }
    return styles


def _section_header(title: str, styles: dict) -> list:
    """Return flowables for a coloured section header with rule."""
    elements = [
        Spacer(1, 4 * mm),
        Paragraph(title.upper(), styles["section_title"]),
        HRFlowable(
            width="100%",
            thickness=1.5,
            color=GMP_ACCENT,
            spaceAfter=3 * mm,
        ),
    ]
    return elements


def _format_block(text: str) -> str:
    """Convert newlines to <br/> for Paragraph rendering."""
    return text.replace("\n", "<br/>")


def generate_gmp_cv(cv_data: dict, output_path: str) -> None:
    """
    Generate a GMP-branded PDF CV.

    Parameters
    ----------
    cv_data : dict
        Parsed CV data with keys: name, email, phone, linkedin,
        summary, skills, experience, education, certifications, projects.
    output_path : str
        Full file path where the generated PDF should be saved.
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=f"GMP CV – {cv_data.get('name', 'Candidate')}",
        author="GMP CV Generator",
    )

    styles = _build_styles()
    story = []

    # ------------------------------------------------------------------
    # Header block: name + contact details
    # ------------------------------------------------------------------
    name = cv_data.get("name") or "Candidate"
    story.append(Paragraph(name, styles["name"]))

    contact_parts = []
    if cv_data.get("email"):
        contact_parts.append(f"✉ {cv_data['email']}")
    if cv_data.get("phone"):
        contact_parts.append(f"✆ {cv_data['phone']}")
    if cv_data.get("linkedin"):
        contact_parts.append(f"in {cv_data['linkedin']}")

    if contact_parts:
        story.append(
            Paragraph("  |  ".join(contact_parts), styles["contact"])
        )

    story.append(
        HRFlowable(
            width="100%",
            thickness=3,
            color=GMP_DARK_BLUE,
            spaceBefore=3 * mm,
            spaceAfter=4 * mm,
        )
    )

    # ------------------------------------------------------------------
    # Professional Summary
    # ------------------------------------------------------------------
    if cv_data.get("summary"):
        story.extend(_section_header("Professional Summary", styles))
        for block in cv_data["summary"]:
            story.append(Paragraph(_format_block(block), styles["body"]))
            story.append(Spacer(1, 2 * mm))

    # ------------------------------------------------------------------
    # Core Skills
    # ------------------------------------------------------------------
    if cv_data.get("skills"):
        story.extend(_section_header("Core Skills & Competencies", styles))
        skills = cv_data["skills"]
        # Lay out skills as a two-column table of bullet items
        rows = []
        for i in range(0, len(skills), 2):
            left = Paragraph(f"▪  {skills[i]}", styles["bullet"])
            right = (
                Paragraph(f"▪  {skills[i + 1]}", styles["bullet"])
                if i + 1 < len(skills)
                else Paragraph("", styles["bullet"])
            )
            rows.append([left, right])

        if rows:
            tbl = Table(rows, colWidths=["50%", "50%"])
            tbl.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                        ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ]
                )
            )
            story.append(tbl)
            story.append(Spacer(1, 2 * mm))

    # ------------------------------------------------------------------
    # Professional Experience
    # ------------------------------------------------------------------
    if cv_data.get("experience"):
        story.extend(_section_header("Professional Experience", styles))
        for block in cv_data["experience"]:
            lines = block.strip().splitlines()
            # First line is treated as the role/company heading
            if lines:
                story.append(Paragraph(lines[0], styles["body_bold"]))
                for ln in lines[1:]:
                    stripped = ln.strip()
                    if stripped:
                        bullet_text = stripped.lstrip("•-–—* ")
                        story.append(
                            Paragraph(f"• {bullet_text}", styles["bullet"])
                        )
            story.append(Spacer(1, 3 * mm))

    # ------------------------------------------------------------------
    # Education
    # ------------------------------------------------------------------
    if cv_data.get("education"):
        story.extend(_section_header("Education", styles))
        for block in cv_data["education"]:
            lines = block.strip().splitlines()
            if lines:
                story.append(Paragraph(lines[0], styles["body_bold"]))
                for ln in lines[1:]:
                    stripped = ln.strip()
                    if stripped:
                        story.append(Paragraph(stripped, styles["body"]))
            story.append(Spacer(1, 2 * mm))

    # ------------------------------------------------------------------
    # Certifications
    # ------------------------------------------------------------------
    if cv_data.get("certifications"):
        story.extend(_section_header("Certifications & Professional Development", styles))
        for block in cv_data["certifications"]:
            for ln in block.strip().splitlines():
                stripped = ln.strip()
                if stripped:
                    story.append(Paragraph(f"▪  {stripped}", styles["bullet"]))
        story.append(Spacer(1, 2 * mm))

    # ------------------------------------------------------------------
    # Projects
    # ------------------------------------------------------------------
    if cv_data.get("projects"):
        story.extend(_section_header("Key Projects", styles))
        for block in cv_data["projects"]:
            lines = block.strip().splitlines()
            if lines:
                story.append(Paragraph(lines[0], styles["body_bold"]))
                for ln in lines[1:]:
                    stripped = ln.strip()
                    if stripped:
                        story.append(
                            Paragraph(f"• {stripped}", styles["bullet"])
                        )
            story.append(Spacer(1, 2 * mm))

    # ------------------------------------------------------------------
    # Footer
    # ------------------------------------------------------------------
    story.append(Spacer(1, 8 * mm))
    story.append(
        HRFlowable(width="100%", thickness=0.5, color=GMP_MUTED, spaceAfter=2 * mm)
    )
    story.append(
        Paragraph(
            "Generated by GMP CV System  •  Confidential",
            styles["footer"],
        )
    )

    doc.build(story)
