from __future__ import annotations
from typing import List, Tuple
import numpy as np
from PIL import Image
import cv2
import pytesseract
import pandas as pd

# NOTE: ensure tesseract is installed system-wide and pytesseract can find it.
# Optionally: pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"


def _binarize(img_gray: np.ndarray) -> np.ndarray:
    """Adaptive thresholding for robust binarization."""
    # Slight blur to reduce noise, then adaptive threshold
    blur = cv2.GaussianBlur(img_gray, (3, 3), 0)
    thr = cv2.adaptiveThreshold(
        blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 17, 8
    )
    return thr


def _detect_grid(thr: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Detect vertical & horizontal lines with morphology, return (vertical, horizontal, grid).
    """
    h, w = thr.shape
    # Kernel sizes relative to page size (heuristics)
    v_ksz = max(10, h // 40)
    h_ksz = max(10, w // 40)

    vert_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, v_ksz))
    hori_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (h_ksz, 1))

    vertical = cv2.erode(thr, vert_kernel, iterations=1)
    vertical = cv2.dilate(vertical, vert_kernel, iterations=2)

    horizontal = cv2.erode(thr, hori_kernel, iterations=1)
    horizontal = cv2.dilate(horizontal, hori_kernel, iterations=2)

    grid = cv2.addWeighted(vertical, 0.5, horizontal, 0.5, 0.0)
    grid = cv2.erode(grid, np.ones((3, 3), np.uint8), iterations=1)
    grid = cv2.dilate(grid, np.ones((3, 3), np.uint8), iterations=1)
    return vertical, horizontal, grid


def _unique_sorted_coords(proj: np.ndarray, min_gap: int) -> List[int]:
    """
    Given a 1D projection of line pixels, return unique x (or y) coordinates of grid lines.
    """
    coords = np.where(proj > 0)[0].tolist()
    if not coords:
        return []
    coords.sort()
    merged = [coords[0]]
    for c in coords[1:]:
        if c - merged[-1] >= min_gap:
            merged.append(c)
    return merged


def _cells_from_grid(
    vertical: np.ndarray, horizontal: np.ndarray
) -> List[Tuple[int, int, int, int]]:
    """
    From vertical/horizontal line maps, compute cell rectangles (x0, y0, x1, y1).
    """
    v_proj = vertical.sum(axis=0)
    h_proj = horizontal.sum(axis=1)
    # minimum gap ~ 1% of image dimension to avoid near-duplicates
    min_gap_x = max(8, vertical.shape[1] // 100)
    min_gap_y = max(8, vertical.shape[0] // 100)
    xs = _unique_sorted_coords(v_proj, min_gap_x)
    ys = _unique_sorted_coords(h_proj, min_gap_y)

    cells = []
    # Build rectangles between adjacent grid lines
    for j in range(len(ys) - 1):
        y0, y1 = ys[j], ys[j + 1]
        if y1 - y0 < 8:  # too small
            continue
        for i in range(len(xs) - 1):
            x0, x1 = xs[i], xs[i + 1]
            if x1 - x0 < 8:
                continue
            cells.append((x0, y0, x1, y1))
    return cells


def _group_cells_to_table(
    cells: List[Tuple[int, int, int, int]],
) -> List[List[Tuple[int, int, int, int]]]:
    """
    Heuristic grouping into rows by y, then sort by x.
    """
    if not cells:
        return []

    # sort by top, then left
    cells = sorted(cells, key=lambda b: (b[1], b[0]))
    rows: List[List[Tuple[int, int, int, int]]] = []
    current_row: List[Tuple[int, int, int, int]] = [cells[0]]
    y0 = cells[0][1]
    tol = 6  # pixel tolerance for row grouping

    for b in cells[1:]:
        if abs(b[1] - y0) <= tol:
            current_row.append(b)
        else:
            rows.append(sorted(current_row, key=lambda c: c[0]))
            current_row = [b]
            y0 = b[1]
    rows.append(sorted(current_row, key=lambda c: c[0]))
    # Normalize row width (#columns) by padding missing cells if any (best-effort)
    max_cols = max(len(r) for r in rows)
    for r in rows:
        if len(r) < max_cols:
            # naive pad by extending last cell horizontally
            last = r[-1]
            for _ in range(max_cols - len(r)):
                r.append((last[2], last[1], last[2] + 1, last[3]))
    return rows


def _ocr_cell(img: np.ndarray) -> str:
    # Slight inset to avoid border artifacts
    h, w = img.shape[:2]
    pad = max(1, min(h, w) // 40)
    roi = img[pad : h - pad, pad : w - pad]
    # Tesseract config: single block or sparse text; try psm 6 (block of text)
    txt = pytesseract.image_to_string(roi, config="--oem 1 --psm 6")
    return txt.strip()


def extract_tables_from_image(pil_image: Image.Image) -> List[pd.DataFrame]:
    """
    Image → (detect grid) → cells → OCR → DataFrame(s).
    If no clear grid is found, fallback to line-wise OCR to produce 1-column table.
    """
    img = np.array(pil_image.convert("RGB"))
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    thr = _binarize(gray)
    vertical, horizontal, grid = _detect_grid(thr)

    # Find cell rectangles
    cells = _cells_from_grid(vertical, horizontal)
    rows = _group_cells_to_table(cells)

    tables: List[pd.DataFrame] = []
    if rows and max(len(r) for r in rows) >= 2 and len(rows) >= 2:
        # Build dataframe from OCR of each cell
        data: List[List[str]] = []
        for r in rows:
            row_vals = []
            for x0, y0, x1, y1 in r:
                crop = img[y0:y1, x0:x1]
                row_vals.append(_ocr_cell(crop))
            data.append(row_vals)
        df = pd.DataFrame(data)
        # Trim empty surrounding rows/cols
        df = df.replace(r"^\s*$", None, regex=True)
        df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")
        if not df.empty:
            tables.append(df)
        return tables

    # Fallback: no grid – do linewise OCR, make a single-column DataFrame
    txt = pytesseract.image_to_string(gray, config="--oem 1 --psm 6")
    lines = [l.strip() for l in txt.splitlines() if l.strip()]
    if lines:
        tables.append(pd.DataFrame(lines, columns=["text"]))
    return tables
