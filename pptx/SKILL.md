---
name: pptx
description: "Use this skill any time a .pptx file is involved in any way — as input, output, or both. This includes: creating slide decks, pitch decks, or presentations; reading, parsing, or extracting text from any .pptx file (even if the extracted content will be used elsewhere, like in an email or summary); editing, modifying, or updating existing presentations; combining or splitting slide files; working with templates, layouts, speaker notes, or comments. Trigger whenever the user mentions \"deck,\" \"slides,\" \"presentation,\" or references a .pptx filename, regardless of what they plan to do with the content afterward. If a .pptx file needs to be opened, created, or touched, use this skill."
license: Proprietary. LICENSE.txt has complete terms
---

# PPTX Skill

## Quick Reference

| Task | Action |
|------|--------|
| Read/analyze existing PPT | See [§ Reading Content](#reading-content) |
| Create a new PPT (no template) | Follow [§ Creation Workflow](#creation-workflow) Steps 1–4 |
| Create from template | Follow [§ Creation Workflow](#creation-workflow) Steps 1–4 (Step 2 为模板处理) |
**创建和编辑ppt的工具介绍在[pptxgenjs.md]文件中，必需阅读该文件**
---

## Reading Content

```bash
# Text extraction
python -m markitdown presentation.pptx

# Visual overview
python scripts/thumbnail.py presentation.pptx

# Raw XML
python scripts/office/unpack.py presentation.pptx unpacked/
```

---

## Creation Workflow

Creating any PPT — from scratch or from a template — follows **three sequential steps**. **Do not skip or reorder steps.**

---

### Step 1 — Content Generation

**User requirements take priority.** If the user specifies content, structure, talking points, data, or any other constraints, follow them exactly and do not override them with the guidelines below. Apply these guidelines only to fill gaps where the user has not expressed a preference.

Before writing a single slide, research and plan the content. Skipping this step produces shallow, generic presentations that fail to inform or persuade.

#### Step 1 — Deep Research

Use `search` and `browser` tools to build a knowledge base before writing anything.

- Use primary sources (official reports, government stats, peer-reviewed papers, industry analysts); cross-reference at least 2 sources per major claim
- Record exact figures, dates, and citations; flag data older than 2 years
- Identify 3–5 key insights that support your thesis; discard tangential data; group into themes

#### Step 2 — Content Planning

- **Single core message**: reducible to one sentence — "[Audience] should [X] because [Y]"; every slide must support it
- **Narrative arc**: problem–insight–solution–action (persuasive) or context–findings–implications (analytical)
- **Slide rules**: one point per slide; title = assertion not topic; 8–12 slides for a pitch, 15–20 for a report

#### Step 3 — Content Density

- 3–5 bullets max per slide; each bullet ≤ 15 words; no full paragraphs
- Every quantitative claim must cite its source inline (e.g., "Source: IMF 2024")
- Define audience first — adjust depth, jargon, and framing accordingly

---

### Step 2 — Template Handling (if applicable)

If a template or existing `.pptx` file is provided:
- Read [editing.md](editing.md) for the full template workflow: analyze → unpack → edit slides → clean → pack
- Apply the content outline from Step 1 to determine what goes on each slide
- Use `python scripts/thumbnail.py presentation.pptx` to analyze the template before editing

If no template: skip this step and proceed directly to Step 3.

---

### Step 3 — PPT Design

#### 总体要求：

**Don't create boring slides.** Plain bullets on a white background won't impress anyone. Consider ideas from this list for each slide.
**Content-rich AND visually clear — both are required.** Every slide must carry substantial information (data, examples, evidence, or structured detail), AND be immediately readable at a glance. These are not opposites: use visual structure (icons, tables, charts, color blocks, columns) to pack more content without creating clutter.
**PPT主题一致性并且主次分明** 选择合适配色方案，视觉上要具有主次区别，也要有特定元素突出主题

##### Color Palettes

Choose colors that match your topic — don't default to generic blue. Use these palettes as inspiration:

| Theme | Primary | Secondary | Accent |
|-------|---------|-----------|--------|
| **Midnight Executive** | `1E2761` (navy) | `CADCFC` (ice blue) | `FFFFFF` (white) |
| **Forest & Moss** | `2C5F2D` (forest) | `97BC62` (moss) | `F5F5F5` (cream) |
| **Coral Energy** | `F96167` (coral) | `F9E795` (gold) | `2F3C7E` (navy) |
| **Warm Terracotta** | `B85042` (terracotta) | `E7E8D1` (sand) | `A7BEAE` (sage) |
| **Ocean Gradient** | `065A82` (deep blue) | `1C7293` (teal) | `21295C` (midnight) |
| **Charcoal Minimal** | `36454F` (charcoal) | `F2F2F2` (off-white) | `212121` (black) |
| **Teal Trust** | `028090` (teal) | `00A896` (seafoam) | `02C39A` (mint) |
| **Berry & Cream** | `6D2E46` (berry) | `A26769` (dusty rose) | `ECE2D0` (cream) |
| **Sage Calm** | `84B59F` (sage) | `69A297` (eucalyptus) | `50808E` (slate) |
| **Cherry Bold** | `990011` (cherry) | `FCF6F5` (off-white) | `2F3C7E` (navy) |

#### 具体设计流程（❗必须严格执行，不得跳过）

每张幻灯片按以下循环执行，**未通过第 3 步检测的幻灯片不得推进到下一张**：

1. **内容选取** — 从 Step 1 的研究成果中，选定本页所需的核心内容与数据
2. **页面设计与内容填充** — 依据主要需求与所选内容，如果有模板则依照模板设计，完成本页的视觉与布局设计并填充内容，**必须满足总体要求**
3. **❗ 规范性检测（必須）** — 本页所有元素添加完毕后，必须检测ppt是否满足[总体要求]，**必须调用 `sb.validate()`，方法的具体实现在[./pptxgenjs.md]文件中**，验证以下三项：
   - 所有元素（文本框、图片、图表、形状）均未超出幻灯片边界
   - 所有元素之间无重叠
   - 当前页面设计满足设计要求
   当满足以上需求 → 检测通过，推进下一张
   当`sb.validate()` 返回非空数组或者页面设计不满足设计要求 → **立即返回第 1 步重新设计，禁止继续**

#### For Each Slide

**Every slide needs a visual element** — image, chart, icon, or shape. Text-only slides are forgettable.

以下提供了部分设计选择, 如果存在step2的模板则以模板为基础，下列规则作为辅助：

**Layout options:**
- Two-column (text left, illustration on right)
- Icon + text rows (icon in colored circle, bold header, description below)
- 2x2 or 2x3 grid (image on one side, grid of content blocks on other)
- Half-bleed image (full left or right side) with content overlay

**Data display options:**
- Large stat callouts (big numbers 60-72pt with small labels below)
- Comparison columns (before/after, pros/cons, side-by-side options)
- Timeline or process flow (numbered steps, arrows)

**Visual polish options:**
- Icons in small colored circles next to section headers
- Italic accent text for key stats or taglines
- don't default to Arial. Pick a header font with personality and pair it with a clean body font.

**Use icons when:**
- A slide lists 2 or more features, benefits, steps, categories, or concepts — each item gets an icon
- A slide has a section header or subheading alongside body content — add an icon to each header
- A slide would otherwise consist of nothing but a title and bullet points — replace bullets with icon+text rows
- Content has a spatial or directional meaning (upload/download, in/out, growth/decline) — use a directional icon to reinforce it
- **Icon implementation** — use `react-icons` rendered to base64 PNG via `sharp`, then `slide.addImage()`. See [pptxgenjs.md](pptxgenjs.md) § Icons for the exact pattern.

**Use tables when:**
- A slide compares 2 or more options, plans, versions, or time periods across multiple attributes
- A slide lists items that each have 2 or more associated properties (name + value + unit, feature + status + owner, etc.)
- A slide would otherwise use a multi-column bullet layout to show parallel structured data
- Content has rows and columns of meaning, even if not labeled as a “table” by the user
**Table implementation** — use `slide.addTable()` with a header row styled in the accent color. See [pptxgenjs.md](pptxgenjs.md) § Tables.

**Before writing icon/table code, verify the following — fix these in code before QA, not after:**
- Every `slide.addImage()` call for an icon must use a non-empty base64 string; if `sharp` or `react-icons` returns empty output, the icon will silently appear blank
- Every `slide.addTable()` must explicitly set `colW` (column widths array) so total width matches the table's `w`; omitting `colW` lets PptxGenJS distribute widths arbitrarily, often causing truncation
- Header row cells must have `fill: { color: "ACCENTCOLOR" }`, `color: "FFFFFF"`, and `bold: true` set explicitly


**Dividers & Section Separators**Use dividers to break up content and add visual structure.
**根据ppt内容和布局来添加，以下参考案例:**
- **Thin horizontal line** under the title: 1–2pt, accent color, spans 80–100% of slide width
- **Colored accent bar**: a filled rectangle, 0.06–0.1" tall, full width, accent color — bolder than a line
- **Vertical divider**: separates two columns; 1pt, muted color, centered between the columns
- **Section background block**: a filled rectangle spanning the entire h or w zone 
See [pptxgenjs.md](pptxgenjs.md) § Dividers & Separators for implementation code.

#### Avoid (Common Mistakes)

- **Don't repeat the same layout** — vary columns, cards, and callouts across slides
- **Don't skimp on size contrast** 
- **Don't default to blue** — pick colors that reflect the specific topic
- **Don't style one slide and leave the rest plain** — commit fully or keep it simple throughout
- **Don't create text-only slides** — add images, icons, charts, or visual elements; avoid plain title + bullets
- **Don't use plain bullets when icons apply** — if a slide lists features, steps, or concepts, use icon+text rows instead of plain bullet points; icons are required, not optional decoration
- **Don't forget text box padding** — when aligning lines or shapes with text edges, set `margin: 0` on the text box or offset the shape to account for padding
- **Don't use low-contrast elements** — icons AND text need strong contrast against the background; avoid light text on light backgrounds or dark text on dark backgrounds
- **Never overlap elements** — all text boxes, shapes, images, and icons must have clear separation; if two elements occupy the same screen area, one must be repositioned or removed
- **Distribute content evenly** — balance visual weight across the slide; avoid clustering all content on one side or in one corner while leaving the other side empty
- **No large blank areas** — every significant empty region (larger than roughly 30% of the slide area) must be filled with a relevant visual element, background shape, or deliberate negative space treatment; accidental whitespace is a layout failure
- **Never exceed slide boundaries** — every element must stay within the slide edges; 

### Step 4 — Implementation with PptxGenJS

**前置条件： Read [pptxgenjs.md](pptxgenjs.md) ,ppt制作的具体均参考该文件**

**📌 Mandatory toolchain: PptxGenJS (Node.js).**
- Creating slides from scratch → `pptxgenjs` npm package, executed with `node yourscript.js`
- The only Python scripts in this skill are for reading (`markitdown`), unpacking/packing XML (`unpack.py`/`pack.py`), and QA (`thumbnail.py`) — none of them create slides
- Only fall back to an alternative library (e.g. `python-pptx`) if `pptxgenjs` is confirmed completely unavailable in the current environment; in that case, state the reason explicitly before proceeding

---

## QA (Required)

**Assume there are problems. Your job is to find them.**

Your first render is almost never correct. Approach QA as a bug hunt, not a confirmation step. If you found zero issues on first inspection, you weren't looking hard enough.

### Content QA

```bash
python -m markitdown output.pptx
```

Check for missing content, typos, wrong order.

**When using templates, check for leftover placeholder text:**

```bash
python -m markitdown output.pptx | grep -iE "xxxx|lorem|ipsum|this.*(page|slide).*layout"
```

If grep returns results, fix them before declaring success.

### Visual QA

**⚠️ USE SUBAGENTS** — even for 2-3 slides. You've been staring at the code and will see what you expect, not what's there. Subagents have fresh eyes.

Convert slides to images (see [Converting to Images](#converting-to-images)), then use this prompt:

```
Visually inspect these slides. Assume there are issues — find them.

Look for:
- Overlapping elements (text through shapes, lines through words, stacked elements)
- Text overflow or cut off at edges/box boundaries
- Decorative lines positioned for single-line text but title wrapped to two lines
- Source citations or footers colliding with content above
- Elements too close (< 0.3" gaps) or cards/sections nearly touching
- Uneven gaps (large empty area in one place, cramped in another)
- Insufficient margin from slide edges (< 0.5")
- Columns or similar elements not aligned consistently
- Low-contrast text (e.g., light gray text on cream-colored background)
- Low-contrast icons (e.g., dark icons on dark backgrounds without a contrasting circle)
- Text boxes too narrow causing excessive wrapping
- Leftover placeholder content
- **Icons not visible or rendering as broken/blank images** — every icon added via addImage() must appear as a recognizable symbol, not a gray box or empty space
- **Icons invisible due to color blending** — icon color too similar to its circle/background; icon must be clearly distinguishable from its container
- **Icon sizing wrong** — icons that are too small (< 0.2" makes them illegible) or too large (overflows its circle or neighboring text)
- **Table header row unstyled** — header row must be visually distinct (accent background color + white bold text); plain header that looks identical to body rows is a defect
- **Table column widths causing text truncation** — cell text cut off or hidden due to column too narrow; all cell content must be fully visible
- **Table extending beyond slide boundaries** — right edge or bottom edge of table cropped by slide border
- **Table borders missing or invisible** — if borders were specified, they must be visible; borderless tables must look intentionally borderless, not accidentally broken

For each slide, list issues or areas of concern, even if minor.

Read and analyze these images:
1. /path/to/slide-01.jpg (Expected: [brief description])
2. /path/to/slide-02.jpg (Expected: [brief description])

Report ALL issues found, including minor ones.
```

### Verification Loop

1. Generate slides → Convert to images → Inspect
2. **List issues found** (if none found, look again more critically)
3. Fix issues
4. **Re-verify affected slides** — one fix often creates another problem
5. Repeat until a full pass reveals no new issues

**Do not declare success until you've completed at least one fix-and-verify cycle.**

---

## Converting to Images

Convert presentations to individual slide images for visual inspection:

```bash
python scripts/office/soffice.py --headless --convert-to pdf output.pptx
pdftoppm -jpeg -r 150 output.pdf slide
```

This creates `slide-01.jpg`, `slide-02.jpg`, etc.

To re-render specific slides after fixes:

```bash
pdftoppm -jpeg -r 150 -f N -l N output.pdf slide-fixed
```

---

## Dependencies

- `pip install "markitdown[pptx]"` - text extraction
- `pip install Pillow` - thumbnail grids
- `npm install -g pptxgenjs` - creating from scratch
- LibreOffice (`soffice`) - PDF conversion (auto-configured for sandboxed environments via `scripts/office/soffice.py`)
- Poppler (`pdftoppm`) - PDF to images
