"""Build the employer-facing CV as a polished, editable A4 Word document."""
import io
import os

from docx import Document as DocxDocument
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.image.image import Image as DocxImage
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from app.models.cv_profile import CVProfile

AUTHORITY = "17313B"
TEAL = "167E8C"
TEAL_LIGHT = "EAF5F5"
CORAL = "D65B50"
GOLD = "D6A84A"
INK = "24363D"
MUTED = "66777D"
LINE = "D5E1E3"
SOFT = "F4F8F8"
WHITE = "FFFFFF"
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOGO_PATH = os.path.join(BASE_DIR, "static", "img", "logo.png")


def _rgb(value):
    return RGBColor.from_string(value)


def _shade_cell(cell, color):
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), color)
    cell._tc.get_or_add_tcPr().append(shd)


def _cell_margins(cell, top=100, start=120, bottom=100, end=120):
    tc_pr = cell._tc.get_or_add_tcPr()
    margins = tc_pr.first_child_found_in("w:tcMar")
    if margins is None:
        margins = OxmlElement("w:tcMar")
        tc_pr.append(margins)
    for side, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = margins.find(qn(f"w:{side}"))
        if node is None:
            node = OxmlElement(f"w:{side}")
            margins.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def _set_borders(table, color=LINE, size="6", outside=True, inside=True):
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        if edge.startswith("inside") and not inside:
            continue
        if edge in ("top", "left", "bottom", "right") and not outside:
            continue
        element = OxmlElement(f"w:{edge}")
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), size)
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), color)
        borders.append(element)
    table._tbl.tblPr.append(borders)


def _set_widths(table, widths):
    table.autofit = False
    for row in table.rows:
        for cell, width in zip(row.cells, widths):
            cell.width = Cm(width)


def _set_cell_text(cell, text, size=9, bold=False, color=INK, align=None):
    cell.text = ""
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    _cell_margins(cell)
    paragraph = cell.paragraphs[0]
    paragraph.paragraph_format.space_after = Pt(0)
    if align is not None:
        paragraph.alignment = align
    run = paragraph.add_run(str(text) if text not in (None, "") else "—")
    run.font.name = "Aptos"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Aptos")
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = _rgb(color)
    return run


def _section_title(doc, en, ar):
    table = doc.add_table(rows=1, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    _set_widths(table, (11.8, 5.6))
    _shade_cell(table.cell(0, 0), AUTHORITY)
    _shade_cell(table.cell(0, 1), TEAL)
    _set_cell_text(table.cell(0, 0), en.upper(), size=9.5, bold=True, color=WHITE)
    _set_cell_text(table.cell(0, 1), ar, size=9, bold=True, color=WHITE, align=WD_ALIGN_PARAGRAPH.RIGHT)
    _set_borders(table, color=AUTHORITY, size="0", outside=False, inside=False)
    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_after = Pt(1)
    spacer.paragraph_format.space_before = Pt(4)


def _info_table(doc, rows, widths=(4.4, 2.8, 10.2)):
    table = doc.add_table(rows=len(rows), cols=3)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    _set_widths(table, widths)
    for row, (label_en, label_ar, value) in zip(table.rows, rows):
        _set_cell_text(row.cells[0], label_en, size=8.5, bold=True)
        _set_cell_text(row.cells[1], label_ar, size=8.2, color=MUTED, align=WD_ALIGN_PARAGRAPH.RIGHT)
        _set_cell_text(row.cells[2], value, size=8.8)
        _shade_cell(row.cells[0], SOFT)
        _shade_cell(row.cells[1], SOFT)
    _set_borders(table)
    return table


def _fitted_size_cm(file_path, max_width, max_height):
    try:
        image = DocxImage.from_file(file_path)
        ratio = min(max_width / image.px_width, max_height / image.px_height)
        return image.px_width * ratio, image.px_height * ratio
    except Exception:
        return max_width, max_height


def _photo_cell(cell, file_path, caption, max_width, max_height):
    cell.text = ""
    _cell_margins(cell, top=140, start=140, bottom=80, end=140)
    _shade_cell(cell, "FBFDFD")
    paragraph = cell.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    ext = file_path.rsplit(".", 1)[-1].lower() if file_path and "." in file_path else ""
    if file_path and os.path.exists(file_path) and ext in ("jpg", "jpeg", "png"):
        width, height = _fitted_size_cm(file_path, max_width, max_height)
        paragraph.add_run().add_picture(file_path, width=Cm(width), height=Cm(height))
    else:
        _set_cell_text(cell, "Photo not on file" if not file_path else "On file as PDF", size=8, color=MUTED, align=WD_ALIGN_PARAGRAPH.CENTER)
    caption_paragraph = cell.add_paragraph()
    caption_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption_run = caption_paragraph.add_run(caption.upper())
    caption_run.font.name = "Aptos"
    caption_run.font.size = Pt(7.5)
    caption_run.font.bold = True
    caption_run.font.color.rgb = _rgb(AUTHORITY)


def _header(doc, applicant, profile, portrait_doc, company_name):
    table = doc.add_table(rows=1, cols=3)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    _set_widths(table, (3.6, 9.0, 5.0))
    _photo_cell(table.cell(0, 0), portrait_doc.file_path if portrait_doc else None, "Portrait", 2.8, 2.8)
    center = table.cell(0, 1)
    center.text = ""
    _shade_cell(center, AUTHORITY)
    _cell_margins(center, top=220, start=220, bottom=180, end=220)
    p = center.paragraphs[0]
    run = p.add_run("JOB APPLICATION")
    run.font.name = "Aptos"
    run.font.size = Pt(8)
    run.font.bold = True
    run.font.color.rgb = _rgb("9CE2E5")
    title = center.add_paragraph()
    run = title.add_run("CURRICULUM VITAE")
    run.font.name = "Aptos Display"
    run.font.size = Pt(18)
    run.font.bold = True
    run.font.color.rgb = _rgb(WHITE)
    sub = center.add_paragraph()
    run = sub.add_run("طلب توظيف — السيرة الذاتية")
    run.font.size = Pt(9)
    run.font.color.rgb = _rgb("D4E5E7")
    name = center.add_paragraph()
    run = name.add_run(applicant.full_name.upper())
    run.font.name = "Aptos Display"
    run.font.size = Pt(11)
    run.font.bold = True
    run.font.color.rgb = _rgb(WHITE)
    right = table.cell(0, 2)
    right.text = ""
    _shade_cell(right, TEAL_LIGHT)
    _cell_margins(right, top=220, start=180, bottom=180, end=180)
    if os.path.exists(LOGO_PATH):
        logo = right.paragraphs[0]
        logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        logo.add_run().add_picture(LOGO_PATH, width=Cm(3.7))
    _set_cell_text(right, company_name, size=7.5, bold=True, color=AUTHORITY, align=WD_ALIGN_PARAGRAPH.CENTER)
    _set_borders(table, color=AUTHORITY, size="8", outside=True, inside=False)


def _application_cards(doc, profile):
    table = doc.add_table(rows=1, cols=4)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    _set_widths(table, (4.4, 4.4, 4.4, 4.4))
    values = [
        ("APPLICATION NO", f"#{profile.application_no}"),
        ("POST APPLIED FOR", profile.post_applied_for),
        ("MONTHLY SALARY", f"{profile.monthly_salary} {profile.salary_currency}" if profile.monthly_salary else None),
        ("CONTRACT PERIOD", f"{profile.contract_period_years} YEARS" if profile.contract_period_years else None),
    ]
    for cell, (label, value) in zip(table.rows[0].cells, values):
        cell.text = ""
        _shade_cell(cell, TEAL_LIGHT)
        _cell_margins(cell, top=130, start=130, bottom=130, end=130)
        label_p = cell.paragraphs[0]
        label_run = label_p.add_run(label)
        label_run.font.size = Pt(6.5)
        label_run.font.bold = True
        label_run.font.color.rgb = _rgb(MUTED)
        value_p = cell.add_paragraph()
        value_run = value_p.add_run(str(value) if value not in (None, "") else "—")
        value_run.font.name = "Aptos Display"
        value_run.font.size = Pt(9)
        value_run.font.bold = True
        value_run.font.color.rgb = _rgb(AUTHORITY)
    _set_borders(table, color=LINE, size="5")


def _ratings(doc, title, arabic, items, levels, percentages):
    _section_title(doc, title, arabic)
    table = doc.add_table(rows=len(items), cols=3)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    _set_widths(table, (5.0, 9.1, 3.3))
    for row, (label, level) in zip(table.rows, zip(items, levels)):
        _set_cell_text(row.cells[0], label, size=8.5, bold=True)
        _shade_cell(row.cells[1], SOFT)
        track = row.cells[1].paragraphs[0]
        track.paragraph_format.space_after = Pt(0)
        amount = max(1, round(percentages.get(level, 0) / 10))
        run = track.add_run("●" * amount + "·" * (10 - amount))
        run.font.size = Pt(8)
        run.font.color.rgb = _rgb(TEAL if percentages.get(level, 0) >= 70 else GOLD if percentages.get(level, 0) >= 40 else CORAL)
        _set_cell_text(row.cells[2], level.title(), size=8, color=MUTED, align=WD_ALIGN_PARAGRAPH.RIGHT)
    _set_borders(table, color=LINE, size="3")


def _footer(doc, company_name, company_phone, company_email, company_address_en, profile):
    table = doc.add_table(rows=1, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    _set_widths(table, (11.8, 5.6))
    _set_cell_text(table.cell(0, 0), f"{company_name}  •  {company_phone}  •  {company_email}\n{company_address_en}", size=7.5, color=MUTED)
    _set_cell_text(table.cell(0, 1), f"APPLICATION #{profile.application_no}\nGENERATED {profile.updated_at.strftime('%Y-%m-%d')}", size=7.5, bold=True, color=AUTHORITY, align=WD_ALIGN_PARAGRAPH.RIGHT)
    _set_borders(table, color=LINE, size="5", outside=False, inside=False)


def build_cv_docx(applicant, profile, company_name, company_phone, company_email, company_address_en,
                  portrait_doc=None, full_doc=None, passport_doc=None):
    """Return a polished, editable A4 Word CV as a BytesIO buffer."""
    doc = DocxDocument()
    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.left_margin = section.right_margin = Cm(1.8)
    section.top_margin = section.bottom_margin = Cm(1.35)

    normal = doc.styles["Normal"]
    normal.font.name = "Aptos"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Aptos")
    normal.font.size = Pt(9)
    normal.font.color.rgb = _rgb(INK)

    _header(doc, applicant, profile, portrait_doc, company_name)
    _application_cards(doc, profile)
    intro = doc.add_paragraph()
    intro.paragraph_format.space_before = Pt(5)
    run = intro.add_run("EMPLOYMENT PROFILE")
    run.font.size = Pt(8)
    run.font.bold = True
    run.font.color.rgb = _rgb(TEAL)
    if profile.partner:
        partner = doc.add_paragraph()
        run = partner.add_run(f"Presented in partnership with {profile.partner.name} — {profile.partner.country}")
        run.font.size = Pt(8)
        run.font.italic = True
        run.font.color.rgb = _rgb(MUTED)

    _section_title(doc, "Personal Information", "المعلومات الشخصية")
    _info_table(doc, [
        ("Nationality", "الجنسية", "Ethiopian"),
        ("Religion", "الديانة", profile.religion),
        ("Date of Birth", "تاريخ الميلاد", applicant.date_of_birth.strftime("%d %b %Y") if applicant.date_of_birth else None),
        ("Place of Birth", "مكان الميلاد", profile.place_of_birth),
        ("Age", "العمر", profile.age()),
        ("Marital Status", "الحالة الاجتماعية", profile.marital_status),
        ("Weight / Height", "الوزن / الطول", f"{profile.weight_kg or '—'} kg / {profile.height_m or '—'} m"),
        ("Educational Qualification", "المؤهل العلمي", applicant.education_level),
    ])

    photos = doc.add_table(rows=1, cols=2)
    photos.alignment = WD_TABLE_ALIGNMENT.CENTER
    _set_widths(photos, (8.7, 8.7))
    _photo_cell(photos.cell(0, 0), full_doc.file_path if full_doc else None, "Full-Length Photo", 7.3, 8.4)
    _photo_cell(photos.cell(0, 1), passport_doc.file_path if passport_doc else None, "Passport Copy", 7.3, 8.4)
    _set_borders(photos, color=TEAL, size="8")

    _section_title(doc, "Passport Details", "بيانات جواز السفر")
    _info_table(doc, [
        ("Passport Number", "رقم الجواز", applicant.passport_number),
        ("Issue Place", "مكان الاصدار", profile.passport_issue_place),
        ("Issue Date", "تاريخ الاصدار", profile.passport_issue_date.strftime("%d/%m/%Y") if profile.passport_issue_date else None),
        ("Expiry Date", "تاريخ الانتهاء", profile.passport_expiry_date.strftime("%d/%m/%Y") if profile.passport_expiry_date else None),
    ])

    lang_map = {item["language"]: item["level"] for item in (profile.languages or [])}
    _ratings(doc, "Languages", "اللغات", CVProfile.DEFAULT_LANGUAGES, [lang_map.get(item, "none") for item in CVProfile.DEFAULT_LANGUAGES], {"none": 10, "fair": 40, "good": 70, "fluent": 100})
    skill_map = {item["skill"]: item["level"] for item in (profile.skills or [])}
    _ratings(doc, "Professional Skills", "المهارات المهنية", CVProfile.DEFAULT_SKILLS, [skill_map.get(item, "good") for item in CVProfile.DEFAULT_SKILLS], {"poor": 25, "fair": 50, "good": 75, "excellent": 100})

    if profile.work_history:
        _section_title(doc, "Work Experience", "الخبرة")
        history = doc.add_table(rows=1 + len(profile.work_history), cols=2)
        _set_widths(history, (8.7, 8.7))
        for cell, text in zip(history.rows[0].cells, ("PERIOD", "COUNTRY")):
            _shade_cell(cell, SOFT)
            _set_cell_text(cell, text, size=8, bold=True)
        for row, item in zip(history.rows[1:], profile.work_history):
            _set_cell_text(row.cells[0], item.get("period"), size=8.5)
            _set_cell_text(row.cells[1], item.get("country"), size=8.5)
        _set_borders(history)

    _section_title(doc, "Emergency Contact", "معلومات الطوارئ")
    _info_table(doc, [
        ("Full Name", "الاسم الكامل", profile.emergency_contact_name),
        ("Address", "العنوان", profile.emergency_contact_address),
        ("Telephone", "رقم الهاتف", profile.emergency_contact_phone),
    ])
    _footer(doc, company_name, company_phone, company_email, company_address_en, profile)

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer
