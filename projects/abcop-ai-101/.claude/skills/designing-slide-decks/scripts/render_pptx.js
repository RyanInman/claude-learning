'use strict';
// Draws the same laid-out primitives into a .pptx via pptxgenjs.
//
// Like the HTML renderer, this file computes no positions of its own. If a deck
// looks right in the browser but wrong in PowerPoint, the bug is a translation
// mistake in here, never a layout decision — layout.js is the single authority.

const path = require('path');
const PptxGenJS = require(path.join(__dirname, 'node_modules', 'pptxgenjs'));

// pptxgenjs rejects "#"-prefixed colors by silently writing invalid XML, which
// PowerPoint then reports as a corrupt file. Strip it at the boundary.
function hex(c) { return c == null ? null : String(c).replace('#', '').toUpperCase(); }

function addText(slide, prim) {
  const runs = prim.runs.map((r) => {
    const parts = String(r.text).split('\n');
    return parts.map((part, i) => ({
      text: part,
      options: {
        bold: !!r.bold,
        italic: !!r.italic,
        fontFace: r.mono ? prim.monoFont : prim.font,
        fontSize: r.size || prim.size,
        color: hex(r.color || prim.color),
        breakLine: i < parts.length - 1,
      },
    }));
  }).flat();

  slide.addText(runs.length ? runs : [{ text: '' }], {
    x: prim.x, y: prim.y, w: prim.w, h: prim.h,
    align: prim.align || 'left',
    valign: prim.valign === 'middle' ? 'middle' : 'top',
    fontFace: prim.font,
    fontSize: prim.size,
    color: hex(prim.color),
    // Zero margins and matched line spacing are what keep pptx text sitting in
    // the same place the browser drew it; pptx defaults add ~0.05" of padding.
    margin: 0,
    lineSpacingMultiple: 1.28,
    charSpacing: prim.letterSpacing ? prim.letterSpacing * prim.size : 0,
    wrap: !prim.noWrap,
    shrinkText: false,
    isTextBox: true,
  });
}

function addShape(pres, slide, prim) {
  const opts = { x: prim.x, y: prim.y, w: prim.w, h: prim.h };
  if (prim.fill) opts.fill = { color: hex(prim.fill) };
  else opts.fill = { type: 'none' };
  if (prim.lineWidth) {
    opts.line = { color: hex(prim.lineColor), width: prim.lineWidth };
    if (prim.dashed) opts.line.dashType = 'dash';
  }
  else opts.line = { type: 'none' };

  let type = pres.ShapeType.rect;
  if (prim.kind === 'ellipse') type = pres.ShapeType.ellipse;
  else if (prim.radius) {
    type = pres.ShapeType.roundRect;
    // pptx expresses corner radius as a fraction of the shorter side, not inches.
    opts.rectRadius = Math.min(0.5, prim.radius / Math.min(prim.w, prim.h));
  }
  slide.addShape(type, opts);
}

function renderPptx(deck, outPath) {
  const pres = new PptxGenJS();
  pres.defineLayout({ name: 'WIDE', width: deck.page.w, height: deck.page.h });
  pres.layout = 'WIDE';
  if (deck.meta.title) pres.title = String(deck.meta.title);
  if (deck.meta.author) pres.author = String(deck.meta.author);

  const sans = deck.design.t.sans;
  const mono = deck.design.t.mono;

  for (const s of deck.slides) {
    const slide = pres.addSlide();
    slide.background = { color: hex(s.bg) };
    for (const prim of s.prims) {
      if (prim.background) continue; // already applied as the slide background
      if (prim.kind === 'rect' || prim.kind === 'ellipse') addShape(pres, slide, prim);
      else if (prim.kind === 'line') {
        slide.addShape(pres.ShapeType.rect, {
          x: prim.x, y: prim.y, w: prim.w, h: Math.max(0.008, prim.thickness / 72),
          fill: { color: hex(prim.color) }, line: { type: 'none' },
        });
      } else if (prim.kind === 'image') {
        slide.addImage({ path: prim.path, x: prim.x, y: prim.y, w: prim.w, h: prim.h });
      } else if (prim.kind === 'text') {
        addText(slide, Object.assign({}, prim, {
          font: prim.font || sans,
          monoFont: mono,
        }));
      } else {
        throw new Error(`pptx renderer has no case for primitive kind "${prim.kind}".`);
      }
    }
    if (s.notes) slide.addNotes(String(s.notes));
  }

  return pres.writeFile({ fileName: outPath }).then(() => outPath);
}

module.exports = { renderPptx };
