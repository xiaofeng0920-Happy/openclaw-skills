# PptxGenJS Tutorial

> **This is the required library for creating PPT slides in this skill.**
> Use `node yourscript.js` to run. Only fall back to an alternative (e.g. `python-pptx`) if `pptxgenjs` is confirmed completely unavailable — state the reason before doing so.

---

## Setup & Basic Structure

**脚本结构：所有代码均必须包裹在 `async main()` 函数内。** 图标流水线使用了 `await`，CommonJS 模块（`.js` 文件）不支持顶层 `await`。以下是每个脚本的标准起始模板：

```javascript
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");

// ── 幻灯片尺寸常量 (LAYOUT_16x9) ─────────────────────────────────
const SLIDE_W   = 10;                      // 宽度，单位英寸
const SLIDE_H   = 5.625;                   // 高度，单位英寸
const MARGIN_X  = 0.5;                     // 左右边距
const CONTENT_W = SLIDE_W - MARGIN_X * 2; // 内容区宽度 = 9"

async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";  // ⚠️ property assignment — NOT pres.setLayout()
  pres.author = "Your Name";
  pres.title  = "Presentation Title";

  const rawSlide = pres.addSlide();
  const sb = new SlideBuilder(rawSlide, SLIDE_W, SLIDE_H);

  // 添加元素…
  sb.addText("Title", { x: 0.5, y: 0.2, w: 9, h: 1.0, fontSize: 40, bold: true }, "title");

  // 规范性检测
  const issues = sb.validate();
  if (issues.length > 0) {
    issues.forEach(i => console.error(i));
    process.exit(1);
  }

  await pres.writeFile({ fileName: "output.pptx" });
  console.log("Done: output.pptx");
}

main().catch(err => { console.error(err); process.exit(1); });
```

**Two rules from the example above — both are mandatory:**

1. **Use `pres.layout = "LAYOUT_16x9"`** (property assignment). `pres.setLayout()` does not exist in current PptxGenJS and throws `TypeError: pres.setLayout is not a function`.
2. **All `await` calls must be inside `async main()`**. Never use top-level `await` in a `.js` CommonJS file — it throws `SyntaxError: await is only valid in async functions`.

## Layout Dimensions

### Coordinate System

All position and size parameters (`x`, `y`, `w`, `h`, `margin`) are in **inches**. There is no implicit padding or safe-area — `y: 0` places an element flush against the very top edge of the slide.

```
(0, 0) ────────────────────────────────────────────────── x → (10, 0)
  |
  |   addText(text, { x: 2, y: 1, w: 4, h: 1.5 })
  |        ┌────────────────────────────┐
  |        │  x=2" → left edge        │
  |        │  y=1" → top edge         │
  |        │  w=4" → width            │
  |        │  h=1.5" → height         │
  |        └────────────────────────────┘
  |        right edge = x + w = 2 + 4 = 6"
  |        bottom edge = y + h = 1 + 1.5 = 2.5"
  y↓
(0, 5.625) ────────────────────────────────────── (10, 5.625)
```

**Units reference:**
- `x`, `y`, `w`, `h`, `margin` → all in **inches**
- `fontSize` → in **points** (1pt = 1/72 inch; 36pt ≈ 0.5")
- `charSpacing` → in points
- `line.width` → in points

**`margin` pitfall:** `addText` has a default internal padding of ~0.05–0.1" on each side. This visual gap is added inside the text box bounds (does not affect x/y/w/h). Set `margin: 0` to remove the internal padding when precise alignment is needed:
```javascript
sb.addText("Title", {
  x: 0.5, y: 0, w: 9, h: 1.0,
  fontSize: 36, bold: true, valign: "middle",
  margin: 0   // removes internal padding so title text aligns predictably
}, "title");
```

### Slide Sizes

Slide dimensions:
- `LAYOUT_16x9`: 10" × 5.625" (default)
- `LAYOUT_16x10`: 10" × 6.25"
- `LAYOUT_4x3`: 10" × 7.5"
- `LAYOUT_WIDE`: 13.3" × 7.5"

---

## SlideBuilder — 元素追踪与规范性检测

**所有元素均通过 `SlideBuilder` 添加，而不直接调用 `slide.addText()` 等原生方法。**

`SlideBuilder` 的两个职责：

1. **元素追踪**：每次添加元素时，自动记录其位置信息（x、y、w、h 及标签）
2. **规范性检测**：所有元素添加完毕后，调用 `sb.validate()` 进行统一检测

### 类定义

```javascript
// ── SlideBuilder: element tracker + validator ───────────────────────
class SlideBuilder {
  constructor(slide, slideW = SLIDE_W, slideH = SLIDE_H) {
    this._s = slide; this._W = slideW; this._H = slideH;
    this._elements = [];  // 记录所有已添加元素，供 validate() 使用
  }

  // 记录元素位置信息
  _track(label, x, y, w, h) {
    this._elements.push({ label, x, y, w: w ?? 0, h: h ?? 0 });
  }

  addText(text, opts, label = 'text')       { this._track(label, opts.x, opts.y, opts.w, opts.h);       return this._s.addText(text, opts); }
  addImage(opts, label = 'image')            { this._track(label, opts.x, opts.y, opts.w, opts.h);       return this._s.addImage(opts); }
  addShape(type, opts, label = 'shape')     { this._track(label, opts.x, opts.y, opts.w??0, opts.h??0); return this._s.addShape(type, opts); }
  addTable(rows, opts, label = 'table')     { this._track(label, opts.x, opts.y, opts.w, opts.h??0);    return this._s.addTable(rows, opts); }
  addChart(type, data, opts, label='chart') { this._track(label, opts.x, opts.y, opts.w, opts.h);       return this._s.addChart(type, data, opts); }

  /**
   * 规范性检测 — 在该幻灯片所有元素添加完毕后调用。
   * 返回 issues 数组；数组为空表示检测通过。
   */
  validate() {
    const issues = [];

    // ── 1. 边界检测 ────────────────────────────────────────────────
    for (const el of this._elements) {
      const { label, x, y, w, h } = el;
      if (x < -0.01 || y < -0.01)
        issues.push(`[越界] "${label}": 负坐标 x=${x} y=${y}`);
      if (x + w > this._W + 0.01)
        issues.push(`[越界] "${label}": 右边缘 ${(x + w).toFixed(3)}" 超出幻灯片宽度 ${this._W}"`);
      if (y + h > this._H + 0.01)
        issues.push(`[越界] "${label}": 下边缘 ${(y + h).toFixed(3)}" 超出幻灯片高度 ${this._H}"`);
    }

    // ── 2. 重叠检测 ────────────────────────────────────────────────
    for (let i = 0; i < this._elements.length; i++) {
      for (let j = i + 1; j < this._elements.length; j++) {
        const a = this._elements[i], b = this._elements[j];
        if (a.w <= 0 || a.h <= 0 || b.w <= 0 || b.h <= 0) continue; // 跳过线条/点
        const overlaps =
          a.x < b.x + b.w - 0.01 && a.x + a.w > b.x + 0.01 &&
          a.y < b.y + b.h - 0.01 && a.y + a.h > b.y + 0.01;
        if (overlaps)
          issues.push(`[重叠] "${a.label}" 与 "${b.label}" 存在重叠`);
      }
    }

    return issues;
  }
}
```


```javascript
// 建立 slide 并添加所有元素
const rawSlide = pres.addSlide();
const sb = new SlideBuilder(rawSlide, SLIDE_W, SLIDE_H);

sb.addText("Title", { x: 0.5, y: 0.2, w: 9, h: 1.0, fontSize: 40, bold: true }, "title");
sb.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 1.1, w: 9, h: 0.06, fill: { color: "0D9488" } }, "divider");
sb.addText("Body content", { x: 0.5, y: 1.4, w: 9, h: 3.9, fontSize: 15 }, "body");

// 所有元素添加完毕后，进行规范性检测
const issues = sb.validate();
if (issues.length > 0) {
  console.error("❌ 规范性检测未通过:");
  issues.forEach(i => console.error("  " + i));
  process.exit(1);  // 返回制作流程重新设计
} else {
  console.log("✅ 规范性检测通过");
}
```

**输出示例（检测未通过）：**
```
❌ 规范性检测未通过:
  [越界] "body": 下边缘 5.300" 超出幻灯片高度 5.625"
  [重叠] "divider" 与 "body" 存在重叠
```

**检测规则：**
- **越界**：`x < 0`、`y < 0`、`x + w > SLIDE_W`、`y + h > SLIDE_H` 之一则触发
- **重叠**：任意两个具有实际面积（w > 0 且 h > 0）的元素在水平和垂直方向均有交叀
- **线条跳过**：w 或 h 为 0 的元素（如分隔线）不参与重叠检测

---

## Text & Formatting

**Font size reference** (always set `fontSize` explicitly — PptxGenJS defaults to 18pt which is too large for body text):

| Element | fontSize |
|---|---|
| Slide title | 36–44 |
| Section header | 20–24 |
| Body text / bullets | 14–16 |
| Captions / labels | 10–12 |

以上字体大小只是建议，实际根据显示效果选择合适的字体大小，下面是使用例子：

```javascript
// Slide title — sb is a SlideBuilder instance (see § SlideBuilder)
sb.addText("Title Text", {
  x: 0.5, y: 0, w: 9, h: 1.0,
  fontSize: 40, fontFace: "Arial", color: "363636", bold: true, valign: "middle"
}, "title");

// Body text
sb.addText("Body Text", {
  x: 0.5, y: 1.2, w: 9, h: 4.0,
  fontSize: 15, fontFace: "Calibri", color: "363636", align: "left", valign: "top",
  shrinkText: true
}, "body");

// Character spacing (use charSpacing, not letterSpacing which is silently ignored)
sb.addText("SPACED TEXT", { x: 1, y: 1, w: 8, h: 1, charSpacing: 6 }, "spaced");

// Rich text arrays
sb.addText([
  { text: "Bold ", options: { bold: true } },
  { text: "Italic ", options: { italic: true } }
], { x: 1, y: 3, w: 8, h: 1 }, "rich");

// Multi-line text (requires breakLine: true)
sb.addText([
  { text: "Line 1", options: { breakLine: true } },
  { text: "Line 2", options: { breakLine: true } },
  { text: "Line 3" }  // Last item doesn't need breakLine
], { x: 0.5, y: 0.5, w: 8, h: 2 }, "multiline");

// Text box margin (internal padding)
sb.addText("Title", {
  x: 0.5, y: 0, w: 9, h: 1.0,
  margin: 0  // Use 0 when aligning text with other elements like shapes or icons
}, "title-margin");
```

**Tip:** Text boxes have internal margin by default. Set `margin: 0` when you need text to align precisely with shapes, lines, or icons at the same x-position.

**Tip:** Always specify `fontSize` explicitly on every `addText` call. Never rely on the default (18pt) — it will make body text appear oversized.

---

## Lists & Bullets

```javascript
// ✅ CORRECT: Multiple bullets
slide.addText([
  { text: "First item", options: { bullet: true, breakLine: true } },
  { text: "Second item", options: { bullet: true, breakLine: true } },
  { text: "Third item", options: { bullet: true } }
], { x: 0.5, y: 0.5, w: 8, h: 3 });

// ❌ WRONG: Never use unicode bullets
slide.addText("• First item", { ... });  // Creates double bullets

// Sub-items and numbered lists
{ text: "Sub-item", options: { bullet: true, indentLevel: 1 } }
{ text: "First", options: { bullet: { type: "number" }, breakLine: true } }
```

---

## Shapes

```javascript
slide.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 0.8, w: 1.5, h: 3.0,
  fill: { color: "FF0000" }, line: { color: "000000", width: 2 }
});

slide.addShape(pres.shapes.OVAL, { x: 4, y: 1, w: 2, h: 2, fill: { color: "0000FF" } });

slide.addShape(pres.shapes.LINE, {
  x: 1, y: 3, w: 5, h: 0, line: { color: "FF0000", width: 3, dashType: "dash" }
});

// With transparency
slide.addShape(pres.shapes.RECTANGLE, {
  x: 1, y: 1, w: 3, h: 2,
  fill: { color: "0088CC", transparency: 50 }
});

// Rounded rectangle (rectRadius only works with ROUNDED_RECTANGLE, not RECTANGLE)
// ⚠️ Don't pair with rectangular accent overlays — they won't cover rounded corners. Use RECTANGLE instead.
slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 1, y: 1, w: 3, h: 2,
  fill: { color: "FFFFFF" }, rectRadius: 0.1
});

// With shadow
slide.addShape(pres.shapes.RECTANGLE, {
  x: 1, y: 1, w: 3, h: 2,
  fill: { color: "FFFFFF" },
  shadow: { type: "outer", color: "000000", blur: 6, offset: 2, angle: 135, opacity: 0.15 }
});
```

Shadow options:

| Property | Type | Range | Notes |
|----------|------|-------|-------|
| `type` | string | `"outer"`, `"inner"` | |
| `color` | string | 6-char hex (e.g. `"000000"`) | No `#` prefix, no 8-char hex — see Common Pitfalls |
| `blur` | number | 0-100 pt | |
| `offset` | number | 0-200 pt | **Must be non-negative** — negative values corrupt the file |
| `angle` | number | 0-359 degrees | Direction the shadow falls (135 = bottom-right, 270 = upward) |
| `opacity` | number | 0.0-1.0 | Use this for transparency, never encode in color string |

To cast a shadow upward (e.g. on a footer bar), use `angle: 270` with a positive offset — do **not** use a negative offset.

**Note**: Gradient fills are not natively supported. Use a gradient image as a background instead.

---

## Dividers & Separators

Use `addShape()` with LINE or a thin RECTANGLE to create visual separators. All coordinates must stay within the slide boundaries (enforced by SlideBuilder).

### Thin Horizontal Line (under title)

```javascript
// 1pt accent-colored line spanning full content width, placed below the title
slide.addShape(pres.ShapeType.line, {
  x: 0.5,
  y: 1.1,   // adjust to match the bottom of your title text box
  w: 9,
  h: 0,
  line: { color: "0D9488", width: 1 }
});
```

### Colored Accent Bar (bolder separator)

```javascript
// Filled rectangle — more visible than a line, works as a section break accent
slide.addShape(pres.ShapeType.rect, {
  x: 0.5,
  y: 1.06,   // adjust to sit just below your title text box
  w: 9,
  h: 0.06,
  fill: { color: "0D9488" },
  line: { color: "0D9488" }
});
```

### Vertical Column Divider

```javascript
// Divides two equal columns; centered between them
const COL_GAP = 0.3;
const COL_W   = (9 - COL_GAP) / 2;      // 4.35" each (9" = slide content width)
const DIV_X   = 0.5 + COL_W + COL_GAP / 2;  // center of the gap

slide.addShape(pres.ShapeType.line, {
  x: DIV_X,
  y: 1.3,    // adjust to match the top of your content area
  w: 0,
  h: 4.0,    // adjust to match the height of your content area
  line: { color: "CBD5E1", width: 1 }  // muted color so it doesn't compete with content
});
```

### Section-Break Slide: Full Header Background Block

```javascript
// Accent-colored block spans the full top area; title text is white on top
slide.addShape(pres.ShapeType.rect, {
  x: 0, y: 0, w: 10, h: 1.5,
  fill: { color: "0D9488" },
  line: { color: "0D9488" }
});
slide.addText("Section Title", {
  x: 0.5, y: 0, w: 9, h: 1.5,
  fontSize: 36, bold: true, color: "FFFFFF", valign: "middle"
});
```

**Rules:**
- Divider `y + h` must not exceed `SLIDE_H` (5.625" for LAYOUT_16x9)
- Line width: 1pt for subtle, 2pt for emphasis; avoid thicker
- Accent bar height: 0.04–0.08" — thinner than 0.04" is invisible, thicker than 0.1" dominates
- Vertical divider color should be muted (e.g. `"CBD5E1"`) so it separates without competing

---

## Images

### Image Sources

```javascript
// From file path
slide.addImage({ path: "images/chart.png", x: 1, y: 1, w: 5, h: 3 });

// From URL
slide.addImage({ path: "https://example.com/image.jpg", x: 1, y: 1, w: 5, h: 3 });

// From base64 (faster, no file I/O)
slide.addImage({ data: "image/png;base64,iVBORw0KGgo...", x: 1, y: 1, w: 5, h: 3 });
```

### Image Options

```javascript
slide.addImage({
  path: "image.png",
  x: 1, y: 1, w: 5, h: 3,
  rotate: 45,              // 0-359 degrees
  rounding: true,          // Circular crop
  transparency: 50,        // 0-100
  flipH: true,             // Horizontal flip
  flipV: false,            // Vertical flip
  altText: "Description",  // Accessibility
  hyperlink: { url: "https://example.com" }
});
```

### Image Sizing Modes

```javascript
// Contain - fit inside, preserve ratio
{ sizing: { type: 'contain', w: 4, h: 3 } }

// Cover - fill area, preserve ratio (may crop)
{ sizing: { type: 'cover', w: 4, h: 3 } }

// Crop - cut specific portion
{ sizing: { type: 'crop', x: 0.5, y: 0.5, w: 2, h: 2 } }
```

### Calculate Dimensions (preserve aspect ratio)

```javascript
const origWidth = 1978, origHeight = 923, maxHeight = 3.0;
const calcWidth = maxHeight * (origWidth / origHeight);
const centerX = (10 - calcWidth) / 2;

slide.addImage({ path: "image.png", x: centerX, y: 1.2, w: calcWidth, h: maxHeight });
```

### Supported Formats

- **Standard**: PNG, JPG, GIF (animated GIFs work in Microsoft 365)
- **SVG**: Works in modern PowerPoint/Microsoft 365

---

## Icons

**Icons are REQUIRED** whenever a slide lists features, steps, categories, or concepts (see SKILL.md § Icons & Tables). Do not skip icons because you are unsure which name to use — pick the closest match from the reference table below.使用图表也能增加ppt的美观性

Install once: `npm install react-icons react react-dom sharp`

**System dependency**: `sharp` requires `librsvg` to process SVG on Linux/macOS. If icons silently fail, install it first:
```bash
# Ubuntu/Debian
sudo apt-get install librsvg2-dev
# macOS
brew install librsvg
```
On Windows, `sharp` bundles its own SVG support and requires no extra installation.

### Diagnostic Check (run this before generating slides)

Run this standalone script to verify the full icon pipeline works end-to-end. If it fails, fix the error before proceeding:

```javascript
// save as test-icon.js, run with: node test-icon.js
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const { FaStar } = require("react-icons/fa");
const fs = require("fs");

async function testIcon() {
  const svg = ReactDOMServer.renderToStaticMarkup(
    React.createElement(FaStar, { color: "#FFFFFF", size: "256" })
  );
  console.log("SVG generated:", svg.length, "chars");
  if (!svg.includes("<svg")) throw new Error("SVG output is empty or invalid");

  const buf = await sharp(Buffer.from(svg), { density: 300 }).png().toBuffer();
  console.log("PNG buffer size:", buf.length, "bytes");
  if (buf.length < 100) throw new Error("PNG output too small — SVG rendering likely failed");

  fs.writeFileSync("test-icon.png", buf);
  console.log("✅ Icon pipeline OK. Check test-icon.png to verify visually.");
}

testIcon().catch(e => {
  console.error("❌ Icon pipeline FAILED:", e.message);
  process.exit(1);
});
```

### Helper Function (copy this verbatim)

```javascript
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");

function renderIconSvg(IconComponent, color = "#FFFFFF", size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(
    React.createElement(IconComponent, { color, size: String(size) })
  );
  if (!svg || !svg.includes("<svg")) {
    throw new Error(`Icon SVG rendering failed for ${IconComponent.displayName || IconComponent.name}`);
  }
  return svg;
}

// ⚠️ MUST include "data:" prefix — PptxGenJS silently ignores images without it
async function iconToBase64Png(IconComponent, color = "#FFFFFF", size = 256) {
  const svg = renderIconSvg(IconComponent, color, size);
  let pngBuffer;
  try {
    pngBuffer = await sharp(Buffer.from(svg), { density: 300 }).png().toBuffer();
  } catch (e) {
    throw new Error(
      `sharp failed to rasterize SVG icon: ${e.message}\n` +
      `Tip: on Linux, run: sudo apt-get install librsvg2-dev\n` +
      `Then reinstall sharp: npm install sharp`
    );
  }
  if (pngBuffer.length < 100) {
    throw new Error("PNG output is suspiciously small — icon likely rendered blank");
  }
  return "data:image/png;base64," + pngBuffer.toString("base64");  // "data:" prefix is required
}
```

### Add Icon to Slide

```javascript
const { FaCheckCircle } = require("react-icons/fa");

// Render icon as white PNG at high resolution (256px), display at 0.4" on slide
const iconData = await iconToBase64Png(FaCheckCircle, "#FFFFFF", 256);

// Icon-in-circle example — set iconY to the desired vertical position on the slide
const iconY = 1.5;  // adjust to your layout
slide.addShape(pres.shapes.OVAL, {
  x: 0.5, y: iconY, w: 0.55, h: 0.55,
  fill: { color: "0D9488" }, line: { color: "0D9488" }
});
slide.addImage({ data: iconData, x: 0.55, y: iconY + 0.05, w: 0.45, h: 0.45 });
```

**Note**: Use size 256 or higher for crisp icons. The size parameter controls rasterization resolution, not display size (which is `w`/`h` in inches). Minimum display size is 0.25" — smaller renders as invisible.

### Common Icons Quick Reference

Use these as defaults. Import from `react-icons/fa` (Font Awesome) unless noted.

| Concept | Icon name | Import |
|---|---|---|
| Check / done / success | `FaCheckCircle` | `react-icons/fa` |
| Star / highlight / featured | `FaStar` | `react-icons/fa` |
| Chart / analytics / growth | `FaChartLine` | `react-icons/fa` |
| Chart bar / statistics | `FaChartBar` | `react-icons/fa` |
| Users / team / people | `FaUsers` | `react-icons/fa` |
| Person / user / profile | `FaUser` | `react-icons/fa` |
| Gear / settings / process | `FaCog` | `react-icons/fa` |
| Light bulb / idea / insight | `FaLightbulb` | `react-icons/fa` |
| Shield / security / trust | `FaShieldAlt` | `react-icons/fa` |
| Globe / global / web | `FaGlobe` | `react-icons/fa` |
| Clock / time / deadline | `FaClock` | `react-icons/fa` |
| Money / finance / revenue | `FaDollarSign` | `react-icons/fa` |
| Rocket / launch / growth | `FaRocket` | `react-icons/fa` |
| Target / goal / objective | `FaBullseye` | `react-icons/fa` |
| Arrow up / increase | `FaArrowUp` | `react-icons/fa` |
| Arrow right / next / flow | `FaArrowRight` | `react-icons/fa` |
| Cloud / cloud service | `FaCloud` | `react-icons/fa` |
| Code / technology | `FaCode` | `react-icons/fa` |
| Database / data | `FaDatabase` | `react-icons/fa` |
| Lock / privacy | `FaLock` | `react-icons/fa` |
| Envelope / email / contact | `FaEnvelope` | `react-icons/fa` |
| Building / company / org | `FaBuilding` | `react-icons/fa` |
| Trophy / award / achievement | `FaTrophy` | `react-icons/fa` |
| Heart / health / wellness | `FaHeart` | `react-icons/fa` |
| Leaf / sustainability / eco | `FaLeaf` | `react-icons/fa` |
| Box / product / package | `FaBox` | `react-icons/fa` |
| Handshake / partnership | `FaHandshake` | `react-icons/fa` |
| Magnifier / search / research | `FaSearch` | `react-icons/fa` |
| Brain / AI / intelligence | `FaBrain` | `react-icons/fa` |
| Mobile / app / device | `FaMobileAlt` | `react-icons/fa` |

### Icon Libraries Available

- `react-icons/fa` — Font Awesome (~1600 icons, broadest coverage, use as default)
- `react-icons/md` — Material Design (~1000 icons, Google style)
- `react-icons/hi` — Heroicons (~300 icons, clean outline)
- `react-icons/bi` — Bootstrap Icons (~1800 icons)

---

## Slide Backgrounds

```javascript
// Solid color
slide.background = { color: "F1F1F1" };

// Color with transparency
slide.background = { color: "FF3399", transparency: 50 };

// Image from URL
slide.background = { path: "https://example.com/bg.jpg" };

// Image from base64
slide.background = { data: "image/png;base64,iVBORw0KGgo..." };
```

---

## Tables

```javascript
slide.addTable([
  ["Header 1", "Header 2"],
  ["Cell 1", "Cell 2"]
], {
  x: 1, y: 1, w: 8, h: 2,
  border: { pt: 1, color: "999999" }, fill: { color: "F1F1F1" }
});

// Advanced with merged cells
let tableData = [
  [{ text: "Header", options: { fill: { color: "6699CC" }, color: "FFFFFF", bold: true } }, "Cell"],
  [{ text: "Merged", options: { colspan: 2 } }]
];
slide.addTable(tableData, { x: 1, y: 3.5, w: 8, colW: [4, 4] });
```

---

## Charts

```javascript
// Bar chart
slide.addChart(pres.charts.BAR, [{
  name: "Sales", labels: ["Q1", "Q2", "Q3", "Q4"], values: [4500, 5500, 6200, 7100]
}], {
  x: 0.5, y: 0.6, w: 6, h: 3, barDir: 'col',
  showTitle: true, title: 'Quarterly Sales'
});

// Line chart
slide.addChart(pres.charts.LINE, [{
  name: "Temp", labels: ["Jan", "Feb", "Mar"], values: [32, 35, 42]
}], { x: 0.5, y: 4, w: 6, h: 3, lineSize: 3, lineSmooth: true });

// Pie chart
slide.addChart(pres.charts.PIE, [{
  name: "Share", labels: ["A", "B", "Other"], values: [35, 45, 20]
}], { x: 7, y: 1, w: 5, h: 4, showPercent: true });
```

### Better-Looking Charts

Default charts look dated. Apply these options for a modern, clean appearance:

```javascript
slide.addChart(pres.charts.BAR, chartData, {
  x: 0.5, y: 1, w: 9, h: 4, barDir: "col",

  // Custom colors (match your presentation palette)
  chartColors: ["0D9488", "14B8A6", "5EEAD4"],

  // Clean background
  chartArea: { fill: { color: "FFFFFF" }, roundedCorners: true },

  // Muted axis labels
  catAxisLabelColor: "64748B",
  valAxisLabelColor: "64748B",

  // Subtle grid (value axis only)
  valGridLine: { color: "E2E8F0", size: 0.5 },
  catGridLine: { style: "none" },

  // Data labels on bars
  showValue: true,
  dataLabelPosition: "outEnd",
  dataLabelColor: "1E293B",

  // Hide legend for single series
  showLegend: false,
});
```

**Key styling options:**
- `chartColors: [...]` - hex colors for series/segments
- `chartArea: { fill, border, roundedCorners }` - chart background
- `catGridLine/valGridLine: { color, style, size }` - grid lines (`style: "none"` to hide)
- `lineSmooth: true` - curved lines (line charts)
- `legendPos: "r"` - legend position: "b", "t", "l", "r", "tr"

---

## Slide Masters

```javascript
pres.defineSlideMaster({
  title: 'TITLE_SLIDE', background: { color: '283A5E' },
  objects: [{
    placeholder: { options: { name: 'title', type: 'title', x: 1, y: 2, w: 8, h: 2 } }
  }]
});

const rawSlide = pres.addSlide({ masterName: "TITLE_SLIDE" });
const sb = new SlideBuilder(rawSlide, SLIDE_W, SLIDE_H);
// placeholder-based addText: bounds are defined by the master; SlideBuilder passes it through
sb.addText("My Title", { placeholder: "title" }, "master-title");
```


## Common Pitfalls

⚠️ These issues cause file corruption, visual bugs, or broken output. Avoid them.

1. **NEVER use "#" with hex colors** - causes file corruption
   ```javascript
   color: "FF0000"      // ✅ CORRECT
   color: "#FF0000"     // ❌ WRONG
   ```

2. **NEVER encode opacity in hex color strings** - 8-char colors (e.g., `"00000020"`) corrupt the file. Use the `opacity` property instead.
   ```javascript
   shadow: { type: "outer", blur: 6, offset: 2, color: "00000020" }          // ❌ CORRUPTS FILE
   shadow: { type: "outer", blur: 6, offset: 2, color: "000000", opacity: 0.12 }  // ✅ CORRECT
   ```

3. **Use `bullet: true`** - NEVER unicode symbols like "•" (creates double bullets)

4. **Use `breakLine: true`** between array items or text runs together

5. **Avoid `lineSpacing` with bullets** - causes excessive gaps; use `paraSpaceAfter` instead

6. **Each presentation needs fresh instance** - don't reuse `pptxgen()` objects

7. **NEVER reuse option objects across calls** - PptxGenJS mutates objects in-place (e.g. converting shadow values to EMU). Sharing one object between multiple calls corrupts the second shape.
   ```javascript
   const shadow = { type: "outer", blur: 6, offset: 2, color: "000000", opacity: 0.15 };
   slide.addShape(pres.shapes.RECTANGLE, { shadow, ... });  // ❌ second call gets already-converted values
   slide.addShape(pres.shapes.RECTANGLE, { shadow, ... });

   const makeShadow = () => ({ type: "outer", blur: 6, offset: 2, color: "000000", opacity: 0.15 });
   slide.addShape(pres.shapes.RECTANGLE, { shadow: makeShadow(), ... });  // ✅ fresh object each time
   slide.addShape(pres.shapes.RECTANGLE, { shadow: makeShadow(), ... });
   ```

8. **Don't use `ROUNDED_RECTANGLE` with accent borders** - rectangular overlay bars won't cover rounded corners. Use `RECTANGLE` instead.
   ```javascript
   // ❌ WRONG: Accent bar doesn't cover rounded corners
   slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 1, y: 1, w: 3, h: 1.5, fill: { color: "FFFFFF" } });
   slide.addShape(pres.shapes.RECTANGLE, { x: 1, y: 1, w: 0.08, h: 1.5, fill: { color: "0891B2" } });

   // ✅ CORRECT: Use RECTANGLE for clean alignment
   slide.addShape(pres.shapes.RECTANGLE, { x: 1, y: 1, w: 3, h: 1.5, fill: { color: "FFFFFF" } });
   slide.addShape(pres.shapes.RECTANGLE, { x: 1, y: 1, w: 0.08, h: 1.5, fill: { color: "0891B2" } });
   ```

9. **NEVER omit `fontSize` on body text** - PptxGenJS default is 18pt, which is larger than the recommended 14–16pt for body text and bullets. Always set it explicitly:
   ```javascript
   // ❌ WRONG: defaults to 18pt, visually oversized
   slide.addText("Body content", { x: 0.5, y: 1, w: 8, h: 3 });

   // ✅ CORRECT: explicitly 15pt
   slide.addText("Body content", { x: 0.5, y: 1, w: 8, h: 3, fontSize: 15 });
   ```

10. **Text overflow — derive element heights top-down from slide dimensions, never estimate bottom-up.** Stacking elements with guessed `h` values causes cumulative overflow. Always compute `available_content_h = slide_h - margins - title_h - gaps`, then assign that value to content text boxes. Add `shrinkText: true` as a safety net for variable-length content.

    Common slide height values: `LAYOUT_16x9 = 5.625"`, `LAYOUT_16x10 = 5.0"`, `LAYOUT_4x3 = 7.5"`

    Also verify for every element: `y + h ≤ slide_h - bottom_margin` and `x + w ≤ slide_w - right_margin`.
    ```javascript
    // ❌ WRONG: stacking estimated heights — cumulative error causes overflow
    slide.addText(title,   { y: 0.3, h: 0.7, ... });
    slide.addText(content, { y: 1.2, h: 3.5, ... });  // 1.2 + 3.5 = 4.7
    slide.addText(footer,  { y: 4.8, h: 0.5, ... });  // 4.8 + 0.5 = 5.3 — exceeds 5.625" with any rounding

    // ✅ CORRECT: budget from slide height
    const SLIDE_H = 5.625, CONTENT_Y = 1.2, BOTTOM_MARGIN = 0.3;
    const CONTENT_H = SLIDE_H - CONTENT_Y - BOTTOM_MARGIN;  // = 4.125"
    slide.addText(content, { y: CONTENT_Y, h: CONTENT_H, fontSize: 15, shrinkText: true, valign: "top" });
    ```

11. **`SyntaxError: await is only valid in async functions`** — caused by using `await` at the top level of a CommonJS `.js` file. Fix: wrap all slide-building code inside `async function main() { ... }` and call `main().catch(...)` at the bottom. See § Setup & Basic Structure for the required script template.

12. **`TypeError: pres.setLayout is not a function`** — `setLayout()` does not exist in PptxGenJS. Use property assignment instead:
    ```javascript
    pres.layout = "LAYOUT_16x9";   // ✅ CORRECT
    pres.setLayout("LAYOUT_16x9"); // ❌ throws TypeError
    ```

---

## Quick Reference

- **Shapes**: RECTANGLE, OVAL, LINE, ROUNDED_RECTANGLE
- **Charts**: BAR, LINE, PIE, DOUGHNUT, SCATTER, BUBBLE, RADAR
- **Layouts**: LAYOUT_16x9 (10"×5.625"), LAYOUT_16x10, LAYOUT_4x3, LAYOUT_WIDE
- **Alignment**: "left", "center", "right"
- **Chart data labels**: "outEnd", "inEnd", "center"
