import fitz  # PyMuPDF
from rapidfuzz import process, fuzz

CANON = {
    # --- your originals (expanded) ---
    "processing": [
        "Mineral Processing and Metallurgical Testing",
        "Mineral Processing",
        "Processing and Metallurgy",
        "Process Plant",
        "Processing Options/Flow Sheet/Design",
        "Metallurgical Testing",
    ],
    "mining_methods": ["Mining Methods", "Mine Design", "Methods"],
    "capex_opex": [
        "Capital and Operating Costs",
        "Capital Costs",
        "Operating Costs",
        "CAPEX",
        "OPEX",
    ],
    "economic_analysis": [
        "Economic Analysis",
        "Project Economics",
        "Economic Analysis and Pre-Feasibility",
        "Dollar Value Calculation",
    ],
    # --- added (useful for retrieval + drivers) ---
    "summary": [
        "Summary",
        "Conclusions and Recommendations",  # often blended into section 1
    ],
    "introduction": [
        "Introduction and Terms of Reference",
        "Introduction",
        "Terms of Reference",
        "Purpose of Report",
        "Sources of Information and Data",
        "Field Involvement by Report Authors",
        "Definitions of Terms",
        "Units of Measure",
        "Acronyms",
        "Glossary of Mining, Geological and Other Technical Terms",
    ],
    "property_location": [
        "Property Description and Location",
        "Location",
        "Property Description",
        "Mineral Claims",
        "Legal Surveys",
        "Requirements to Maintain the Claims in Good Standing",
        "Titles and Obligations / Agreements",
        "Exceptions to Title Opinion",
        "Royalties and Other Encumbrances",
        "Environmental Liabilities",
        "Permits and Licenses",
    ],
    "access_infrastructure": [
        "Accessibility, Climate, Local Resources, Infrastructure, Physiography",
        "Access",
        "Physiography",
        "Climate and Operating Seasons",
        "Vegetation",
        "Local Resources and Infrastructure",
    ],
    "project_infrastructure": ["Project Infrastructure", "Infrastructure"],
    "history": ["History"],
    "geology": [
        "Geological Setting & Mineralization",
        "Geological Setting and Mineralization",
        "Geology and Mineralization",
    ],
    "deposit_types": ["Deposit Types"],
    "exploration": ["Exploration"],
    "drilling": [
        "Drilling",
        "Drilling Methods",
        "Infill Drilling Program",
        "Summary",  # in context of Drilling subsection
    ],
    "sampling_qaqc": [
        "Sample Methods, Preparation, Analysis, Security",
        "Sample Preparation",
        "Analytical Procedures",
        "Quality Control Procedures (QA/QC)",
        "Sample Security",
        "ISO 9000 Certification",
    ],
    "data_verification": ["Data Verification", "Historical Data Verification"],
    "resources_reserves": [
        "Mineral Resource and Mineral Reserve Estimates",
        "Mineral Resource and Mineral Reserve",
        "Resource Estimation",
        "Drillhole Database",
        "Specific Gravity",
        "Variogram Analysis & Modeling",
        "Variogram Analysis",
        "Modeling",
        "Model Verification",
        "Resource Classification",
        "Mineral Resource Statement",
        "Mineral Resource Sensitivity",
        "Mineral Reserve Estimates",
    ],
    "market_studies": ["Market Studies and Contracts", "Market Studies", "Contracts"],
    "environmental_social": [
        "Environmental Studies, Permitting, Social Impact",
        "Environmental Studies",
        "Permitting",
        "Social Impact",
        "Environmental and Permitting",
    ],
    "adjacent_properties": ["Adjacent Properties"],
    "other_data": ["Other Relevant Data and Information"],
    "interpretation_conclusions": ["Interpretation and Conclusions", "Conclusions"],
    "recommendations": [
        "Recommendations",
        "Proposed Budget",
        "Resource Definition Drilling",
        "Other Geological/Geotechnical/Metallurgical/Hydrological Work",
        "Processing Options/Flow Sheet/Design",
        "Economic Analysis and Pre-Feasibility",
        "Environmental and Permitting",
        "Summary",  # in context of Recommendations subsection
    ],
    "references": ["References", "Bibliography"],
    "lists": ["List of Tables", "List of Figures", "LIST OF TABLES", "LIST OF FIGURES"],
    "appendices": ["Appendix", "Appendices"],
}


def normalize_title(t):
    return " ".join(t.replace("\u00a0", " ").split()).lower()


def map_to_canon(title):
    title_norm = normalize_title(title)
    best_key, best_score = None, 0
    for k, aliases in CANON.items():
        m, score, _ = process.extractOne(
            title_norm, [a.lower() for a in aliases], scorer=fuzz.token_set_ratio
        )
        if score > best_score:
            best_key, best_score = k, score
    return best_key if best_score >= 70 else None


import re
import fitz  # PyMuPDF

LEADER_CHARS = r"\.\u2026\u00B7\u2219"  # . … · ∙


def _clean(s: str) -> str:
    if not s:
        return ""
    s = s.replace("\u00a0", " ")  # NBSP → space
    s = re.sub(rf"[{LEADER_CHARS}]", ".", s)  # normalize leaders to '.'
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _level_from_numbering(title: str) -> int:
    # e.g., "14.2.2.1 Geology modeling" -> 4; "2. INTRO ..." -> 1
    m = re.match(r"^\s*(\d+(?:\.\d+)*)\b", title)
    if not m:
        return 1
    return m.group(1).count(".") + 1


def _collect_outline_entries(doc, min_level=1, max_level=None):
    toc = doc.get_toc(simple=True) or []
    if not toc:
        return []
    if max_level is None:
        max_level = max(l for (l, _, _) in toc)
    ents = []
    for lvl, title, p1 in toc:
        if not (min_level <= lvl <= max_level):
            continue
        title = _clean(title or "")
        start = max(0, (p1 or 1) - 1)
        ents.append((lvl, title, start))
    # sort by page, then by level depth so sub-sections can follow
    ents.sort(key=lambda x: (x[2], x[0], x[1]))
    return ents


def _join_wrapped_lines(lines):
    """Join TOC lines where title and page number got split across lines."""
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # if line doesn't end in digits and next line is just/page number, join
        if not re.search(r"\d+\s*$", line) and i + 1 < len(lines):
            nxt = lines[i + 1]
            if re.match(r"^\s*\d+\s*$", nxt):
                out.append(f"{line} {nxt.strip()}")
                i += 2
                continue
        out.append(line)
        i += 1
    return out


def _collect_visual_entries(doc, scan_pages=40, min_level=1, max_level=None):
    n_pages = len(doc)
    scan_pages = min(scan_pages, n_pages)
    # find pages likely containing a ToC
    cand_pages = []
    for i in range(scan_pages):
        txt = doc.load_page(i).get_text("text") or ""
        if not txt:
            continue
        if re.search(r"\b(table of contents|contents)\b", txt, re.I) or re.search(
            r"\.{2,}\s+\d{1,4}\s*$", txt, re.M
        ):
            cand_pages.append(i)

    entries = []
    for i in cand_pages:
        raw = doc.load_page(i).get_text("text") or ""
        lines = [_clean(l) for l in raw.splitlines() if _clean(l)]
        lines = _join_wrapped_lines(lines)

        for line in lines:
            # Capture "title ..... 123" OR "1.2 Title ..... 45" OR even "TITLE 45"
            m = re.search(r"(?P<title>.+?)\s*(?P<page>\d{1,4})\s*$", line)
            if not m:
                continue
            title = _clean(m.group("title"))
            # drop obviously non-toc markers
            if len(title) < 3 or title.lower().startswith(
                ("galway metals", "victorio mountains")
            ):
                continue

            tgt = int(m.group("page"))
            tgt = min(max(tgt - 1, 0), n_pages - 1)

            lvl = _level_from_numbering(title)
            # remove leading numbering from title for consistency
            title = re.sub(r"^\s*\d+(?:\.\d+)*\s*[\-\.:)]*\s*", "", title).strip()

            entries.append((lvl, title, tgt))

    if not entries:
        return []

    if max_level is None:
        max_level = max(l for (l, _, _) in entries)

    # filter by level, dedupe by (title, start)
    filt = [(l, t, s) for (l, t, s) in entries if min_level <= l <= max_level]
    seen = set()
    uniq = []
    for l, t, s in sorted(filt, key=lambda x: (x[2], x[0], x[1])):
        key = (t.lower(), s)
        if key in seen:
            continue
        seen.add(key)
        uniq.append((l, t, s))
    return uniq


def _to_ranges(entries, n_pages):
    """entries: list of (level, title, start). Return list of dicts with end."""
    out = []
    if not entries:
        return out
    entries = sorted(entries, key=lambda x: (x[2], x[0], x[1]))
    for i, (lvl, title, start) in enumerate(entries):
        next_start = entries[i + 1][2] if i + 1 < len(entries) else n_pages
        start = min(max(start, 0), n_pages - 1)
        end = min(max(next_start - 1, 0), n_pages - 1)
        if end < start:
            continue
        out.append({"title": title, "level": lvl, "start": start, "end": end})
    return out


def section_page_ranges_from_bytes(
    pdf_bytes, min_level=1, max_level=3, scan_pages=40, merge_visual_if_sparse=True
):
    """
    Robust ToC extractor:
      - merges outline + printed ToC
      - supports multi-level sections
      - tolerant to leader variations and wrapped lines
    Returns: [{'title','canon','level','start','end'}]
    """
    from rapidfuzz import fuzz, process  # needed for your map_to_canon

    ranges = []
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        n_pages = len(doc)

        outline = _collect_outline_entries(doc, min_level, max_level)
        visual = _collect_visual_entries(doc, scan_pages, min_level, max_level)

        entries = outline
        if merge_visual_if_sparse or not outline:
            # merge: add any visual items not already in outline (by title+start)
            seen = {(t.lower(), s) for (_, t, s) in outline}
            for l, t, s in visual:
                key = (t.lower(), s)
                if key not in seen:
                    entries.append((l, t, s))
            entries.sort(key=lambda x: (x[2], x[0], x[1]))

        out = _to_ranges(entries, n_pages)

        # attach canon (uses your existing normalize_title/map_to_canon)
        for r in out:
            r["canon"] = map_to_canon(r["title"])
        return out


def process_report(pdf_bytes):
    try:
        report_data = section_page_ranges_from_bytes(pdf_bytes)
        # Further processing of the extracted text
        if len(report_data) == 0:
            return {"status": "error", "message": "Failed to extract report data."}
        return report_data
    except Exception as e:
        return {"status": "error", "message": str(e)}
