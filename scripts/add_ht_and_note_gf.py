#!/usr/bin/env python3
"""Add HT to Unit Price / Total Amount headers only; bold centered note on last page."""

from __future__ import annotations

from pathlib import Path

import pymupdf

SRC = Path("/home/ubuntu/.cursor/projects/workspace/uploads/Devis_Villa_Yasmina_Prix_1_eacd.pdf")
OUT = Path("/workspace/output/Devis_Villa_Yasmina_Prix_HT_Note.pdf")

FONT_REG = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
FONTNAME_REG = "liberationsans"
FONTNAME_BOLD = "liberationsans-bold"

NOTE = "NB: The wood used is solid wood."


def page_grid(page: pymupdf.Page) -> tuple[list[float], list[float]]:
    xs: set[float] = set()
    ys: set[float] = set()
    for d in page.get_drawings():
        r = d.get("rect")
        if not r:
            continue
        if abs(r.x1 - r.x0) < 1.5:
            xs.add(round(float(r.x0), 1))
        if abs(r.y1 - r.y0) < 1.5:
            ys.add(round(float(r.y0), 1))
    return sorted(xs), sorted(ys)


def header_spans(page: pymupdf.Page) -> list[dict]:
    spans: list[dict] = []
    for block in page.get_text("dict")["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                t = span["text"].strip()
                x0, y0, _, _ = span["bbox"]
                if y0 > 95:
                    continue
                if t in ("Unit", "Price", "Total", "Amount", "(HT)"):
                    spans.append(span)
    return spans


def column_cell(page: pymupdf.Page, spans: list[dict], candidates: list[float]) -> pymupdf.Rect | None:
    if not spans:
        return None
    cx = sum((s["bbox"][0] + s["bbox"][2]) / 2 for s in spans) / len(spans)
    left = max((x for x in candidates if x < cx - 0.5), default=cx - 25)
    right = min((x for x in candidates if x > cx + 0.5), default=cx + 25)
    _, ys = page_grid(page)
    header_ys = [y for y in ys if 50 < y < 115]
    if len(header_ys) >= 2:
        y0, y1 = header_ys[0], header_ys[1]
    else:
        y0 = min(s["bbox"][1] for s in spans) - 2
        y1 = max(s["bbox"][3] for s in spans) + 2
    return pymupdf.Rect(left, y0, right, y1)


def write_header(page: pymupdf.Page, cell: pymupdf.Rect, lines: list[str]) -> None:
    font = pymupdf.Font(fontfile=FONT_BOLD)
    size = 7.0
    max_w = max(cell.width - 3, 8)
    while size > 5.0:
        if max(font.text_length(ln, fontsize=size) for ln in lines) <= max_w:
            break
        size -= 0.25
    line_h = size * 1.08
    block_h = line_h * len(lines)
    y_start = cell.y0 + (cell.height - block_h) / 2 + size * 0.8
    for i, ln in enumerate(lines):
        tw = font.text_length(ln, fontsize=size)
        x = cell.x0 + (cell.width - tw) / 2
        page.insert_text(
            pymupdf.Point(x, y_start + i * line_h),
            ln,
            fontname=FONTNAME_BOLD,
            fontsize=size,
            color=(0, 0, 0),
        )


def add_ht_headers(page: pymupdf.Page) -> bool:
    spans = header_spans(page)
    if any(s["text"].strip() == "(HT)" for s in spans):
        return False

    price_anchor = next((s for s in spans if s["text"].strip() == "Price"), None)
    amount_anchor = next((s for s in spans if s["text"].strip() == "Amount"), None)
    if not price_anchor and not amount_anchor:
        return False

    xs, _ = page_grid(page)
    # Include slightly lower threshold for pages with narrower tables (e.g. page 2)
    candidates = [x for x in xs if x > 300]

    def near(anchor: dict, labels: set[str]) -> list[dict]:
        ax = (anchor["bbox"][0] + anchor["bbox"][2]) / 2
        out = []
        for s in spans:
            t = s["text"].strip()
            if t not in labels:
                continue
            sx = (s["bbox"][0] + s["bbox"][2]) / 2
            if abs(sx - ax) < 30:
                out.append(s)
        return out

    jobs: list[tuple[list[dict], pymupdf.Rect, list[str]]] = []
    if price_anchor:
        group = near(price_anchor, {"Unit", "Price"})
        cell = column_cell(page, group or [price_anchor], candidates)
        if cell:
            jobs.append((group or [price_anchor], cell, ["Unit", "Price", "(HT)"]))
    if amount_anchor:
        group = near(amount_anchor, {"Total", "Amount"})
        cell = column_cell(page, group or [amount_anchor], candidates)
        if cell:
            jobs.append((group or [amount_anchor], cell, ["Total", "Amount", "(HT)"]))

    if not jobs:
        return False

    for group, _, _ in jobs:
        for span in group:
            page.add_redact_annot(pymupdf.Rect(span["bbox"]), fill=(1, 1, 1), cross_out=False)
    page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)
    page.insert_font(fontname=FONTNAME_REG, fontfile=FONT_REG)
    page.insert_font(fontname=FONTNAME_BOLD, fontfile=FONT_BOLD)

    for _, cell, lines in jobs:
        write_header(page, cell, lines)
    return True


def add_last_page_note(page: pymupdf.Page) -> None:
    page.insert_font(fontname=FONTNAME_BOLD, fontfile=FONT_BOLD)
    font = pymupdf.Font(fontfile=FONT_BOLD)
    size = 11.0
    tw = font.text_length(NOTE, fontsize=size)
    x = (page.rect.width - tw) / 2
    # Just below last table border on page 23 (table ends ~y 234)
    y = 260.0
    page.insert_text(
        pymupdf.Point(x, y),
        NOTE,
        fontname=FONTNAME_BOLD,
        fontsize=size,
        color=(0, 0, 0),
    )


def process(src: Path, out: Path) -> None:
    doc = pymupdf.open(src)
    updated = 0
    for page in doc:
        page.insert_font(fontname=FONTNAME_REG, fontfile=FONT_REG)
        page.insert_font(fontname=FONTNAME_BOLD, fontfile=FONT_BOLD)
        if add_ht_headers(page):
            updated += 1

    add_last_page_note(doc[-1])

    out.parent.mkdir(parents=True, exist_ok=True)
    doc.set_metadata(
        {
            "title": "VILLA YASMINA - Unit Prices HT",
            "subject": "HT in Unit Price / Total Amount headers; solid wood note on last page",
            "creator": "add_ht_and_note_gf.py",
        }
    )
    doc.save(out, garbage=4, deflate=True)
    doc.close()
    print(f"Wrote {out}")
    print(f"  pages with HT headers updated: {updated}")
    print(f"  last-page note (bold, centered): {NOTE}")


if __name__ == "__main__":
    process(SRC, OUT)
