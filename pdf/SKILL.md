---
name: pdf
description: Use this skill whenever the user wants to do anything with PDF files. This includes creating new PDFs, reading or extracting text/tables from PDFs, combining or merging multiple PDFs into one, splitting PDFs apart, rotating pages, adding watermarks, filling PDF forms, encrypting/decrypting PDFs, extracting images, and OCR on scanned PDFs to make them searchable. If the user mentions a .pdf file or asks to produce one, use this skill.
license: Proprietary. LICENSE.txt has complete terms
---

# PDF Processing Guide

## Overview

This guide covers essential PDF processing operations using Python libraries and command-line tools. For advanced features, JavaScript libraries, and detailed examples, see REFERENCE.md. If you need to fill out a PDF form, read FORMS.md and follow its instructions.

## Quick Start

```python
from pypdf import PdfReader, PdfWriter

# Read a PDF
reader = PdfReader("document.pdf")
print(f"Pages: {len(reader.pages)}")

# Extract text
text = ""
for page in reader.pages:
    text += page.extract_text()
```

## Python Libraries

### pypdf - Basic Operations

#### Merge PDFs
```python
from pypdf import PdfWriter, PdfReader

writer = PdfWriter()
for pdf_file in ["doc1.pdf", "doc2.pdf", "doc3.pdf"]:
    reader = PdfReader(pdf_file)
    for page in reader.pages:
        writer.add_page(page)

with open("merged.pdf", "wb") as output:
    writer.write(output)
```

#### Split PDF
```python
reader = PdfReader("input.pdf")
for i, page in enumerate(reader.pages):
    writer = PdfWriter()
    writer.add_page(page)
    with open(f"page_{i+1}.pdf", "wb") as output:
        writer.write(output)
```

#### Extract Metadata
```python
reader = PdfReader("document.pdf")
meta = reader.metadata
print(f"Title: {meta.title}")
print(f"Author: {meta.author}")
print(f"Subject: {meta.subject}")
print(f"Creator: {meta.creator}")
```

#### Rotate Pages
```python
reader = PdfReader("input.pdf")
writer = PdfWriter()

page = reader.pages[0]
page.rotate(90)  # Rotate 90 degrees clockwise
writer.add_page(page)

with open("rotated.pdf", "wb") as output:
    writer.write(output)
```

### pdfplumber - Text and Table Extraction

#### Extract Text with Layout
```python
import pdfplumber

with pdfplumber.open("document.pdf") as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        print(text)
```

#### Extract Tables
```python
with pdfplumber.open("document.pdf") as pdf:
    for i, page in enumerate(pdf.pages):
        tables = page.extract_tables()
        for j, table in enumerate(tables):
            print(f"Table {j+1} on page {i+1}:")
            for row in table:
                print(row)
```

#### Advanced Table Extraction
```python
import pandas as pd

with pdfplumber.open("document.pdf") as pdf:
    all_tables = []
    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            if table:  # Check if table is not empty
                df = pd.DataFrame(table[1:], columns=table[0])
                all_tables.append(df)

# Combine all tables
if all_tables:
    combined_df = pd.concat(all_tables, ignore_index=True)
    combined_df.to_excel("extracted_tables.xlsx", index=False)
```

### weasyprint - Create PDFs (Recommended)

WeasyPrint converts HTML + CSS to PDF. It handles Unicode, CJK fonts, complex layouts, and watermarks naturally through standard CSS — no manual coordinate calculation or font registration required.

Install: `pip install weasyprint`

#### Basic PDF Creation

```python
from weasyprint import HTML

html = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    @page { size: A4; margin: 2cm; }
    body { font-family: 'Noto Sans CJK SC', 'WenQuanYi Micro Hei', 'Microsoft YaHei', 'PingFang SC', sans-serif; }
  </style>
</head>
<body>
  <h1>Hello / 你好</h1>
  <p>This is a PDF created with WeasyPrint.</p>
</body>
</html>"""

HTML(string=html).write_pdf("hello.pdf")
```

#### Unicode / CJK Fonts

WeasyPrint resolves fonts through CSS `font-family` — no manual registration needed.
For CJK text, list CJK-capable system fonts in CSS with a generic fallback:

```css
body {
  font-family: 'Noto Sans CJK SC', 'WenQuanYi Micro Hei', 'Microsoft YaHei', 'PingFang SC', sans-serif;
}
```

#### Multi-page Document

```python
from weasyprint import HTML

html = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    @page { size: A4; margin: 2cm; }
    body { font-family: 'Noto Sans CJK SC', 'WenQuanYi Micro Hei', sans-serif; }
    h1 { page-break-before: always; }
    h1:first-of-type { page-break-before: avoid; }
  </style>
</head>
<body>
  <h1>第一章 / Chapter 1</h1>
  <p>Chapter 1 content...</p>

  <h1>第二章 / Chapter 2</h1>
  <p>Chapter 2 content...</p>
</body>
</html>"""

HTML(string=html).write_pdf("report.pdf")
```

#### Create Text Watermark with WeasyPrint

Use CSS `position: fixed` to overlay watermark text on every page:

```python
from weasyprint import HTML

html = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    @page { size: A4; margin: 2cm; }
    body { font-family: 'Noto Sans CJK SC', 'WenQuanYi Micro Hei', 'Microsoft YaHei', sans-serif; }
    .watermark {
      position: fixed;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%) rotate(-45deg);
      font-size: 72px;
      color: rgba(180, 180, 180, 0.30);
      z-index: 9999;
      white-space: nowrap;
      pointer-events: none;
    }
  </style>
</head>
<body>
  <div class="watermark">机密文件 / CONFIDENTIAL</div>
  <h1>Document Title</h1>
  <p>Document content here...</p>
</body>
</html>"""

HTML(string=html).write_pdf("watermarked.pdf")
```

### reportlab - Create PDFs (Low-level / Alternative)

Use ReportLab only when you need fine-grained pixel-level control (e.g. precise coordinate drawing, custom graphics). For most document creation tasks, prefer WeasyPrint above.

#### Unicode Font Setup

Register a Unicode/CJK font via `TTFont` before any drawing. Use the snippet below to auto-detect a suitable font on the current platform:

```python
import sys, os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def _register_cjk_font(alias="CustomFont"):
    skill_dir = os.path.dirname(os.path.abspath(__file__))
    if sys.platform == "win32":
        candidates = [
            r"C:/Windows/Fonts/msyh.ttc",
            r"C:/Windows/Fonts/simsun.ttc",
        ]
    elif sys.platform == "darwin":
        candidates = [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Medium.ttc",
        ]
    else:  # Linux / Android
        candidates = [
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        ]
    for path in candidates:
        if os.path.exists(path):
            pdfmetrics.registerFont(TTFont(alias, path))
            return alias
    raise RuntimeError(
        "No correct font, run: apt install fonts-wqy-microhei"
    )
```

#### Canvas (coordinate-based)

```python
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

_register_cjk_font()  # registers as "CustomFont"
c = canvas.Canvas("output.pdf", pagesize=letter)
width, height = letter
c.setFont("CustomFont", 14)
c.drawString(100, height - 100, "机密文件 / Confidential")
c.save()
```

#### Platypus (flow-based layout)

```python
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

_register_cjk_font()  # registers as "CustomFont"
doc = SimpleDocTemplate("report.pdf", pagesize=letter)
styles = getSampleStyleSheet()
for name in ("Title", "Normal", "Heading1", "Heading2", "BodyText"):
    styles[name].fontName = "CustomFont"

story = [
    Paragraph("报告标题 / Report Title", styles["Title"]),
    Spacer(1, 12),
    Paragraph("这是正文。This is body text.", styles["Normal"]),
]
doc.build(story)
```

#### Subscripts and Superscripts

**IMPORTANT**: Never use Unicode subscript/superscript characters (₀₁₂₃₄₅₆₇₈₉, ⁰¹²³⁴⁵⁶⁷⁸⁹) in ReportLab PDFs. The built-in fonts do not include these glyphs, causing them to render as solid black boxes.

Instead, use ReportLab's XML markup tags in Paragraph objects:
```python
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet

styles = getSampleStyleSheet()

# Subscripts: use <sub> tag
chemical = Paragraph("H<sub>2</sub>O", styles['Normal'])

# Superscripts: use <super> tag
squared = Paragraph("x<super>2</super> + y<super>2</super>", styles['Normal'])
```

For canvas-drawn text (not Paragraph objects), manually adjust font the size and position rather than using Unicode subscripts/superscripts.

## Command-Line Tools

### pdftotext (poppler-utils)
```bash
# Extract text
pdftotext input.pdf output.txt

# Extract text preserving layout
pdftotext -layout input.pdf output.txt

# Extract specific pages
pdftotext -f 1 -l 5 input.pdf output.txt  # Pages 1-5
```

### qpdf
```bash
# Merge PDFs
qpdf --empty --pages file1.pdf file2.pdf -- merged.pdf

# Split pages
qpdf input.pdf --pages . 1-5 -- pages1-5.pdf
qpdf input.pdf --pages . 6-10 -- pages6-10.pdf

# Rotate pages
qpdf input.pdf output.pdf --rotate=+90:1  # Rotate page 1 by 90 degrees

# Remove password
qpdf --password=mypassword --decrypt encrypted.pdf decrypted.pdf
```

### pdftk (if available)
```bash
# Merge
pdftk file1.pdf file2.pdf cat output merged.pdf

# Split
pdftk input.pdf burst

# Rotate
pdftk input.pdf rotate 1east output rotated.pdf
```

## Common Tasks

### Extract Text from Scanned PDFs
```python
# Requires: pip install pytesseract pdf2image
import pytesseract
from pdf2image import convert_from_path

# Convert PDF to images
images = convert_from_path('scanned.pdf')

# OCR each page
text = ""
for i, image in enumerate(images):
    text += f"Page {i+1}:\n"
    text += pytesseract.image_to_string(image)
    text += "\n\n"

print(text)
```

### Add Watermark
```python
from pypdf import PdfReader, PdfWriter

# Create watermark (or load existing)
watermark = PdfReader("watermark.pdf").pages[0]

# Apply to all pages
reader = PdfReader("document.pdf")
writer = PdfWriter()

for page in reader.pages:
    page.merge_page(watermark)
    writer.add_page(page)

with open("watermarked.pdf", "wb") as output:
    writer.write(output)
```

#### Creating Text Watermarks

For watermarks in newly created PDFs, use WeasyPrint CSS (see `### weasyprint` section above).

To add a text watermark to an **existing PDF** (any source), generate a watermark-only PDF with WeasyPrint and merge it using pypdf:

```python
import io
from weasyprint import HTML
from pypdf import PdfReader, PdfWriter

# Step 1: generate a single-page watermark PDF in memory
watermark_html = """
<!DOCTYPE html><html><head><meta charset="utf-8"><style>
  @page { size: A4; margin: 0; }
  body { margin: 0; }
  .watermark {
    position: fixed; top: 50%; left: 50%;
    transform: translate(-50%, -50%) rotate(-45deg);
    font-size: 72px;
    font-family: 'Noto Sans CJK SC', 'WenQuanYi Micro Hei', sans-serif;
    color: rgba(180, 180, 180, 0.30);
    white-space: nowrap;
  }
</style></head>
<body><div class="watermark">机密文件 / CONFIDENTIAL</div></body></html>
"""
wm_bytes = HTML(string=watermark_html).write_pdf()
watermark_page = PdfReader(io.BytesIO(wm_bytes)).pages[0]

# Step 2: merge watermark onto every page of the source PDF
reader = PdfReader("document.pdf")
writer = PdfWriter()
for page in reader.pages:
    page.merge_page(watermark_page)
    writer.add_page(page)

with open("watermarked.pdf", "wb") as f:
    writer.write(f)
```

### Extract Images
```bash
# Using pdfimages (poppler-utils)
pdfimages -j input.pdf output_prefix

# This extracts all images as output_prefix-000.jpg, output_prefix-001.jpg, etc.
```

### Password Protection
```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("input.pdf")
writer = PdfWriter()

for page in reader.pages:
    writer.add_page(page)

# Add password
writer.encrypt("userpassword", "ownerpassword")

with open("encrypted.pdf", "wb") as output:
    writer.write(output)
```

## Quick Reference

| Task | Best Tool | Command/Code |
|------|-----------|-------------- |
| Merge PDFs | pypdf | `writer.add_page(page)` |
| Split PDFs | pypdf | One page per file |
| Extract text | pdfplumber | `page.extract_text()` |
| Extract tables | pdfplumber | `page.extract_tables()` |
| Create PDFs (recommended) | weasyprint | `HTML(string=html).write_pdf(...)` |
| Add watermark (recommended) | weasyprint + pypdf | CSS `.watermark` + `merge_page()` |
| Create PDFs (low-level) | reportlab | Canvas or Platypus |
| Command line merge | qpdf | `qpdf --empty --pages ...` |
| OCR scanned PDFs | pytesseract | Convert to image first |
| Fill PDF forms | pdf-lib or pypdf (see FORMS.md) | See FORMS.md |

## Next Steps

- For advanced pypdfium2 usage, see REFERENCE.md
- For JavaScript libraries (pdf-lib), see REFERENCE.md
- If you need to fill out a PDF form, follow the instructions in FORMS.md
- For troubleshooting guides, see REFERENCE.md
