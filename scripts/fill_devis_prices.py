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

# Header replacements (exact span text)
HEADER_MAP = {
    "Rate": "Unit Price",
    "Amount": "Total Amount",
}

# Priced rows: (page_index_0based, qty_y, qty, unit_price)
# qty_y = baseline y of the Qty cell used to align Rate/Amount
PRICES: list[tuple[int, float, float, float]] = [
    # Page 4
    (3, 463.4, 1, 11230),   # F2 TABLE-05
    (3, 528.0, 1, 3500),    # F3 TABLE-04
    (3, 595.9, 2, 5500),    # F4 TABLE-03 pedestal
    (3, 665.2, 1, 18000),   # F4 TABLE-03 TV cabinet
    # Page 5
    (4, 634.6, 1, 4000),    # F3 TABLE-11
    # Page 7
    (6, 183.0, 8, 3500),    # F5 TABLE-06
    (6, 258.1, 2, 9000),    # F6 TABLE
    (6, 328.9, 1, 19000),   # F7 TABLE-08
    (6, 395.5, 1, 23000),   # F8 TABLE-07
    (6, 456.2, 1, 18000),   # F9 CONSOLE-06
    (6, 613.8, 1, 31000),   # F11 CONSOLE
    # Page 8
    (7, 387.0, 1, 17000),   # F3 TABLE-09
    (7, 453.6, 2, 7000),    # F4 TABLE
    (7, 518.5, 1, 11250),   # F5 TABLE-14
    # Page 9
    (8, 287.5, 1, 19000),   # F8 CONSOLE-02
    # Page 17
    (16, 170.3, 71, 220),   # FL1 skirting / plinthes
    # Page 20
    (19, 252.5, 2, 31000),  # WD1 wood veneer console
    (19, 335.9, 1, 27000),  # WD2 dining table
    (19, 651.0, 5, 25000),  # WD2 vanity counter
    # Page 21
    (20, 165.7, 10, 21000),     # WD-1 shelves
    (20, 389.2, 1, 18000),      # WD1 dresser / coiffeuse
    (20, 471.6, 1.2, 9000),     # WD2 wood veneer shelves
    # Page 22
    (21, 639.6, 4.7, 42120),    # WD2 wood cabinets
    # Page 23
    (22, 106.4, 3.1, 27720),    # WD3 wood cabinets
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


def column_x_for_page(page: pymupdf.Page) -> tuple[float, float, float, float]:
    """Return (rate_x0, rate_x1, amount_x0, amount_x1) from headers."""
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
    if not rate or not amount:
        # furniture default
        return 455.0, 505.0, 505.0, 560.0
    # Expand columns between unit and page edge
    rate_x0 = rate[0] - 8
    amount_x1 = min(page.rect.width - 20, amount[2] + 20)
    mid = (rate[2] + amount[0]) / 2
    return rate_x0, mid, mid, amount_x1


def process(src: Path, out: Path) -> None:
    doc = pymupdf.open(src)
    header_jobs: list[tuple[int, dict]] = []
    price_by_page: dict[int, list[tuple[float, float, float]]] = {}
    for pi, qty_y, qty, rate in PRICES:
        price_by_page.setdefault(pi, []).append((qty_y, qty, rate))

    # 1) Collect header replacements
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
                    bbox = pymupdf.Rect(span["bbox"])
                    # Widen a bit so longer header fits visually after rewrite
                    if t == "Rate":
                        bbox.x1 = max(bbox.x1, bbox.x0 + 55)
                    else:
                        bbox.x1 = max(bbox.x1, bbox.x0 + 70)
                        bbox.x0 = min(bbox.x0, bbox.x1 - 70)
                    header_jobs.append(
                        (
                            pi,
                            {
                                "bbox": bbox,
                                "text": HEADER_MAP[t],
                                "size": span["size"],
                                "color": int_color_to_rgb(span["color"]),
                                "fill": sample_fill(pix, pymupdf.Rect(span["bbox"])),
                                "origin": span.get("origin", (bbox.x0, bbox.y1 - 1)),
                                "bold": "Bold" in span["font"],
                            },
                        )
                    )

    # Apply header redactions page by page, then insert prices
    for pi, page in enumerate(doc):
        page.insert_font(fontname=FONTNAME_REG, fontfile=FONT_REG)
        page.insert_font(fontname=FONTNAME_BOLD, fontfile=FONT_BOLD)

        # Capture column geometry before headers are rewritten
        rate_x0, rate_x1, amt_x0, amt_x1 = column_x_for_page(page)

        page_headers = [j for p, j in header_jobs if p == pi]
        for job in page_headers:
            page.add_redact_annot(job["bbox"], fill=job["fill"], cross_out=False)
        if page_headers:
            page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)
            page.insert_font(fontname=FONTNAME_REG, fontfile=FONT_REG)
            page.insert_font(fontname=FONTNAME_BOLD, fontfile=FONT_BOLD)

        for job in page_headers:
            fontname = FONTNAME_BOLD if job["bold"] else FONTNAME_REG
            size = job["size"]
            # Shrink if needed
            font = pymupdf.Font(fontfile=FONT_BOLD if job["bold"] else FONT_REG)
            tw = font.text_length(job["text"], fontsize=size)
            if tw > job["bbox"].width:
                size = max(6.0, size * job["bbox"].width / tw * 0.96)
            x, y = job["origin"]
            page.insert_text(
                pymupdf.Point(x, y),
                job["text"],
                fontname=fontname,
                fontsize=size,
                color=job["color"],
            )

        # Insert unit prices + totals
        if pi not in price_by_page:
            continue
        fontsize = 9.0
        for qty_y, qty, rate in price_by_page[pi]:
            total = qty * rate
            # Align with qty baseline
            baseline = qty_y + 9.5  # approx glyph baseline from bbox top
            # Prefer matching nearby qty span baseline if possible
            for block in page.get_text("dict")["blocks"]:
                if block.get("type") != 0:
                    continue
                for line in block["lines"]:
                    for span in line["spans"]:
                        if abs(span["bbox"][1] - qty_y) < 0.6 and span["bbox"][0] > 370:
                            baseline = span.get("origin", (0, span["bbox"][1] + 9))[1]
                            fontsize = min(span["size"], 9.5)
                            break

            rate_str = fmt_money(rate)
            total_str = fmt_money(total)

            # Right-align within columns
            font = pymupdf.Font(fontfile=FONT_REG)
            rw = font.text_length(rate_str, fontsize=fontsize)
            tw = font.text_length(total_str, fontsize=fontsize)
            rate_x = max(rate_x0 + 2, rate_x1 - rw - 4)
            amt_x = max(amt_x0 + 2, amt_x1 - tw - 4)

            page.insert_text(
                pymupdf.Point(rate_x, baseline),
                rate_str,
                fontname=FONTNAME_REG,
                fontsize=fontsize,
                color=(0, 0, 0),
            )
            page.insert_text(
                pymupdf.Point(amt_x, baseline),
                total_str,
                fontname=FONTNAME_REG,
                fontsize=fontsize,
                color=(0, 0, 0),
            )

    out.parent.mkdir(parents=True, exist_ok=True)
    doc.set_metadata(
        {
            "title": "VILLA YASMINA GF BOQ - Unit Prices",
            "subject": "Rate→Unit Price, Amount→Total Amount + filled prices",
            "creator": "fill_devis_prices.py",
        }
    )
    doc.save(out, garbage=4, deflate=True)
    doc.close()
    print(f"Wrote {out}")
    print(f"Headers replaced on all pages; priced rows: {len(PRICES)}")
    for pi, qty_y, qty, rate in PRICES:
        print(f"  p{pi+1}: qty={qty} @ {rate} → total {qty*rate:g}")


if __name__ == "__main__":
    process(SRC, OUT)
