#!/usr/bin/env python3
"""Fill unit prices on Villa Yasmina FF BOQ; rename Rate/Amount headers."""

from __future__ import annotations

from pathlib import Path

import pymupdf

SRC = Path("/home/ubuntu/.cursor/projects/workspace/uploads/Devis_villa_Yasmina_2_6796.pdf")
OUT = Path("/workspace/output/Devis_Villa_Yasmina_FF_Prix_v1.pdf")

FONT_REG = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
FONTNAME_REG = "liberationsans"
FONTNAME_BOLD = "liberationsans-bold"

HEADER_MAP = {
    "Rate": "Unit Price (HT)",
    "Amount": "Total Amount (HT)",
}

# (page_index, qty_y, qty, unit_price, is_m2)
# m² rows: Total Amount = same as Unit Price (no qty multiplication)
PRICES: list[tuple[int, float, float, float, bool]] = [
    # Page 4
    (3, 281.6, 2, 4500, False),    # F2 BED SIDE TABLE (TABLE-16)
    (3, 530.9, 1, 18000, False),   # F5 TV CONSOLE TABLE (CS-05)
    # Page 5
    (4, 306.7, 2, 4500, False),    # F2 BED SIDE TABLE (TB-15)
    (4, 393.2, 1, 9000, False),    # F3 SITTING (CH-11)
    (4, 558.0, 1, 12000, False),   # F5 CENTER TABLE (TB-13)
    (4, 619.3, 1, 6000, False),    # F6 SIDE TABLE (TB-17)
    # Page 6
    (5, 97.6, 1, 18000, False),    # F7 TV CONSOLE TABLE (CS-04)
    (5, 355.7, 1, 5000, False),    # F2 SIDE TABLE (TB-12)
    (5, 417.4, 1, 10000, False),   # F3 CONSOLE TABLE (CS-03)
    # Page 14
    (13, 176.6, 164, 220, False),  # FL1 To SKIRTING (WOOD)
    # Pages 17-21 vanities (M²)
    (16, 415.0, 1.1, 8250, True),  # WD1 VANITY 1
    (17, 415.0, 1.1, 9000, True),  # WD1 VANITY 2
    (18, 428.2, 1.1, 8250, True),  # WD1 VANITY 3
    (19, 427.4, 1.5, 11250, True), # WD1 VANITY 4
    (20, 427.4, 1.5, 11250, True), # WD1 VANITY 5
    # Page 22 drawers (M²)
    (21, 617.8, 1.7, 14250, True), # WD1 BUILT IN DRAWERS
    # Page 23 shelf (M²)
    (22, 106.4, 0.8, 12000, True), # WD3 WOOD VENEER SHELF (WD-02)
]


def fmt_money(value: float) -> str:
    if abs(value - round(value)) < 1e-6:
        return f"{int(round(value)):,}".replace(",", " ")
    return f"{value:,.2f}".replace(",", " ")


def int_color_to_rgb(color: int) -> tuple[float, float, float]:
    return (
        ((color >> 16) & 255) / 255,
        ((color >> 8) & 255) / 255,
        (color & 255) / 255,
    )


def sample_fill(pix: pymupdf.Pixmap, bbox: pymupdf.Rect) -> tuple[float, float, float]:
    x0, y0, x1, y1 = bbox
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    for sx, sy in ((cx, y0 - 1), (cx, y1 + 1), (x1 + 2, cy), (cx, cy)):
        ix = max(0, min(int(round(sx)), pix.width - 1))
        iy = max(0, min(int(round(sy)), pix.height - 1))
        p = pix.pixel(ix, iy)
        if len(p) >= 3 and (0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2]) > 80:
            return (p[0] / 255, p[1] / 255, p[2] / 255)
    return (1, 1, 1)


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


def column_cells(page: pymupdf.Page) -> tuple[tuple[float, float], tuple[float, float]]:
    """Return expanded Unit Price / Total Amount column bounds."""
    xs, _ = page_grid(page)
    rate = amount = None
    for block in page.get_text("dict")["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                t = span["text"].strip()
                if t == "Rate":
                    rate = span["bbox"]
                elif t == "Amount":
                    amount = span["bbox"]
    candidates = [x for x in xs if x > 350]
    if len(candidates) >= 3 and rate and amount:
        def bounds(cx: float) -> tuple[float, float]:
            left = max((x for x in candidates if x < cx), default=cx - 25)
            right = min((x for x in candidates if x > cx), default=cx + 25)
            return left, right

        rate_b = bounds((rate[0] + rate[2]) / 2)
        amt_b = bounds((amount[0] + amount[2]) / 2)
    else:
        rate_b, amt_b = (463.6, 501.8), (501.8, 546.8)

    # Enlarge columns: steal a bit from Unit, extend Total Amount into right margin
    left_expand = 14.0
    right_expand = 28.0
    mid_shift = 8.0  # give a bit more width to Unit Price
    new_rate_x0 = rate_b[0] - left_expand
    new_amt_x1 = min(page.rect.width - 14.0, amt_b[1] + right_expand)
    mid = ((rate_b[1] + amt_b[0]) / 2) + mid_shift
    # Keep mid between the new edges
    mid = min(max(mid, new_rate_x0 + 42), new_amt_x1 - 48)
    return (new_rate_x0, mid), (mid, new_amt_x1)


def widen_price_column_strip(page: pymupdf.Page, rate_x: tuple[float, float], amt_x: tuple[float, float]) -> None:
    """Visually enlarge Unit Price + Total Amount columns and redraw grid."""
    xs, ys = page_grid(page)
    table_ys = [y for y in ys if 50 < y < 750]
    if len(table_ys) < 2:
        return
    y_top, y_bot = min(table_ys), max(table_ys)
    x0, x1 = rate_x[0], amt_x[1]
    mid = rate_x[1]

    # Cover old price columns (+ a little overlap) with white
    page.draw_rect(
        pymupdf.Rect(x0 - 0.4, y_top - 0.4, x1 + 0.4, y_bot + 0.4),
        color=None,
        fill=(1, 1, 1),
        width=0,
    )

    # Outer verticals + divider
    for x in (x0, mid, x1):
        page.draw_line(pymupdf.Point(x, y_top), pymupdf.Point(x, y_bot), color=(0, 0, 0), width=0.7)
    # Horizontal lines across widened strip
    for y in table_ys:
        page.draw_line(pymupdf.Point(x0, y), pymupdf.Point(x1, y), color=(0, 0, 0), width=0.6)


def row_bounds(page: pymupdf.Page, qty_y: float) -> tuple[float, float]:
    _, ys = page_grid(page)
    y_ref = qty_y + 5
    above = [y for y in ys if y < y_ref - 1]
    below = [y for y in ys if y > y_ref + 1]
    y0 = max(above) if above else qty_y - 8
    y1 = min(below) if below else qty_y + 20
    if y1 - y0 > 90:
        y0 = max(y0, qty_y - 12)
        y1 = min(y1, qty_y + 28)
    return y0, y1


def centered_insert(page: pymupdf.Page, text: str, cell: pymupdf.Rect, fontsize: float = 8.5) -> None:
    font = pymupdf.Font(fontfile=FONT_REG)
    pad = 2.0
    max_w = max(cell.width - 2 * pad, 8)
    size = fontsize
    tw = font.text_length(text, fontsize=size)
    if tw > max_w:
        size = max(5.5, size * max_w / tw)
        tw = font.text_length(text, fontsize=size)
    x = cell.x0 + (cell.width - tw) / 2
    y = cell.y0 + (cell.height + size * 0.72) / 2
    page.insert_text(
        pymupdf.Point(x, y),
        text,
        fontname=FONTNAME_REG,
        fontsize=size,
        color=(0, 0, 0),
    )


def process(src: Path, out: Path) -> None:
    doc = pymupdf.open(src)
    header_jobs: list[tuple[int, dict]] = []
    price_by_page: dict[int, list[tuple[float, float, float, bool]]] = {}
    for pi, qty_y, qty, rate, is_m2 in PRICES:
        price_by_page.setdefault(pi, []).append((qty_y, qty, rate, is_m2))

    for pi, page in enumerate(doc):
        pix = page.get_pixmap(matrix=pymupdf.Identity, alpha=False)
        for block in page.get_text("dict")["blocks"]:
            if block.get("type") != 0:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    t = span["text"]
                    if t not in HEADER_MAP:
                        continue
                    orig = pymupdf.Rect(span["bbox"])
                    header_jobs.append(
                        (
                            pi,
                            {
                                "kind": t,
                                "orig_bbox": orig,
                                "text": HEADER_MAP[t],
                                "size": span["size"],
                                "color": int_color_to_rgb(span["color"]),
                                "fill": sample_fill(pix, orig),
                                "bold": "Bold" in span["font"],
                            },
                        )
                    )

    for pi, page in enumerate(doc):
        page.insert_font(fontname=FONTNAME_REG, fontfile=FONT_REG)
        page.insert_font(fontname=FONTNAME_BOLD, fontfile=FONT_BOLD)
        rate_cell_x, amt_cell_x = column_cells(page)

        page_headers = [j for p, j in header_jobs if p == pi]

        # Redact old Rate/Amount labels first
        for job in page_headers:
            page.add_redact_annot(job["orig_bbox"], fill=(1, 1, 1), cross_out=False)
        if page_headers:
            page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)
            page.insert_font(fontname=FONTNAME_REG, fontfile=FONT_REG)
            page.insert_font(fontname=FONTNAME_BOLD, fontfile=FONT_BOLD)

        # Enlarge Unit Price / Total Amount columns visually on pages that have them
        if page_headers:
            widen_price_column_strip(page, rate_cell_x, amt_cell_x)

        _, ys = page_grid(page)
        header_ys = [y for y in ys if 50 < y < 110]
        for job in page_headers:
            if job["kind"] == "Rate":
                cell = pymupdf.Rect(rate_cell_x[0], 54.0, rate_cell_x[1], 79.7)
            else:
                cell = pymupdf.Rect(amt_cell_x[0], 54.0, amt_cell_x[1], 79.7)
            if len(header_ys) >= 2:
                cell.y0, cell.y1 = header_ys[0], header_ys[1]

            fontname = FONTNAME_BOLD if job["bold"] else FONTNAME_REG
            fontfile = FONT_BOLD if job["bold"] else FONT_REG
            font = pymupdf.Font(fontfile=fontfile)
            if job["kind"] == "Rate":
                lines = ["Unit Price", "(HT)"]
            else:
                lines = ["Total Amount", "(HT)"]
            size = 7.0
            max_w = max(cell.width - 3, 8)
            while size > 5.0:
                if max(font.text_length(ln, fontsize=size) for ln in lines) <= max_w:
                    break
                size -= 0.25
            # If still too wide, split first line
            if font.text_length(lines[0], fontsize=size) > max_w:
                if job["kind"] == "Rate":
                    lines = ["Unit", "Price", "(HT)"]
                else:
                    lines = ["Total", "Amount", "(HT)"]
                size = 6.2
                while size > 5.0:
                    if max(font.text_length(ln, fontsize=size) for ln in lines) <= max_w:
                        break
                    size -= 0.2
            line_h = size * 1.08
            block_h = line_h * len(lines)
            y_start = cell.y0 + (cell.height - block_h) / 2 + size * 0.8
            for i, ln in enumerate(lines):
                tw = font.text_length(ln, fontsize=size)
                x = cell.x0 + (cell.width - tw) / 2
                page.insert_text(
                    pymupdf.Point(x, y_start + i * line_h),
                    ln,
                    fontname=fontname,
                    fontsize=size,
                    color=job["color"],
                )

        # Fill only priced rows (HT stays in headers only)
        if pi not in price_by_page:
            continue
        for qty_y, qty, rate, is_m2 in price_by_page[pi]:
            y0, y1 = row_bounds(page, qty_y)
            rate_rect = pymupdf.Rect(rate_cell_x[0], y0, rate_cell_x[1], y1)
            amt_rect = pymupdf.Rect(amt_cell_x[0], y0, amt_cell_x[1], y1)
            centered_insert(page, fmt_money(rate), rate_rect)
            total = rate if is_m2 else qty * rate
            centered_insert(page, fmt_money(total), amt_rect)

    out.parent.mkdir(parents=True, exist_ok=True)
    doc.set_metadata(
        {
            "title": "VILLA YASMINA FF BOQ - Unit Prices",
            "subject": "Wider Unit Price/Total Amount columns; HT in headers only",
            "creator": "fill_ff_devis_prices.py",
        }
    )
    doc.save(out, garbage=4, deflate=True)
    doc.close()
    print(f"Wrote {out}")
    for pi, qty_y, qty, rate, is_m2 in PRICES:
        if is_m2:
            print(f"  p{pi+1}: m2 @ {rate} → total={rate}")
        else:
            print(f"  p{pi+1}: qty={qty} @ {rate} → total={qty * rate:g}")


if __name__ == "__main__":
    process(SRC, OUT)
