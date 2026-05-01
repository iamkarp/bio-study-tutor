# PDF extraction

The reference Bio app only handled PPTX and DOCX. For subjects whose source material is PDF (textbook chapters, research papers, slides exported as PDF), add a small `tools/extract_pdf.py`.

## Approach

Use `pypdf` (pure Python, no system deps) for text-based PDFs:

```python
#!/usr/bin/env python3
"""Extract text from .pdf files into markdown."""
from __future__ import annotations
import re
import sys
from pathlib import Path

from pypdf import PdfReader

REPO = Path(__file__).resolve().parents[1]
EXTRACTED = REPO / "raw" / "extracted"


def slug_for(name: str) -> str:
    base = re.sub(r"\.pdf$", "", name, flags=re.I)
    return re.sub(r"[^a-z0-9-]+", "-", base.lower()).strip("-")


def extract_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    out: list[str] = [f"# {path.name}\n",
                       f"_Extracted from `{path.name}` — {len(reader.pages)} pages_\n"]
    for i, page in enumerate(reader.pages, 1):
        out.append(f"## Page {i} {{#page-{i:03d}}}\n")
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        text = re.sub(r"\n{3,}", "\n\n", text.strip())
        if text:
            out.append(text)
        out.append("")
    return "\n".join(out)


def main() -> int:
    paths = [Path(p) for p in sys.argv[1:]]
    if not paths:
        for d in [REPO, REPO / "raw"]:
            if d.exists():
                paths.extend(sorted(d.glob("*.pdf")))
        paths = list({p.resolve() for p in paths})
    if not paths:
        print("no .pdf files found", file=sys.stderr)
        return 1
    EXTRACTED.mkdir(parents=True, exist_ok=True)
    for p in paths:
        slug = slug_for(p.name)
        out_path = EXTRACTED / f"{slug}.md"
        print(f"  {p.name} → {out_path.relative_to(REPO)}")
        out_path.write_text(extract_pdf(p), encoding="utf-8")
    print(f"extracted {len(paths)} pdf files into {EXTRACTED.relative_to(REPO)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Install: `pip3 install pypdf`.

## When this isn't enough

- **Scanned PDFs (image-based)** — `pypdf` returns empty text. Use OCR via `pdf2image` + `pytesseract`, or services like AWS Textract.
- **Math-heavy PDFs** — equations come out as garbled Unicode. Consider `pdfminer.six` with `LAParams` tuning, or convert to LaTeX via Mathpix / nougat.
- **Multi-column layouts** — text order may be wrong. `pdfplumber` handles columns better than `pypdf`.

For a typical course PDF (text-based, single-column lecture notes or chapter PDF), `pypdf` is sufficient and fast.
