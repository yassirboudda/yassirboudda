#!/usr/bin/env python3
"""Fill unit prices / totals on Villa Yasmina GF BOQ and rename Rate/Amount headers."""

from __future__ import annotations

from pathlib import Path

import pymupdf

SRC = Path("/home/ubuntu/.cursor/projects/workspace/uploads/Devis_villa_Yasmina_57b3.pdf")
OUT = Path("/workspace/output/Devis_Villa_Yasmina_Prix_Unitaires.pdf")

FONT_REG = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
FONTNAME_REG = "liberationsans"
FONTNAME_BOLD = "liberationsans-bold"

HEADER_MAP = {
    "Rate": "Unit Price",
    "Amount": "Total Amount",
}

# (page_index, qty_y, qty, unit_price, is_m2)
# For m² rows: only Unit Price is written (no Total Amount multiplication).
PRICES: list[tuple[int, float, float, float, bool]] = [
    # Page 4
    (3, 463.4, 1, 11230, False),   # F2 TABLE-05
    (3, 528.0, 1, 3500, False),    # F3 TABLE-04
    (3, 595.9, 2, 5500, False),    # F4 TABLE-03 pedestal
    (3, 665.2, 1, 18000, False),   # F4 TABLE-03 TV cabinet
    # Page 5
    (4, 634.6, 1, 4000, False),    # F3 TABLE-11
    # Page 7
    (6, 183.0, 8, 3500, False),    # F5 TABLE-06
    (6, 258.1, 2, 9000, False),    # F6 TABLE
    (6, 328.9, 1, 19000, False),   # F7 TABLE-08
    (6, 395.5, 1, 23000, False),   # F8 TABLE-07
    (6, 456.2, 1, 18000, False),   # F9 CONSOLE-06
    (6, 613.8, 1, 31000, False),   # F11 CONSOLE
    # Page 8
    (7, 387.0, 1, 17000, False),   # F3 TABLE-09
    (7, 453.6, 2, 7000, False),    # F4 TABLE
    (7, 518.5, 1, 11250, False),   # F5 TABLE-14
    # Page 9
    (8, 287.5, 1, 19000, False),   # F8 CONSOLE-02
    # Page 17 — LM, multiply
    (16, 170.3, 71, 220, False),   # FL1 plinthes
    # Page 20
    (19, 252.5, 2, 31000, False),  # WD1 console (NO)
    (19, 335.9, 1, 27000, False),  # WD2 dining table (NO)
    (19, 651.0, 5, 25000, True),   # WD2 vanity (M²) — unit only
    # Page 21
    (20, 165.7, 10, 21000, True),  # WD-1 shelves (M²) — unit only
    (20, 389.2, 1, 18000, False),  # WD1 coiffeuse (NO)
    (20, 471.6, 1.2, 9000, True),  # WD2 shelves (M²) — unit only
    # Page 22
    (21, 639.6, 4.7, 42120, True), # WD2 cabinets (M2) — unit only
    # Page 23
    (22, 106.4, 3.1, 27720, True), # WD3 cabinets (M2) — unit only
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
    """Collect thin vertical/horizontal grid lines from drawings."""
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
    """Return ((rate_x0, rate_x1), (amount_x0, amount_x1)) from vertical grid."""
    xs, _ = page_grid(page)
    # Prefer grid lines near the Rate/Amount headers
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
    candidates = [x for x in xs if x > 380]
    if len(candidates) >= 3 and rate and amount:
        # Find lines surrounding each header center
        def bounds(cx: float) -> tuple[float, float]:
            left = max((x for x in candidates if x < cx), default=cx - 25)
            right = min((x for x in candidates if x > cx), default=cx + 25)
            return left, right

        rate_cell = bounds((rate[0] + rate[2]) / 2)
        amt_cell = bounds((amount[0] + amount[2]) / 2)
        return rate_cell, amt_cell
    # Fallback furniture layout
    return (463.6, 501.8), (501.8, 546.8)


def row_bounds(page: pymupdf.Page, qty_y: float) -> tuple[float, float]:
    """Find horizontal grid lines surrounding the qty row."""
    _, ys = page_grid(page)
    # qty_y is top of qty glyph bbox; use mid of glyph ~ qty_y+5
    y_ref = qty_y + 5
    above = [y for y in ys if y < y_ref - 1]
    below = [y for y in ys if y > y_ref + 1]
    y0 = max(above) if above else qty_y - 8
    y1 = min(below) if below else qty_y + 20
    # Avoid huge merged rows: clamp to a reasonable cell height
    if y1 - y0 > 90:
        y0 = max(y0, qty_y - 12)
        y1 = min(y1, qty_y + 28)
    return y0, y1


def centered_insert(
    page: pymupdf.Page,
    text: str,
    cell: pymupdf.Rect,
    fontsize: float = 9.0,
) -> None:
    """Insert text centered horizontally and vertically inside cell."""
    font = pymupdf.Font(fontfile=FONT_REG)
    # Shrink to fit width with padding
    pad = 2.0
    max_w = max(cell.width - 2 * pad, 8)
    size = fontsize
    tw = font.text_length(text, fontsize=size)
    if tw > max_w:
        size = max(6.0, size * max_w / tw)
        tw = font.text_length(text, fontsize=size)
    # Approximate glyph height ~ size; baseline centered in cell
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
                                "origin": span.get("origin", (orig.x0, orig.y1 - 1)),
                                "bold": "Bold" in span["font"],
                            },
                        )
                    )

    for pi, page in enumerate(doc):
        page.insert_font(fontname=FONTNAME_REG, fontfile=FONT_REG)
        page.insert_font(fontname=FONTNAME_BOLD, fontfile=FONT_BOLD)

        rate_cell_x, amt_cell_x = column_cells(page)

        page_headers = [j for p, j in header_jobs if p == pi]
        # Redact original Rate/Amount glyphs only (tight bbox), then rewrite centered in columns
        for job in page_headers:
            page.add_redact_annot(job["orig_bbox"], fill=job["fill"], cross_out=False)
        if page_headers:
            page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)
            page.insert_font(fontname=FONTNAME_REG, fontfile=FONT_REG)
            page.insert_font(fontname=FONTNAME_BOLD, fontfile=FONT_BOLD)

        for job in page_headers:
            if job["kind"] == "Rate":
                cell = pymupdf.Rect(rate_cell_x[0], 54.0, rate_cell_x[1], 79.7)
            else:
                cell = pymupdf.Rect(amt_cell_x[0], 54.0, amt_cell_x[1], 79.7)
            # Use full header row height from grid when available
            _, ys = page_grid(page)
            header_ys = [y for y in ys if 50 < y < 110]
            if len(header_ys) >= 2:
                cell.y0, cell.y1 = header_ys[0], header_ys[1]

            fontname = FONTNAME_BOLD if job["bold"] else FONTNAME_REG
            fontfile = FONT_BOLD if job["bold"] else FONT_REG
            font = pymupdf.Font(fontfile=fontfile)

            # Prefer 2-line header so it stays inside the column cell
            words = job["text"].split(" ")
            if len(words) >= 2:
                lines = [" ".join(words[:-1]), words[-1]]
            else:
                lines = [job["text"]]
            size = 7.2
            max_w = max(cell.width - 3, 8)
            while size > 5.2:
                widths = [font.text_length(ln, fontsize=size) for ln in lines]
                if max(widths) <= max_w:
                    break
                size -= 0.3
            line_h = size * 1.15
            block_h = line_h * len(lines)
            y_start = cell.y0 + (cell.height - block_h) / 2 + size * 0.85
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

        if pi not in price_by_page:
            continue

        for qty_y, qty, rate, is_m2 in price_by_page[pi]:
            y0, y1 = row_bounds(page, qty_y)
            rate_rect = pymupdf.Rect(rate_cell_x[0], y0, rate_cell_x[1], y1)
            amt_rect = pymupdf.Rect(amt_cell_x[0], y0, amt_cell_x[1], y1)

            centered_insert(page, fmt_money(rate), rate_rect, fontsize=9.0)
            if not is_m2:
                centered_insert(page, fmt_money(qty * rate), amt_rect, fontsize=9.0)

    out.parent.mkdir(parents=True, exist_ok=True)
    doc.set_metadata(
        {
            "title": "VILLA YASMINA GF BOQ - Unit Prices",
            "subject": "Centered Unit Price / Total Amount; m² rows unit-only",
            "creator": "fill_devis_prices.py",
        }
    )
    doc.save(out, garbage=4, deflate=True)
    doc.close()
    print(f"Wrote {out}")
    for pi, qty_y, qty, rate, is_m2 in PRICES:
        if is_m2:
            print(f"  p{pi+1}: qty={qty} m2 @ {rate} → unit only")
        else:
            print(f"  p{pi+1}: qty={qty} @ {rate} → total {qty * rate:g}")


if __name__ == "__main__":
    process(SRC, OUT)
