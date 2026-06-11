"""
Bid Compliance Report Generator
Reads the latest JSON analysis outputs and produces a professional Word document.

Usage:
    python generate_report.py
    python generate_report.py --timestamp 20260611_153155
    python generate_report.py --output my_report.docx
"""

import json
import argparse
from pathlib import Path
from datetime import datetime

from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

from config.settings import (
    METADATA_OUTPUT_DIR, COMPLIANCE_OUTPUT_DIR,
    OEM_OUTPUT_DIR, ENVELOPE_OUTPUT_DIR, OUTPUTS_DIR
)

# ─── Colour palette ──────────────────────────────────────────────────────────
CLR_HEADER_BG   = "1F3864"   # dark navy  – section headers
CLR_HEADER_FG   = "FFFFFF"   # white
CLR_MANDATORY   = "C00000"   # deep red
CLR_CONDITIONAL = "E36C09"   # orange
CLR_OPTIONAL    = "375623"   # dark green
CLR_ENV1_BG     = "D6E4F0"   # light blue  – envelope 1
CLR_ENV2_BG     = "FFF2CC"   # light amber – envelope 2
CLR_ROW_ALT     = "F2F2F2"   # light grey  – alternating rows
CLR_TABLE_HEADER= "2E4057"   # table column headers
CLR_BORDER      = "BFBFBF"

# ─── Helpers ─────────────────────────────────────────────────────────────────

def _set_cell_bg(cell, hex_color: str):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def _set_cell_borders(cell, color=CLR_BORDER):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement("w:tcBorders")
    for side in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)
        tcBorders.append(el)
    tcPr.append(tcBorders)


def _cell_para(cell, text: str, bold=False, italic=False,
               font_size=9, color=None, align=WD_ALIGN_PARAGRAPH.LEFT, wrap=True):
    para = cell.paragraphs[0]
    para.clear()
    para.alignment = align
    run = para.add_run(str(text) if text is not None else "—")
    run.bold = bold
    run.font.size = Pt(font_size)
    if color:
        run.font.color.rgb = RGBColor.from_string(color)
    if italic:
        run.italic = True
    return para


def _add_section_heading(doc: Document, title: str, level=1):
    """Coloured section heading bar."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(4)
    # shading on paragraph
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), CLR_HEADER_BG)
    pPr.append(shd)
    run = p.add_run(f"  {title}")
    run.bold = True
    run.font.color.rgb = RGBColor.from_string(CLR_HEADER_FG)
    run.font.size = Pt(12 if level == 1 else 10)
    return p


def _add_sub_heading(doc: Document, title: str):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run(title)
    run.bold = True
    run.font.size = Pt(10)
    run.font.color.rgb = RGBColor.from_string("2E4057")
    return p


def _category_color(cat: str) -> str:
    cat = (cat or "").upper()
    if "MANDATORY" in cat:
        return CLR_MANDATORY
    if "CONDITIONAL" in cat:
        return CLR_CONDITIONAL
    return CLR_OPTIONAL


def _latest_file(directory: Path) -> Path | None:
    files = sorted(directory.glob("*.json"))
    return files[-1] if files else None


def _load(directory: Path, timestamp: str | None) -> dict | None:
    if timestamp:
        matches = list(directory.glob(f"{timestamp}_*.json"))
        if matches:
            return json.loads(matches[0].read_text(encoding="utf-8"))
    f = _latest_file(directory)
    return json.loads(f.read_text(encoding="utf-8")) if f else None


# ─── Cover Page ──────────────────────────────────────────────────────────────

def _add_cover(doc: Document, metadata: dict):
    # Big title
    doc.add_paragraph()
    doc.add_paragraph()
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = title.add_run("BID COMPLIANCE ANALYSIS REPORT")
    r.bold = True
    r.font.size = Pt(22)
    r.font.color.rgb = RGBColor.from_string(CLR_HEADER_BG)

    doc.add_paragraph()
    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sr = sub.add_run("Procurement Agent for Bid Compliance Analyzer")
    sr.italic = True
    sr.font.size = Pt(12)
    sr.font.color.rgb = RGBColor.from_string("595959")

    doc.add_paragraph()
    doc.add_paragraph()

    # Key info box
    table = doc.add_table(rows=0, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"

    info_rows = [
        ("Project Name",       metadata.get("project_name") or "—"),
        ("Tender Reference",   metadata.get("tender_reference") or "—"),
        ("Procuring Entity",   metadata.get("procuring_entity") or "—"),
        ("Procurement Type",   metadata.get("procurement_type") or "—"),
        ("Submission Deadline",metadata.get("bid_submission_deadline") or "—"),
        ("Report Generated",   datetime.now().strftime("%d %B %Y")),
    ]

    for label, value in info_rows:
        row = table.add_row()
        row.height = Cm(0.75)
        _set_cell_bg(row.cells[0], "E8EEF4")
        _set_cell_borders(row.cells[0])
        _set_cell_borders(row.cells[1])
        _cell_para(row.cells[0], label, bold=True, font_size=10, color="1F3864")
        _cell_para(row.cells[1], value, font_size=10)

    doc.add_page_break()


# ─── Section 1: Tender Metadata ──────────────────────────────────────────────

def _add_metadata_section(doc: Document, metadata: dict):
    _add_section_heading(doc, "SECTION 1 — TENDER METADATA SHEET")

    field_labels = {
        "project_name":              "Project Name",
        "tender_reference":          "Tender Reference No.",
        "procuring_entity":          "Procuring Entity / Employer",
        "country":                   "Country",
        "project_location":          "Project Location",
        "procurement_method":        "Procurement Method",
        "procurement_type":          "Procurement Type",
        "funding_source":            "Funding Source",
        "loan_credit_number":        "Loan / Credit Number",
        "estimated_contract_value":  "Estimated Contract Value",
        "currency":                  "Currency",
        "bid_submission_deadline":   "Bid Submission Deadline",
        "bid_opening_date":          "Bid Opening Date",
        "bid_validity_period":       "Bid Validity Period",
        "performance_security":      "Performance Security",
        "advance_payment":           "Advance Payment",
        "contract_duration":         "Contract Duration",
        "bid_security_amount":       "Bid Security Amount",
        "pre_bid_meeting_date":      "Pre-Bid Meeting Date",
        "qualification_criteria_summary": "Qualification Criteria (Summary)",
        "contact_details":           "Contact Details",
        "document_issuance_date":    "Document Issuance Date",
        "lots":                      "Lot Structure",
    }

    table = doc.add_table(rows=0, cols=2)
    table.style = "Table Grid"

    # Header row
    hdr = table.add_row()
    _set_cell_bg(hdr.cells[0], CLR_TABLE_HEADER)
    _set_cell_bg(hdr.cells[1], CLR_TABLE_HEADER)
    _cell_para(hdr.cells[0], "Field", bold=True, font_size=9, color="FFFFFF")
    _cell_para(hdr.cells[1], "Value", bold=True, font_size=9, color="FFFFFF")

    for i, (key, label) in enumerate(field_labels.items()):
        value = metadata.get(key)
        if value is None:
            continue
        if isinstance(value, (list, dict)):
            value = json.dumps(value, indent=2)
        row = table.add_row()
        bg = CLR_ROW_ALT if i % 2 == 0 else "FFFFFF"
        _set_cell_bg(row.cells[0], "EEF2F7")
        _set_cell_bg(row.cells[1], bg)
        _set_cell_borders(row.cells[0])
        _set_cell_borders(row.cells[1])
        _cell_para(row.cells[0], label, bold=True, font_size=9)
        _cell_para(row.cells[1], value, font_size=9)

    doc.add_paragraph()
    doc.add_page_break()


# ─── Section 2: Compliance Checklist ─────────────────────────────────────────

def _add_compliance_section(doc: Document, compliance: dict):
    _add_section_heading(doc, "SECTION 2 — COMPLIANCE CHECKLIST")

    # Legend
    legend_para = doc.add_paragraph()
    legend_para.paragraph_format.space_before = Pt(4)
    legend_para.paragraph_format.space_after = Pt(6)
    for cat, clr, label in [
        ("M", CLR_MANDATORY,   "MANDATORY"),
        ("C", CLR_CONDITIONAL, "CONDITIONAL"),
        ("O", CLR_OPTIONAL,    "OPTIONAL"),
    ]:
        r = legend_para.add_run(f"  {label}  ")
        r.bold = True
        r.font.size = Pt(8)
        r.font.color.rgb = RGBColor.from_string("FFFFFF")
        # can't shade inline runs easily — add text label
    # Simple text legend
    legend_para.clear()
    for cat, clr, label in [
        ("■", CLR_MANDATORY,   " MANDATORY   "),
        ("■", CLR_CONDITIONAL, " CONDITIONAL   "),
        ("■", CLR_OPTIONAL,    " OPTIONAL"),
    ]:
        r = legend_para.add_run(cat)
        r.font.color.rgb = RGBColor.from_string(clr)
        r.font.size = Pt(10)
        r2 = legend_para.add_run(label)
        r2.font.size = Pt(9)
        r2.bold = True

    checklist = compliance.get("checklist", [])

    # Group by topic
    topics: dict[str, list] = {}
    for item in checklist:
        topic = item.get("topic", item.get("section_reference", "General"))
        if not isinstance(topic, str):
            topic = str(topic)
        # Try to get a clean group name
        for grp in ["Eligibility", "Financial", "Technical", "Legal",
                    "Bid Security", "Specifications", "Environmental",
                    "Administrative", "Submission"]:
            if grp.lower() in topic.lower():
                topic = grp
                break
        topics.setdefault(topic, []).append(item)

    # If no groups detected, put all in one group
    if not topics:
        topics["Requirements"] = checklist

    for topic_name, items in topics.items():
        _add_sub_heading(doc, topic_name)

        table = doc.add_table(rows=0, cols=5)
        table.style = "Table Grid"

        # Column headers
        hdr = table.add_row()
        for cell, text in zip(hdr.cells, ["ID", "Category", "Requirement", "Document Required", "Notes"]):
            _set_cell_bg(cell, CLR_TABLE_HEADER)
            _set_cell_borders(cell)
            _cell_para(cell, text, bold=True, font_size=8, color="FFFFFF",
                       align=WD_ALIGN_PARAGRAPH.CENTER)

        for i, item in enumerate(items):
            row = table.add_row()
            cat = str(item.get("category", "")).upper()
            cat_color = _category_color(cat)
            bg = CLR_ROW_ALT if i % 2 == 0 else "FFFFFF"

            cells = row.cells
            _set_cell_borders(cells[0]); _set_cell_bg(cells[0], bg)
            _set_cell_borders(cells[1])
            _set_cell_borders(cells[2]); _set_cell_bg(cells[2], bg)
            _set_cell_borders(cells[3]); _set_cell_bg(cells[3], bg)
            _set_cell_borders(cells[4]); _set_cell_bg(cells[4], bg)

            _cell_para(cells[0], item.get("requirement_id", ""),
                       bold=True, font_size=8, align=WD_ALIGN_PARAGRAPH.CENTER)
            # Category with colour
            _set_cell_bg(cells[1], cat_color)
            _cell_para(cells[1], cat, bold=True, font_size=7,
                       color="FFFFFF", align=WD_ALIGN_PARAGRAPH.CENTER)
            # Requirement text
            req_text = item.get("requirement", "")
            cond = item.get("condition", "")
            if cond:
                req_text += f"\n[Condition: {cond}]"
            _cell_para(cells[2], req_text, font_size=8)
            _cell_para(cells[3], item.get("document_required", "—"), font_size=8)
            _cell_para(cells[4], item.get("notes", "—"), font_size=8, italic=True)

        doc.add_paragraph()

    doc.add_page_break()


# ─── Section 3: OEM Checklist ─────────────────────────────────────────────────

def _add_oem_section(doc: Document, oem: dict):
    _add_section_heading(doc, "SECTION 3 — OEM DOCUMENT CHECKLIST")

    # Approved makes summary
    makes = oem.get("approved_makes", [])
    if makes:
        p = doc.add_paragraph()
        r = p.add_run("Approved Makes / Brands:  ")
        r.bold = True
        r.font.size = Pt(9)
        r2 = p.add_run(", ".join(str(m) for m in makes))
        r2.font.size = Pt(9)

    local_req = oem.get("local_agent_requirements", "")
    if local_req:
        p = doc.add_paragraph()
        r = p.add_run("Local Agent Requirements:  ")
        r.bold = True
        r.font.size = Pt(9)
        r2 = p.add_run(str(local_req))
        r2.font.size = Pt(9)

    single = oem.get("single_source_items", [])
    if single:
        p = doc.add_paragraph()
        r = p.add_run("Single-Source Items:  ")
        r.bold = True
        r.font.size = Pt(9)
        r2 = p.add_run(", ".join(str(s) for s in single))
        r2.font.size = Pt(9)
        r2.italic = True

    doc.add_paragraph()
    requirements = oem.get("oem_requirements", [])

    table = doc.add_table(rows=0, cols=6)
    table.style = "Table Grid"

    hdr = table.add_row()
    for cell, text in zip(hdr.cells, ["ID", "Equipment Item", "Requirement Type",
                                       "Document Required", "Issuing Party", "Mandatory"]):
        _set_cell_bg(cell, CLR_TABLE_HEADER)
        _set_cell_borders(cell)
        _cell_para(cell, text, bold=True, font_size=8, color="FFFFFF",
                   align=WD_ALIGN_PARAGRAPH.CENTER)

    for i, item in enumerate(requirements):
        row = table.add_row()
        bg = CLR_ROW_ALT if i % 2 == 0 else "FFFFFF"
        is_mandatory = str(item.get("mandatory", "")).lower() in ("true", "yes", "1")
        mand_bg = "FFE0E0" if is_mandatory else "FFFFFF"

        for cell in row.cells:
            _set_cell_borders(cell)
            _set_cell_bg(cell, bg)

        _cell_para(row.cells[0], item.get("item_id", ""),
                   bold=True, font_size=8, align=WD_ALIGN_PARAGRAPH.CENTER)
        _cell_para(row.cells[1], item.get("equipment_item", ""), bold=True, font_size=8)
        _cell_para(row.cells[2], item.get("oem_requirement_type", ""), font_size=8)
        _cell_para(row.cells[3], item.get("required_document", "—"), font_size=8)
        _cell_para(row.cells[4], item.get("issuing_party", "—"), font_size=8)
        _set_cell_bg(row.cells[5], "FFE0E0" if is_mandatory else "E8F5E9")
        _cell_para(row.cells[5], "YES" if is_mandatory else "No",
                   bold=is_mandatory, font_size=8,
                   color="C00000" if is_mandatory else "375623",
                   align=WD_ALIGN_PARAGRAPH.CENTER)

    doc.add_paragraph()
    doc.add_page_break()


# ─── Section 4: Envelope Contents ────────────────────────────────────────────

def _add_envelope_table(doc: Document, items: list, env_num: int, bg_color: str):
    if not items:
        doc.add_paragraph("No documents specified.")
        return

    table = doc.add_table(rows=0, cols=5)
    table.style = "Table Grid"

    hdr = table.add_row()
    hdr_bg = "1A5276" if env_num == 1 else "7D6608"
    for cell, text in zip(hdr.cells, ["ID", "Document Name", "Format / Copies", "Mandatory", "Notes"]):
        _set_cell_bg(cell, hdr_bg)
        _set_cell_borders(cell)
        _cell_para(cell, text, bold=True, font_size=8, color="FFFFFF",
                   align=WD_ALIGN_PARAGRAPH.CENTER)

    for i, doc_item in enumerate(items):
        row = table.add_row()
        bg = bg_color if i % 2 == 0 else "FFFFFF"
        is_mandatory = str(doc_item.get("mandatory", "")).lower() in ("true", "yes", "1")

        for cell in row.cells:
            _set_cell_borders(cell)
            _set_cell_bg(cell, bg)

        doc_id = doc_item.get("doc_id", str(i + 1))
        _cell_para(row.cells[0], doc_id, bold=True, font_size=8,
                   align=WD_ALIGN_PARAGRAPH.CENTER)
        _cell_para(row.cells[1], doc_item.get("document_name", "—"), bold=True, font_size=8)

        fmt = doc_item.get("format", "")
        copies = doc_item.get("copies_required", "")
        fmt_text = fmt
        if copies:
            fmt_text += f"\n{copies}"
        _cell_para(row.cells[2], fmt_text, font_size=8)

        _set_cell_bg(row.cells[3], "FFE0E0" if is_mandatory else "E8F5E9")
        _cell_para(row.cells[3], "YES" if is_mandatory else "No",
                   bold=is_mandatory, font_size=8,
                   color="C00000" if is_mandatory else "375623",
                   align=WD_ALIGN_PARAGRAPH.CENTER)

        _cell_para(row.cells[4], doc_item.get("notes", "—"), font_size=8, italic=True)


def _add_envelope_section(doc: Document, envelope: dict):
    _add_section_heading(doc, "SECTION 4 — ENVELOPE CONTENTS (ONE STAGE TWO ENVELOPE)")

    # Submission info
    for field, label in [
        ("submission_format", "Submission Format"),
        ("sealing_requirements", "Sealing Requirements"),
        ("outer_envelope_marking", "Outer Envelope Marking"),
    ]:
        val = envelope.get(field, "")
        if val:
            p = doc.add_paragraph()
            r = p.add_run(f"{label}:  ")
            r.bold = True
            r.font.size = Pt(9)
            r2 = p.add_run(str(val))
            r2.font.size = Pt(9)

    doc.add_paragraph()

    # Envelope 1 — Technical Bid
    mark1 = envelope.get("envelope_1_marking", "ENVELOPE 1 — TECHNICAL BID")
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    r = p.add_run(f"ENVELOPE 1 (TECHNICAL BID)   |   {mark1}")
    r.bold = True
    r.font.size = Pt(11)
    r.font.color.rgb = RGBColor.from_string("1A5276")

    caution = doc.add_paragraph()
    rc = caution.add_run("IMPORTANT: This envelope must contain ZERO pricing information.")
    rc.bold = True
    rc.font.color.rgb = RGBColor.from_string(CLR_MANDATORY)
    rc.font.size = Pt(9)

    _add_envelope_table(doc, envelope.get("envelope_1", []), 1, CLR_ENV1_BG)
    doc.add_paragraph()

    # Envelope 2 — Financial Bid
    mark2 = envelope.get("envelope_2_marking", "ENVELOPE 2 — FINANCIAL BID")
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    r = p.add_run(f"ENVELOPE 2 (FINANCIAL BID)   |   {mark2}")
    r.bold = True
    r.font.size = Pt(11)
    r.font.color.rgb = RGBColor.from_string("7D6608")

    _add_envelope_table(doc, envelope.get("envelope_2", []), 2, CLR_ENV2_BG)


# ─── Main ─────────────────────────────────────────────────────────────────────

def generate_report(timestamp: str | None = None, output_path: str | None = None) -> Path:
    print("[Report] Loading JSON outputs...")

    metadata   = _load(METADATA_OUTPUT_DIR,   timestamp) or {}
    compliance = _load(COMPLIANCE_OUTPUT_DIR, timestamp) or {}
    oem        = _load(OEM_OUTPUT_DIR,        timestamp) or {}
    envelope   = _load(ENVELOPE_OUTPUT_DIR,   timestamp) or {}

    print(f"  Metadata    : {len(metadata)} fields")
    print(f"  Compliance  : {len(compliance.get('checklist', []))} requirements")
    print(f"  OEM         : {len(oem.get('oem_requirements', []))} items")
    print(f"  Envelope 1  : {len(envelope.get('envelope_1', []))} docs")
    print(f"  Envelope 2  : {len(envelope.get('envelope_2', []))} docs")

    doc = Document()

    # Page margins (A4, 2.5cm margins)
    for section in doc.sections:
        section.top_margin    = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin   = Cm(2.5)
        section.right_margin  = Cm(2.5)

    # Default paragraph style
    style = doc.styles["Normal"]
    style.font.name = "Arial"
    style.font.size = Pt(9)

    print("[Report] Building document...")
    _add_cover(doc, metadata)
    _add_metadata_section(doc, metadata)
    _add_compliance_section(doc, compliance)
    _add_oem_section(doc, oem)
    _add_envelope_section(doc, envelope)

    # Determine output filename
    if output_path:
        out = Path(output_path)
    else:
        ts = timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
        project = (metadata.get("project_name") or "tender").replace(" ", "_")[:40]
        out = OUTPUTS_DIR / f"{ts}_BidComplianceReport_{project}.docx"

    doc.save(str(out))
    print(f"[Report] Saved -> {out}")
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Word compliance report from JSON outputs")
    parser.add_argument("--timestamp", "-t", help="Use specific run timestamp e.g. 20260611_153155")
    parser.add_argument("--output",    "-o", help="Output .docx path (optional)")
    args = parser.parse_args()

    path = generate_report(timestamp=args.timestamp, output_path=args.output)
    print(f"\nDone! Open the report:\n  {path}\n")
