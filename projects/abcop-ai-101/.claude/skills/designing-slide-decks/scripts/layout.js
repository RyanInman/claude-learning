'use strict';
// Layout engine: spec -> flat list of positioned primitives, measured in inches.
//
// Both renderers consume this same output, which is the whole point: the browser
// preview and the .pptx are two drawings of one layout, so a design approved on
// screen cannot drift in the exported file. Nothing here knows about HTML or
// pptx, and neither renderer is allowed to reposition anything.

const fs = require('fs');
const path = require('path');
const { resolveDesign } = require('./themes');

const PAGE_W = 13.333;
const PAGE_H = 7.5;
const SAFE_BOTTOM = 7.05; // content below this is overflow; the engine reports it

// ---------------------------------------------------------------- measurement

// Character-width ratios as a fraction of the em, averaged over mixed-case text.
// Deliberately a hair generous: over-estimating height pushes content apart,
// which looks loose; under-estimating overlaps text, which looks broken.
const WIDTH_RATIO = { sans: 0.52, mono: 0.601, serif: 0.5 };
const LINE_HEIGHT = 1.28;

function charsPerLine(widthIn, sizePt, mono, serif) {
  const ratio = mono ? WIDTH_RATIO.mono : (serif ? WIDTH_RATIO.serif : WIDTH_RATIO.sans);
  const charIn = ratio * sizePt / 72;
  return Math.max(1, Math.floor(widthIn / charIn));
}

function wrapCount(text, widthIn, sizePt, mono, serif) {
  const cpl = charsPerLine(widthIn, sizePt, mono, serif);
  let lines = 0;
  for (const para of String(text == null ? '' : text).split('\n')) {
    if (!para.length) { lines += 1; continue; }
    let cur = 0;
    for (const word of para.split(/\s+/)) {
      const add = cur === 0 ? word.length : cur + 1 + word.length;
      if (add <= cpl) { cur = add; }
      else {
        lines += 1;
        // A single word longer than the line still occupies whole lines.
        cur = word.length > cpl ? (lines += Math.floor(word.length / cpl), word.length % cpl) : word.length;
      }
    }
    lines += 1;
  }
  return Math.max(1, lines);
}

function textHeight(text, widthIn, sizePt, mono, serif) {
  return wrapCount(text, widthIn, sizePt, mono, serif) * (sizePt / 72) * LINE_HEIGHT;
}

// ------------------------------------------------------------------- glyphs

// Icons are a filled circle plus one centred character. Restricting to glyphs
// present in the core fonts keeps the icon identical in the browser and in
// PowerPoint on a machine that has none of our assets — an SVG icon set would
// need rasterising to survive the pptx round-trip.
const GLYPHS = {
  terminal: '>_', bolt: '⚡', check: '✓', cross: '✗',
  star: '★', dot: '●', arrow: '→', up: '↑', down: '↓',
  book: '▤', gear: '⚙', flag: '⚑', pin: '◆',
  bulb: '☼', warn: '⚠', clock: '◴', layers: '≣',
  search: '⌕', chat: '“', doc: '☷', brain: '◎',
  one: '1', two: '2', three: '3', four: '4', five: '5',
  // Monochrome symbols that take the icon colour, unlike emoji.
  erase: '⌫', undo: '↺', redo: '↻', compress: '⤓', expand: '⤒',
  equals: '≡', plus: '+', minus: '–', percent: '%',
  // Emoji: full-colour pictures. They ignore the colour they are given, so they
  // cannot sit inside a tinted circle and look deliberate. Use only when the
  // specific picture matters more than the styling.
  broom: '🧹', press: '🗜', rewindEmoji: '⏪', sparkle: '✨',
};

function glyphFor(name) {
  if (name == null) return GLYPHS.dot;
  if (GLYPHS[name]) return GLYPHS[name];
  // A short literal string is a legitimate icon ("1", "A", "%").
  if (String(name).length <= 2) return String(name);
  throw new Error(
    `Unknown icon "${name}". Available: ${Object.keys(GLYPHS).join(', ')} ` +
    `(or pass a 1-2 character literal).`);
}

// ------------------------------------------------------------------ context

function makeCtx(design, slide, basedir) {
  const { t, p } = design;
  const dark = isDark(slide, t);
  return {
    t, p, dark, basedir,
    body: t.sans, mono: t.mono,
    serif: /Georgia|Times/.test(t.sans),
    fg: dark ? t.darkText : t.text,
    dim: dark ? t.darkMuted : t.muted,
    rule: dark ? t.darkLine : t.line,
    soft: dark ? t.panelBar : t.fill,
    accent: t.accent,
  };
}

function isDark(slide, t) {
  const bg = slide.background;
  if (!bg || bg === 'light') return false;
  if (bg === 'dark') return true;
  // Custom hex: decide by luminance so text contrast stays correct.
  const hex = String(bg).replace('#', '');
  if (!/^[0-9A-Fa-f]{6}$/.test(hex)) return false;
  const [r, g, b] = [0, 2, 4].map((i) => parseInt(hex.slice(i, i + 2), 16));
  return (0.299 * r + 0.587 * g + 0.114 * b) < 140;
}

function bgColor(slide, t) {
  const bg = slide.background;
  if (!bg || bg === 'light') return t.bg;
  if (bg === 'dark') return t.dark;
  return String(bg).replace('#', '');
}

function color(ctx, name, fallback) {
  if (name == null) return fallback;
  const key = String(name);
  if (/^[0-9A-Fa-f]{6}$/.test(key)) return key;
  const aliases = {
    accent: ctx.accent, muted: ctx.dim, text: ctx.fg, ok: ctx.t.ok, bad: ctx.t.bad,
    okCode: ctx.t.okCode, badCode: ctx.t.badCode, code: ctx.t.code, codeDim: ctx.t.codeDim,
    dark: ctx.t.dark, panel: ctx.t.panel, line: ctx.rule, fill: ctx.soft,
  };
  if (aliases[key]) return aliases[key];
  if (ctx.t[key] && /^[0-9A-Fa-f]{6}$/.test(ctx.t[key])) return ctx.t[key];
  throw new Error(
    `Unknown color "${name}". Use a theme key (accent, muted, ok, bad, ...) or a ` +
    `6-digit hex with no "#" prefix.`);
}

// ------------------------------------------------------------------ builder

class Box {
  constructor() { this.out = []; this.maxY = 0; }
  push(prim) { this.out.push(prim); this.maxY = Math.max(this.maxY, prim.y + (prim.h || 0)); return prim; }
  concat(prims) { for (const p of prims) this.push(p); return this; }
}

function runsOf(el, ctx, size, defColor, P) {
  if (Array.isArray(el.runs)) {
    return el.runs.map((r, i) => ({
      text: r.break ? '\n' + (r.text || '') : (r.text || ''),
      bold: !!r.bold, italic: !!r.italic, mono: !!r.mono,
      size: r.size || size,
      color: color(ctx, r.color, defColor),
      src: P && P.concat(['runs', i, 'text']),
    }));
  }
  return [{
    text: String(el.text == null ? '' : el.text),
    bold: !!el.bold, italic: !!el.italic, mono: !!el.mono,
    size, color: defColor,
    src: P && P.concat(['text']),
  }];
}

function runsPlain(runs) { return runs.map((r) => r.text).join(''); }

// ----------------------------------------------------------------- elements
// Every element handler has the signature (el, ctx, frame) -> {prims, h} where
// frame is {x, y, w}. Handlers never read the page directly, so any element
// works unchanged inside a column at any width.

const ELEMENTS = {};

ELEMENTS.text = (el, ctx, f, P) => {
  const size = el.size || ctx.p.bodySize;
  const c = color(ctx, el.color, ctx.fg);
  const runs = runsOf(el, ctx, size, c, P);
  const mono = runs.every((r) => r.mono);
  // `w` caps the measure so a paragraph can sit in a column of a slide that is
  // otherwise full width — without it, long text runs under anything pinned
  // beside it with `at:`.
  const w = el.w ? Math.min(el.w, f.w) : f.w;
  const h = el.h || textHeight(runsPlain(runs), w, size, mono, ctx.serif);
  return {
    h,
    prims: [{
      kind: 'text', x: f.x, y: f.y, w, h,
      runs, size, color: c, align: el.align || 'left', valign: 'top',
      font: mono ? ctx.mono : ctx.body,
    }],
  };
};

ELEMENTS.bullets = (el, ctx, f, P) => {
  const size = el.size || ctx.p.bodySize;
  const gap = 0.14 * ctx.p.scale;
  const marker = el.marker === 'dash' ? '–' : '•';
  const indent = size / 72 * 1.5;
  const b = new Box();
  let y = f.y;
  (el.items || []).forEach((raw, i) => {
    const item = typeof raw === 'string' ? { text: raw } : raw;
    const c = color(ctx, item.color, ctx.fg);
    const h = textHeight(item.text, f.w - indent, size, false, ctx.serif);
    b.push({
      kind: 'text', x: f.x, y, w: indent, h: size / 72 * 1.4,
      runs: [{ text: marker, size, color: color(ctx, item.markerColor, ctx.accent), bold: true }],
      size, color: ctx.accent, align: 'left', valign: 'top', font: ctx.body,
    });
    b.push({
      kind: 'text', x: f.x + indent, y, w: f.w - indent, h,
      runs: [{ text: item.text, size, color: c, bold: !!item.bold,
        src: P && P.concat(typeof raw === 'string' ? ['items', i] : ['items', i, 'text']) }],
      size, color: c, align: 'left', valign: 'top', font: ctx.body,
    });
    y += h + gap;
  });
  return { prims: b.out, h: Math.max(0, y - f.y - gap) };
};

ELEMENTS.code = (el, ctx, f, P) => {
  const size = el.fontSize || ctx.p.codeSize;
  const lines = (el.lines || []).map((l) => (typeof l === 'string' ? { t: l } : l));
  const pad = 0.18;
  const barH = el.title === false ? 0 : 0.3;
  const lineH = size / 72 * 1.45;
  const h = el.h || (barH + pad * 2 + Math.max(1, lines.length) * lineH);
  const b = new Box();
  b.push({ kind: 'rect', x: f.x, y: f.y, w: f.w, h, fill: ctx.t.panel, radius: 0.08 });
  if (barH) {
    // PowerPoint cannot round individual corners, so the bar is a rounded rect
    // with its bottom squared off by a thin overlay. Both renderers draw the
    // same three shapes and therefore agree.
    b.push({ kind: 'rect', x: f.x, y: f.y, w: f.w, h: barH, fill: ctx.t.panelBar, radius: 0.08 });
    b.push({ kind: 'rect', x: f.x, y: f.y + barH - 0.08, w: f.w, h: 0.08, fill: ctx.t.panelBar });
    for (let i = 0; i < 3; i++) {
      b.push({ kind: 'ellipse', x: f.x + 0.14 + i * 0.16, y: f.y + barH / 2 - 0.045, w: 0.09, h: 0.09,
        fill: [ctx.t.badCode, ctx.t.codeDim, ctx.t.okCode][i] });
    }
    if (typeof el.title === 'string') {
      b.push({
        kind: 'text', x: f.x + 0.66, y: f.y + 0.03, w: f.w - 0.8, h: barH - 0.06,
        runs: [{ text: el.title, size: Math.max(9, size - 2), color: ctx.t.codeDim, mono: true,
          src: P && P.concat(['title']) }],
        size: Math.max(9, size - 2), color: ctx.t.codeDim, align: 'left', valign: 'middle', font: ctx.mono,
      });
    }
  }
  let y = f.y + barH + pad;
  lines.forEach((l, li) => {
    const raw = (el.lines || [])[li];
    // Console lines never wrap; a line too long for the panel is a spec problem
    // the author must break by hand, so the renderer keeps it on one line.
    b.push({
      kind: 'text', x: f.x + pad, y, w: f.w - pad * 2, h: lineH, noWrap: true,
      runs: [{ text: l.t == null ? '' : String(l.t), size: l.s || size, mono: true, bold: !!l.b,
        color: color(ctx, l.c, ctx.t.code),
        src: P && P.concat(typeof raw === 'string' ? ['lines', li] : ['lines', li, 't']) }],
      size: l.s || size, color: color(ctx, l.c, ctx.t.code), align: 'left', valign: 'top', font: ctx.mono,
    });
    y += lineH;
  });
  return { prims: b.out, h };
};

ELEMENTS.callout = (el, ctx, f, P) => {
  const size = el.size || ctx.p.bodySize + 1;
  const style = el.style || (ctx.dark ? 'onDark' : 'solid');
  const fills = {
    solid: { bg: ctx.t.dark, fg: ctx.t.darkText, line: null },
    tint: { bg: ctx.t.tint, fg: ctx.t.text, line: null },
    onDark: { bg: ctx.t.panelBar, fg: ctx.t.darkText, line: null },
    outline: { bg: null, fg: ctx.fg, line: ctx.accent },
  };
  const sk = fills[style];
  if (!sk) throw new Error(`Unknown callout style "${el.style}". Use solid, tint, onDark, or outline.`);
  const pad = 0.22 * ctx.p.scale;
  const iconD = el.icon ? 0.44 : 0;
  const innerX = f.x + pad + (iconD ? iconD + 0.18 : 0);
  const innerW = f.w - pad * 2 - (iconD ? iconD + 0.18 : 0);
  const b = new Box();
  let ih = 0;
  const parts = [];
  if (el.bold) {
    parts.push({ text: el.bold, bold: true, size: size + 1,
      color: el.style === 'tint' ? ctx.accent : sk.fg, src: P && P.concat(['bold']) });
  }
  const runs = el.bold && !el.text && !el.runs ? [] : runsOf(el, ctx, size, sk.fg, P);
  const boldH = el.bold ? textHeight(el.bold, innerW, size + 1, false, ctx.serif) : 0;
  const restText = runsPlain(runs);
  const restH = restText ? textHeight(restText, innerW, size, false, ctx.serif) : 0;
  ih = boldH + restH + (boldH && restH ? 0.06 : 0);
  const h = el.h || ih + pad * 2;
  b.push({ kind: 'rect', x: f.x, y: f.y, w: f.w, h, fill: sk.bg, radius: 0.1,
    lineColor: sk.line, lineWidth: sk.line ? 1.25 : 0 });
  if (iconD) {
    b.push({ kind: 'ellipse', x: f.x + pad, y: f.y + (h - iconD) / 2, w: iconD, h: iconD, fill: ctx.accent });
    b.push({ kind: 'text', x: f.x + pad, y: f.y + (h - iconD) / 2, w: iconD, h: iconD,
      runs: [{ text: glyphFor(el.icon), size: size, color: ctx.t.accentText, bold: true }],
      size, color: ctx.t.accentText, align: 'center', valign: 'middle', font: ctx.body });
  }
  let y = f.y + (h - ih) / 2;
  if (parts.length) {
    b.push({ kind: 'text', x: innerX, y, w: innerW, h: boldH, runs: parts,
      size: size + 1, color: parts[0].color, align: el.align || 'left', valign: 'top', font: ctx.body });
    y += boldH + 0.06;
  }
  if (restText) {
    b.push({ kind: 'text', x: innerX, y, w: innerW, h: restH, runs,
      size, color: sk.fg, align: el.align || 'left', valign: 'top', font: ctx.body });
  }
  return { prims: b.out, h };
};

ELEMENTS.chips = (el, ctx, f, P) => {
  const size = el.size || Math.max(10, ctx.p.bodySize - 2);
  const h = size / 72 * 2.1;
  const gap = 0.12;
  const styles = {
    tint: { bg: ctx.dark ? ctx.t.panelBar : ctx.t.tint, fg: ctx.dark ? ctx.t.darkText : ctx.accent, line: null },
    solid: { bg: ctx.accent, fg: ctx.t.accentText, line: null },
    muted: { bg: null, fg: ctx.dim, line: ctx.rule },
  };
  const sk = styles[el.style || 'tint'];
  if (!sk) throw new Error(`Unknown chip style "${el.style}". Use tint, solid, or muted.`);
  const labels = el.labels || [];
  const b = new Box();
  if (el.fit === false) {
    const cw = (f.w - gap * (labels.length - 1)) / labels.length;
    labels.forEach((label, i) => chip(b, ctx, sk, label, f.x + i * (cw + gap), f.y, cw, h, size,
      P && P.concat(['labels', i])));
  } else {
    let x = f.x;
    let y = f.y;
    let rows = 1;
    labels.forEach((label, i) => {
      const cw = String(label).length * (size / 72) * 0.56 + 0.32;
      if (x + cw > f.x + f.w && x > f.x) { x = f.x; y += h + gap; rows += 1; }
      chip(b, ctx, sk, label, x, y, cw, h, size, P && P.concat(['labels', i]));
      x += cw + gap;
    });
    return { prims: b.out, h: rows * h + (rows - 1) * gap };
  }
  return { prims: b.out, h };
};

function chip(b, ctx, sk, label, x, y, w, h, size, src) {
  b.push({ kind: 'rect', x, y, w, h, fill: sk.bg, radius: h / 2,
    lineColor: sk.line, lineWidth: sk.line ? 1 : 0 });
  b.push({ kind: 'text', x, y, w, h, runs: [{ text: String(label), size, color: sk.fg, bold: true, src }],
    size, color: sk.fg, align: 'center', valign: 'middle', font: ctx.body });
}

ELEMENTS.cards = (el, ctx, f, P) => {
  const list = el.cards || [];
  const gap = el.gap == null ? 0.26 : el.gap;
  const cw = (f.w - gap * (list.length - 1)) / Math.max(1, list.length);
  const pad = 0.24;
  const b = new Box();
  // Cards in a row share one height so their edges line up; a ragged row of
  // boxes is the most common way a generated deck looks unfinished.
  const heights = list.map((c) => cardHeight(c, ctx, cw - pad * 2));
  // Cards sized purely to their text come out short and stamp-like on an
  // otherwise empty slide, so a row claims a presence-worthy minimum unless the
  // spec asks for a specific height (or the row is nested inside a column).
  const floor = f.w > 7 ? 2.3 : 1.2;
  const h = el.height || Math.max(...heights, floor);
  list.forEach((c, i) => {
    const x = f.x + i * (cw + gap);
    const emph = !!c.emphasis;
    b.push({ kind: 'rect', x, y: f.y, w: cw, h,
      fill: emph ? (ctx.dark ? ctx.t.panelBar : ctx.t.tint) : (ctx.dark ? ctx.t.panelBar : ctx.t.fill),
      radius: 0.12, lineColor: emph ? ctx.accent : ctx.rule, lineWidth: emph ? 1.5 : 1 });
    b.concat(cardBody(c, ctx, { x: x + pad, y: f.y + pad, w: cw - pad * 2 }, h - pad * 2,
      P && P.concat(['cards', i])).prims);
  });
  return { prims: b.out, h };
};

function cardParts(c, ctx, w) {
  const size = ctx.p.bodySize;
  const parts = [];
  if (c.icon) parts.push({ type: 'icon', h: 0.5 + 0.14 });
  if (c.name) parts.push({ type: 'name', h: textHeight(c.name, w, size + 4, false, ctx.serif) + 0.06 });
  if (c.sub) parts.push({ type: 'sub', h: textHeight(c.sub, w, size - 1, false, ctx.serif) + 0.08 });
  if (c.mono) parts.push({ type: 'mono', h: textHeight(c.mono, w, size - 2, true, false) + 0.08 });
  if (c.lead) parts.push({ type: 'lead', h: textHeight(c.lead, w, size, false, ctx.serif) + 0.08 });
  for (const r of c.rows || []) {
    const label = r.label ? `${r.label}  ` : '';
    parts.push({ type: 'row', row: r, h: textHeight(label + r.text, w, size - 1, false, ctx.serif) + 0.07 });
  }
  for (const t of c.bullets || []) {
    const ind = (size - 1) / 72 * 1.4;
    parts.push({ type: 'bullet', text: t, h: textHeight(t, w - ind, size - 1, false, ctx.serif) + 0.06 });
  }
  return parts;
}

function cardHeight(c, ctx, w) {
  const pad = 0.24;
  let h = cardParts(c, ctx, w).reduce((a, p) => a + p.h, 0);
  if (c.example) h += textHeight(c.example, w, ctx.p.bodySize - 2, false, ctx.serif) + 0.16;
  if (c.tag) h += 0.42;
  return h + pad * 2;
}

function cardBody(c, ctx, f, innerH, P) {
  const size = ctx.p.bodySize;
  const at = (k) => (P ? P.concat(k) : undefined);
  const b = new Box();
  let y = f.y;
  let rowN = -1;
  let bulletN = -1;
  for (const part of cardParts(c, ctx, f.w)) {
    if (part.type === 'icon') {
      b.push({ kind: 'ellipse', x: f.x, y, w: 0.5, h: 0.5, fill: ctx.accent });
      b.push({ kind: 'text', x: f.x, y, w: 0.5, h: 0.5,
        runs: [{ text: glyphFor(c.icon), size: size + 1, color: ctx.t.accentText, bold: true }],
        size, color: ctx.t.accentText, align: 'center', valign: 'middle', font: ctx.body });
    } else if (part.type === 'name') {
      b.push(txt(ctx, f.x, y, f.w, part.h, c.name, size + 4, ctx.fg, { bold: true, src: at(['name']) }));
    } else if (part.type === 'sub') {
      b.push(txt(ctx, f.x, y, f.w, part.h, c.sub, size - 1, ctx.accent, { bold: true, src: at(['sub']) }));
    } else if (part.type === 'mono') {
      b.push(txt(ctx, f.x, y, f.w, part.h, c.mono, size - 2, ctx.dim, { mono: true, src: at(['mono']) }));
    } else if (part.type === 'lead') {
      b.push(txt(ctx, f.x, y, f.w, part.h, c.lead, size, ctx.fg, { bold: true, src: at(['lead']) }));
    } else if (part.type === 'row') {
      const r = part.row;
      rowN += 1;
      const runs = [];
      if (r.label) {
        runs.push({ text: r.label + '  ', size: size - 1, bold: true,
          color: color(ctx, r.labelColor, ctx.accent), src: at(['rows', rowN, 'label']) });
      }
      runs.push({ text: r.text, size: size - 1, color: ctx.dim, src: at(['rows', rowN, 'text']) });
      b.push({ kind: 'text', x: f.x, y, w: f.w, h: part.h, runs,
        size: size - 1, color: ctx.dim, align: 'left', valign: 'top', font: ctx.body });
    } else if (part.type === 'bullet') {
      bulletN += 1;
      const ind = (size - 1) / 72 * 1.4;
      b.push(txt(ctx, f.x, y, ind, part.h, '•', size - 1, ctx.dim, {}));
      b.push(txt(ctx, f.x + ind, y, f.w - ind, part.h, part.text, size - 1, ctx.dim,
        { src: at(['bullets', bulletN]) }));
    }
    y += part.h;
  }
  // example and tag pin to the bottom of the card, not to the flow.
  if (c.example) {
    const eh = textHeight(c.example, f.w, ctx.p.bodySize - 2, false, ctx.serif);
    const ey = f.y + innerH - eh - (c.tag ? 0.42 : 0);
    b.push(txt(ctx, f.x, ey, f.w, eh, c.example, ctx.p.bodySize - 2, ctx.dim,
      { italic: true, src: at(['example']) }));
  }
  if (c.tag) {
    const solid = c.tagStyle === 'solid';
    const tw = String(c.tag).length * (ctx.p.bodySize / 72) * 0.5 + 0.3;
    const ty = f.y + innerH - 0.3;
    b.push({ kind: 'rect', x: f.x, y: ty, w: tw, h: 0.28, radius: 0.14,
      fill: solid ? ctx.accent : null, lineColor: solid ? null : ctx.accent, lineWidth: solid ? 0 : 1 });
    b.push({ kind: 'text', x: f.x, y: ty, w: tw, h: 0.28,
      runs: [{ text: String(c.tag), size: Math.max(9, ctx.p.bodySize - 3), bold: true,
        color: solid ? ctx.t.accentText : ctx.accent, src: at(['tag']) }],
      size: Math.max(9, ctx.p.bodySize - 3), color: ctx.accent, align: 'center', valign: 'middle', font: ctx.body });
  }
  return { prims: b.out, h: innerH };
}

function txt(ctx, x, y, w, h, text, size, c, opt) {
  return {
    kind: 'text', x, y, w, h,
    // `src` is the spec path this string came from, carried on the run so the
    // studio can write an in-browser edit back to the right field. Runs without
    // one are simply not editable — that is how decorative text opts out.
    runs: [{
      text: String(text), size, color: c,
      bold: !!opt.bold, italic: !!opt.italic, mono: !!opt.mono, src: opt.src,
    }],
    size, color: c, align: opt.align || 'left', valign: 'top',
    font: opt.mono ? ctx.mono : ctx.body,
  };
}

ELEMENTS.icon_rows = (el, ctx, f, P) => {
  const size = ctx.p.bodySize;
  const items = el.items || [];
  const at = (i, k) => (P ? P.concat(['items', i, k]) : undefined);
  const b = new Box();
  if (el.layout === 'list') {
    const d = el.iconSize || 0.42;
    const nameW = Math.min(3.2, f.w * 0.32);
    let y = f.y;
    items.forEach((it, i) => {
      const bodyW = f.w - d - 0.2 - nameW - 0.24;
      const nh = textHeight(it.name || '', nameW, size + 1, false, ctx.serif)
        + (it.cmd ? textHeight(it.cmd, nameW, size - 2, true, false) + 0.04 : 0);
      const bh = textHeight(it.body || '', bodyW, size - 1, false, ctx.serif);
      const rh = Math.max(el.rowHeight || 0, nh, bh, d) + 0.22;
      b.push({ kind: 'ellipse', x: f.x, y, w: d, h: d, fill: ctx.accent });
      b.push({ kind: 'text', x: f.x, y, w: d, h: d,
        runs: [{ text: glyphFor(it.icon), size: size + (d - 0.42) * 26,
          color: ctx.t.accentText, bold: true }],
        size, color: ctx.t.accentText, align: 'center', valign: 'middle', font: ctx.body });
      b.push(txt(ctx, f.x + d + 0.2, y, nameW, nh, it.name || '', size + 1, ctx.fg,
        { bold: true, src: at(i, 'name') }));
      if (it.cmd) {
        b.push(txt(ctx, f.x + d + 0.2, y + textHeight(it.name || '', nameW, size + 1, false, ctx.serif) + 0.02,
          nameW, 0.2, it.cmd, size - 2, ctx.accent, { mono: true, src: at(i, 'cmd') }));
      }
      b.push(txt(ctx, f.x + d + 0.2 + nameW + 0.24, y, bodyW, bh, it.body || '', size - 1, ctx.dim,
        { src: at(i, 'body') }));
      y += rh;
      if (el.dividers && i < items.length - 1) {
        b.push({ kind: 'line', x: f.x, y: y - 0.11, w: f.w, color: ctx.rule, thickness: 1 });
      }
    });
    return { prims: b.out, h: y - f.y };
  }
  const cols = el.columns || 2;
  const gap = 0.3;
  const cw = (f.w - gap * (cols - 1)) / cols;
  const d = 0.46;
  const textW = cw - d - 0.2;
  const lastRowStart = Math.floor((items.length - 1) / cols) * cols;
  const lastRowCount = items.length - lastRowStart;
  // A trailing row of 2 under a row of 3 reads as an accident unless it is
  // centred, so `centerLast` shifts just that row by the leftover half-width.
  const lastShift = el.centerLast && lastRowCount < cols
    ? (cols - lastRowCount) * (cw + gap) / 2 : 0;
  let rowH = 0;
  let y = f.y;
  items.forEach((it, i) => {
    const col = i % cols;
    if (col === 0 && i > 0) { y += rowH + 0.26; rowH = 0; }
    const x = f.x + col * (cw + gap) + (i >= lastRowStart ? lastShift : 0);
    const hh = textHeight(it.head || '', textW, size + 1, false, ctx.serif);
    const bh = textHeight(it.body || '', textW, size - 1, false, ctx.serif);
    rowH = Math.max(rowH, hh + bh + 0.08, d, el.rowHeight || 0);
    b.push({ kind: 'ellipse', x, y, w: d, h: d, fill: ctx.accent });
    b.push({ kind: 'text', x, y, w: d, h: d,
      runs: [{ text: glyphFor(it.icon), size: size + 1, color: ctx.t.accentText, bold: true }],
      size, color: ctx.t.accentText, align: 'center', valign: 'middle', font: ctx.body });
    b.push(txt(ctx, x + d + 0.2, y, textW, hh, it.head || '', size + 1, ctx.fg,
      { bold: true, src: at(i, 'head') }));
    b.push(txt(ctx, x + d + 0.2, y + hh + 0.06, textW, bh, it.body || '', size - 1, ctx.dim,
      { src: at(i, 'body') }));
  });
  return { prims: b.out, h: y + rowH - f.y };
};

ELEMENTS.numbered = (el, ctx, f, P) => {
  const size = ctx.p.bodySize + 1;
  const d = 0.42;
  const b = new Box();
  let y = f.y;
  (el.items || []).forEach((raw, i) => {
    const item = typeof raw === 'string' ? { text: raw } : raw;
    const tw = f.w - d - 0.24;
    const th = textHeight(item.text, tw, size, false, ctx.serif);
    const rh = Math.max(el.rowHeight || 0, th, d) + 0.2;
    b.push({ kind: 'ellipse', x: f.x, y, w: d, h: d, fill: null, lineColor: ctx.accent, lineWidth: 1.4 });
    b.push({ kind: 'text', x: f.x, y, w: d, h: d,
      runs: [{ text: String(i + 1), size: size - 1, color: ctx.accent, bold: true }],
      size, color: ctx.accent, align: 'center', valign: 'middle', font: ctx.body });
    b.push(txt(ctx, f.x + d + 0.24, y + (d - Math.min(th, d)) / 2 * 0.4, tw, th, item.text, size, ctx.fg,
      { src: P && P.concat(typeof raw === 'string' ? ['items', i] : ['items', i, 'text']) }));
    y += rh;
  });
  return { prims: b.out, h: Math.max(0, y - f.y - 0.2) };
};

ELEMENTS.quote = (el, ctx, f, P) => {
  const size = el.size || ctx.p.subtitleSize + 2;
  const align = el.align || 'right';
  const qh = textHeight(el.text, f.w, size, false, ctx.serif);
  const b = new Box();
  b.push({ kind: 'text', x: f.x, y: f.y, w: f.w, h: qh,
    runs: [{ text: el.text, size, italic: true, color: color(ctx, el.color, ctx.accent),
      src: P && P.concat(['text']) }],
    size, color: ctx.accent, align, valign: 'top', font: ctx.body });
  let h = qh;
  if (el.caption) {
    const ch = textHeight(el.caption, f.w, size - 4, false, ctx.serif);
    b.push(txt(ctx, f.x, f.y + qh + 0.08, f.w, ch, el.caption, size - 4, ctx.dim,
      { align, src: P && P.concat(['caption']) }));
    h += ch + 0.08;
  }
  return { prims: b.out, h };
};

ELEMENTS.divider = (el, ctx, f) => ({
  h: 0.02,
  prims: [{ kind: 'line', x: f.x, y: f.y, w: el.w || f.w, color: color(ctx, el.color, ctx.rule), thickness: el.thickness || 1 }],
});

ELEMENTS.spacer = (el, ctx, f) => ({ h: el.h == null ? 0.2 : el.h, prims: [] });

ELEMENTS.image = (el, ctx, f, P) => {
  const h = el.h || 2.5;
  const w = el.w || f.w;
  if (!el.path) throw new Error('An `image` element needs a `path`.');
  // Resolved against the spec's directory, never the working directory, so a
  // build from another cwd finds the same artwork the author meant.
  el = Object.assign({}, el, { path: path.resolve(ctx.basedir || '.', el.path) });
  // A missing file degrades to a visible placeholder rather than failing the
  // build, so a deck can be laid out around artwork that has not arrived yet —
  // and the gap is impossible to ship by accident.
  if (!fs.existsSync(el.path)) {
    return {
      h,
      prims: [
        { kind: 'rect', x: f.x, y: f.y, w, h, fill: null, radius: 0.08,
          lineColor: ctx.accent, lineWidth: 1.25, dashed: true },
        {
          kind: 'text', x: f.x, y: f.y, w, h,
          runs: [{ text: el.alt ? `[ ${el.alt} ]` : `[ missing: ${el.path} ]`,
            size: Math.max(9, ctx.p.bodySize - 2), color: ctx.accent, bold: true }],
          size: Math.max(9, ctx.p.bodySize - 2), color: ctx.accent,
          align: 'center', valign: 'middle', font: ctx.body,
        },
      ],
      missing: el.path,
    };
  }
  return {
    h,
    prims: [{ kind: 'image', x: f.x, y: f.y, w, h, path: el.path, alt: el.alt || '' }],
  };
};

// A chat transcript. Turns alternate sides so the shape of a conversation reads
// at a glance — the point being made is usually about accumulation, not content.
ELEMENTS.chat = (el, ctx, f, P) => {
  const size = el.size || ctx.p.bodySize;
  const pad = 0.16;
  const gap = el.gap == null ? 0.09 : el.gap;
  const maxW = f.w * (el.width || 0.86);
  const b = new Box();
  let y = f.y;
  (el.rows || []).forEach((r, i) => {
    const mine = r.from === 'user' || r.from === 'you';
    const tw = maxW - pad * 2;
    const th = textHeight(r.text, tw, size, false, ctx.serif);
    const bh = th + pad * 2;
    const bw = Math.min(maxW,
      Math.max(1.2, String(r.text).length * (size / 72) * 0.55 + pad * 2));
    const x = mine ? f.x + f.w - bw : f.x;
    b.push({ kind: 'rect', x, y, w: bw, h: bh, radius: 0.14,
      fill: mine ? ctx.accent : (ctx.dark ? ctx.t.panelBar : ctx.t.fill),
      lineColor: mine ? null : ctx.rule, lineWidth: mine ? 0 : 1 });
    b.push({
      kind: 'text', x: x + pad, y: y + pad, w: bw - pad * 2, h: th,
      runs: [{ text: r.text, size, color: mine ? ctx.t.accentText : ctx.fg,
        src: P && P.concat(['rows', i, 'text']) }],
      size, color: mine ? ctx.t.accentText : ctx.fg,
      align: 'left', valign: 'top', font: ctx.body,
    });
    if (r.note) {
      // The note annotates its own bubble, so it sits under it on the same side.
      // Opposite-side placement reads as a stray label belonging to nothing.
      const nh = size / 72 * 1.25;
      b.push(txt(ctx, mine ? f.x + f.w - maxW : f.x, y + bh + 0.03, maxW, nh, r.note,
        Math.max(8, size - 4), ctx.dim, { align: mine ? 'right' : 'left',
          src: P && P.concat(['rows', i, 'note']) }));
      y += nh + 0.03;
    }
    y += bh + gap;
  });
  return { prims: b.out, h: Math.max(0, y - f.y - gap) };
};

// Rows of coloured pips. Built for showing a sequence that grows row over row.
ELEMENTS.dots = (el, ctx, f, P) => {
  const d = el.size || 0.3;
  const gap = el.gap == null ? 0.1 : el.gap;
  const rowGap = el.rowGap == null ? 0.13 : el.rowGap;
  const labelW = (el.rows || []).some((r) => r.label) ? (el.labelWidth || 1.1) : 0;
  const b = new Box();
  let y = f.y;
  (el.rows || []).forEach((row, ri) => {
    if (row.label) {
      b.push(txt(ctx, f.x, y + (d - ctx.p.bodySize / 72 * 1.1) / 2, labelW - 0.12, d,
        row.label, Math.max(9, ctx.p.bodySize - 2), ctx.dim,
        { src: P && P.concat(['rows', ri, 'label']) }));
    }
    (row.colors || []).forEach((c, ci) => {
      b.push({ kind: 'ellipse', x: f.x + labelW + ci * (d + gap), y, w: d, h: d,
        fill: color(ctx, c, ctx.accent) });
    });
    if (row.trail) {
      b.push(txt(ctx, f.x + labelW + (row.colors || []).length * (d + gap), y, 1.2, d,
        row.trail, Math.max(9, ctx.p.bodySize - 1), ctx.dim, {}));
    }
    y += d + rowGap;
  });
  return { prims: b.out, h: Math.max(0, y - f.y - rowGap) };
};

ELEMENTS.dial = (el, ctx, f, P) => {
  const labels = el.labels || [];
  const nT = Math.max(2, labels.length);
  const active = Math.max(0, Math.min(nT - 1, el.active == null ? 0 : el.active));
  const knobD = el.size || 1.5;
  const knobR = knobD / 2;
  const tickR = knobR + 0.2;
  const size = Math.max(9, ctx.p.bodySize - 2);
  const labelH = size / 72 * 1.4;
  const cx = f.x + f.w / 2;
  const cy = f.y + tickR + labelH + 0.06;
  const b = new Box();
  // 240 degrees of travel, lower-left round through the top to lower-right.
  const ang = (i) => (210 - i * (240 / (nT - 1))) * Math.PI / 180;

  b.push({ kind: 'ellipse', x: cx - knobR, y: cy - knobR, w: knobD, h: knobD,
    fill: ctx.dark ? ctx.t.panelBar : ctx.t.fill,
    lineColor: ctx.rule, lineWidth: 1.5 });
  b.push({ kind: 'ellipse', x: cx - knobR * 0.58, y: cy - knobR * 0.58,
    w: knobR * 1.16, h: knobR * 1.16, fill: ctx.accent });

  labels.forEach((lab, i) => {
    const a = ang(i);
    const td = i === active ? 0.13 : 0.09;
    b.push({ kind: 'ellipse',
      x: cx + tickR * Math.cos(a) - td / 2, y: cy - tickR * Math.sin(a) - td / 2,
      w: td, h: td, fill: i === active ? ctx.accent : ctx.rule });
    if (!el.labelAll && i !== active) return;
    // Radial placement: a label sits outside its own tick, pushed away from the
    // knob along the angle it belongs to, so the whole scale stays readable.
    const lw = el.labelWidth || 1.0;
    const lr = tickR + 0.12;
    const sn = Math.sin(a);
    const cs = Math.cos(a);
    const lx = cx + lr * cs - lw / 2 + (Math.abs(cs) > 0.3 ? Math.sign(cs) * lw / 2 : 0);
    const ly = cy - lr * sn - (sn > 0.3 ? labelH : (sn < -0.3 ? 0 : labelH / 2));
    b.push(txt(ctx, lx, ly, lw, labelH, lab, size,
      i === active ? ctx.accent : ctx.dim,
      { bold: i === active,
        align: Math.abs(cs) > 0.3 ? (cs > 0 ? 'left' : 'right') : 'center',
        src: P && P.concat(['labels', i]) }));
  });

  // Pointer: a dot on the knob face at the selected angle.
  const pa = ang(active);
  const pd = 0.13;
  b.push({ kind: 'ellipse',
    x: cx + knobR * 0.68 * Math.cos(pa) - pd / 2,
    y: cy - knobR * 0.68 * Math.sin(pa) - pd / 2,
    w: pd, h: pd, fill: ctx.t.accentText });

  let bottom = cy + tickR + (el.labelAll ? labelH + 0.16 : 0.1);
  if (el.caption) {
    const ch = textHeight(el.caption, f.w, size, false, ctx.serif);
    b.push(txt(ctx, f.x, bottom + 0.06, f.w, ch, el.caption, size, ctx.dim,
      { align: 'center', mono: !!el.captionMono, src: P && P.concat(['caption']) }));
    bottom += ch + 0.06;
  }
  return { prims: b.out, h: bottom - f.y };
};

// Mixes two hex colours. Used to build a ramp from one accent so a segmented
// bar reads as one scale rather than a set of unrelated colours.
function blend(a, b, t) {
  const pa = [0, 2, 4].map((i) => parseInt(String(a).slice(i, i + 2), 16));
  const pb = [0, 2, 4].map((i) => parseInt(String(b).slice(i, i + 2), 16));
  return pa.map((v, i) => Math.round(v + (pb[i] - v) * t).toString(16)
    .padStart(2, '0')).join('').toUpperCase();
}

// A proportional bar of labelled segments, with the unused remainder drawn as an
// empty tail. Built for showing something filling up.
ELEMENTS.bar = (el, ctx, f, P) => {
  const segs = el.segments || [];
  const rem = el.remainder || 0;
  const total = segs.reduce((a, sg) => a + (sg.size || 1), 0) + rem;
  if (!total) throw new Error('A `bar` needs segments with a size.');
  const barH = el.h || 0.46;
  const size = Math.max(9, ctx.p.bodySize - 2);
  const lineH = size / 72 * 1.35;
  const b = new Box();

  // Group captions sit above the span of segments they cover.
  const groups = [];
  let acc = 0;
  segs.forEach((sg) => {
    if (sg.group) groups.push({ label: sg.group, start: acc });
    acc += sg.size || 1;
  });
  const groupH = groups.length ? lineH + 0.1 : 0;
  groups.forEach((g, i) => {
    const gx = f.x + f.w * (g.start / total);
    const end = i + 1 < groups.length
      ? f.x + f.w * (groups[i + 1].start / total) : f.x + f.w;
    b.push(txt(ctx, gx, f.y, Math.max(0.6, end - gx - 0.1), lineH, g.label,
      size, ctx.accent, { bold: true }));
  });

  const y = f.y + groupH;
  let x = f.x;
  segs.forEach((sg, i) => {
    const w = f.w * ((sg.size || 1) / total);
    // Ramp from a light tint to the full accent so the bar reads left to right.
    const t = segs.length > 1 ? i / (segs.length - 1) : 1;
    b.push({ kind: 'rect', x, y, w: Math.max(0.02, w - 0.02), h: barH,
      fill: sg.c ? color(ctx, sg.c, ctx.accent) : blend(ctx.t.tint, ctx.accent, 0.25 + t * 0.75),
      radius: 0.04 });
    x += w;
  });
  if (rem) {
    b.push({ kind: 'rect', x, y, w: f.x + f.w - x, h: barH, radius: 0.04,
      fill: ctx.dark ? ctx.t.panelBar : ctx.t.fill,
      lineColor: ctx.rule, lineWidth: 1 });
    if (el.remainderLabel) {
      b.push(txt(ctx, x, y, f.x + f.w - x, barH, el.remainderLabel, size, ctx.dim,
        { align: 'center', src: P && P.concat(['remainderLabel']) }));
    }
  }

  // Segments are too narrow for inside labels, so the key runs underneath.
  let ly = y + barH + 0.14;
  let lx = f.x;
  const sw = 0.13;
  segs.forEach((sg, i) => {
    const tw = String(sg.label || '').length * (size / 72) * 0.55;
    const itemW = sw + 0.08 + tw + 0.26;
    if (lx + itemW > f.x + f.w && lx > f.x) { lx = f.x; ly += lineH + 0.08; }
    const t = segs.length > 1 ? i / (segs.length - 1) : 1;
    b.push({ kind: 'rect', x: lx, y: ly + (lineH - sw) / 2, w: sw, h: sw, radius: 0.02,
      fill: sg.c ? color(ctx, sg.c, ctx.accent) : blend(ctx.t.tint, ctx.accent, 0.25 + t * 0.75) });
    b.push(txt(ctx, lx + sw + 0.08, ly, tw + 0.1, lineH, sg.label || '', size, ctx.dim,
      { src: P && P.concat(['segments', i, 'label']) }));
    lx += itemW;
  });

  return { prims: b.out, h: (ly + lineH) - f.y };
};

// A horizontal sequence with labelled stops. Good for "what happens when".
ELEMENTS.timeline = (el, ctx, f, P) => {
  const items = el.items || [];
  const size = ctx.p.bodySize;
  const d = 0.26;
  const n = Math.max(1, items.length);
  const colW = Math.min(f.w / n * 1.5, 2.7);
  // Stops are inset by half a label so the first and last dots sit under the
  // centre of their own labels instead of being clamped away from them.
  const inset = items.length > 1 ? Math.min(colW / 2, f.w / 2) : 0;
  const span = f.w - inset * 2;
  const step = items.length > 1 ? span / (n - 1 + 0.0001) : f.w;
  const headH = textHeight('X', f.w / n, size, false, ctx.serif);
  const lineY = headH + 0.34;
  const b = new Box();
  b.push({ kind: 'line', x: f.x, y: f.y + lineY, w: f.w, color: ctx.rule, thickness: 2 });
  items.forEach((it, i) => {
    const cx = items.length > 1 ? f.x + inset + i * step : f.x + f.w / 2;
    const tx = Math.max(f.x, Math.min(f.x + f.w - colW, cx - colW / 2));
    b.push(txt(ctx, tx, f.y, colW, headH, it.label || '', size, ctx.fg,
      { bold: true, align: 'center', src: P && P.concat(['items', i, 'label']) }));
    b.push({ kind: 'ellipse', x: cx - d / 2, y: f.y + lineY - d / 2 + 0.01, w: d, h: d,
      fill: ctx.accent });
    if (it.sub) {
      const sh = textHeight(it.sub, colW, size - 2, false, ctx.serif);
      b.push(txt(ctx, tx, f.y + lineY + 0.24, colW, sh, it.sub, size - 2, ctx.dim,
        { align: 'center', src: P && P.concat(['items', i, 'sub']) }));
    }
  });
  const subH = items.some((i) => i.sub)
    ? textHeight('X', 2, size - 2, false, ctx.serif) + 0.24 : 0.1;
  return { prims: b.out, h: lineY + subH + 0.18 };
};

ELEMENTS.columns = (el, ctx, f, P) => {
  const items = el.items || [];
  const gap = el.gap == null ? 0.34 : el.gap;
  const widths = el.widths && el.widths.length === items.length
    ? el.widths
    : new Array(items.length).fill(1 / Math.max(1, items.length));
  const total = widths.reduce((a, x) => a + x, 0);
  const avail = f.w - gap * (items.length - 1);
  const b = new Box();
  let x = f.x;
  let h = 0;
  items.forEach((colElements, i) => {
    const cw = avail * (widths[i] / total);
    const r = flow(colElements || [], ctx, { x, y: f.y, w: cw }, P && P.concat(['items', i]));
    b.concat(r.prims);
    h = Math.max(h, r.h);
    x += cw + gap;
  });
  return { prims: b.out, h };
};

// -------------------------------------------------------------------- flow

// `base` is the spec path of the array these elements live in, so the path of
// element i is base.concat([i]). Columns pass their own items array, which is
// what lets a nested element resolve to a real field instead of a stray path.
function flow(elements, ctx, frame, base) {
  const b = new Box();
  const P = base || null;
  let y = frame.y;
  let last = 0;
  elements.forEach((el, i) => {
    if (!el || typeof el !== 'object') {
      throw new Error(`Element ${i + 1} must be an object with a "type", got: ${JSON.stringify(el)}`);
    }
    const handler = ELEMENTS[el.type];
    if (!handler) {
      throw new Error(
        `Unknown element type "${el.type}". Available: ${Object.keys(ELEMENTS).sort().join(', ')}`);
    }
    const path = P && P.concat([i]);
    const indent = el.indent || 0;
    if (el.at) {
      // Absolute placement opts out of the flow entirely.
      const r = handler(el, ctx, { x: el.at.x, y: el.at.y, w: el.at.w == null ? frame.w : el.at.w }, path);
      b.concat(r.prims);
      return;
    }
    const r = handler(el, ctx, { x: frame.x + indent, y, w: frame.w - indent }, path);
    b.concat(r.prims);
    last = el.gap == null ? ctx.p.elementGap : el.gap;
    y += r.h + last;
  });
  return { prims: b.out, h: Math.max(0, y - frame.y - last) };
}

// ------------------------------------------------------------------- slide

function layoutSlide(slide, design, index, basedir) {
  const ctx = makeCtx(design, slide, basedir);
  const { p } = design;
  const b = new Box();
  const margin = slide.margin == null ? p.margin : slide.margin;
  const contentTop = slide.contentTop == null ? p.contentTop : slide.contentTop;
  const w = PAGE_W - margin * 2;
  let y = contentTop;

  b.push({ kind: 'rect', x: 0, y: 0, w: PAGE_W, h: PAGE_H, fill: bgColor(slide, design.t), background: true });

  if (slide.kicker) {
    const kh = p.kickerSize / 72 * 1.5;
    b.push({
      kind: 'text', x: margin, y, w, h: kh,
      runs: [{ text: String(slide.kicker).toUpperCase(), size: p.kickerSize, bold: true,
        color: ctx.accent, letterSpacing: 0.08, src: [index, 'kicker'] }],
      size: p.kickerSize, color: ctx.accent, align: 'left', valign: 'top', font: ctx.body,
      letterSpacing: 0.08,
    });
    y += kh + 0.06;
    if (p.kickerRule) {
      b.push({ kind: 'line', x: margin, y, w: 1.1, color: ctx.accent, thickness: 2 });
      y += 0.16;
    }
  }

  if (slide.title) {
    const t = typeof slide.title === 'string' ? { text: slide.title } : slide.title;
    const size = t.size || p.titleSize;
    const tw = t.w || w;
    const lines = t.lines || [{ text: t.text, color: t.color }];
    lines.forEach((ln, li) => {
      const lh = textHeight(ln.text, tw, size, false, ctx.serif);
      b.push({
        kind: 'text', x: margin, y, w: tw, h: lh,
        runs: [{ text: ln.text, size, bold: p.titleWeight,
          color: color(ctx, ln.color || t.color, ctx.fg),
          src: typeof slide.title === 'string'
            ? [index, 'title']
            : (t.lines ? [index, 'title', 'lines', li, 'text'] : [index, 'title', 'text']) }],
        size, color: ctx.fg, align: t.align || 'left', valign: 'top', font: ctx.body,
      });
      y += lh;
    });
    y += slide.gapAfterTitle == null ? p.gapAfterTitle : slide.gapAfterTitle;
  }

  if (slide.subtitle) {
    const sw = slide.subtitleWidth || Math.min(w, 9.2);
    const sh = textHeight(slide.subtitle, sw, p.subtitleSize, false, ctx.serif);
    b.push(txt(ctx, margin, y, sw, sh, slide.subtitle, p.subtitleSize, ctx.dim, { src: [index, 'subtitle'] }));
    y += sh + 0.26;
  }

  const localCtx = Object.assign({}, ctx, {
    p: Object.assign({}, p, slide.elementGap == null ? {} : { elementGap: slide.elementGap }),
  });
  const body = flow(slide.elements || [], localCtx, { x: margin, y, w }, [index, 'elements']);
  b.concat(body.prims);

  let contentBottom = b.out
    .filter((prim) => !prim.background)
    .reduce((m, prim) => Math.max(m, prim.y + (prim.h || 0)), 0);

  // Optical centring. A slide whose content stops two inches short of the bottom
  // reads as unfinished rather than airy, so the whole composition — kicker,
  // title and body together, never the body alone — slides down to sit in the
  // middle of the page. Dense slides shift by nothing and are unaffected.
  const vcenter = slide.vcenter == null
    ? (design.vcenter == null ? p.vcenter : design.vcenter)
    : slide.vcenter;
  if (vcenter && contentBottom < SAFE_BOTTOM) {
    const shift = (SAFE_BOTTOM - contentBottom) / 2;
    if (shift > 0.15) {
      for (const prim of b.out) {
        if (!prim.background) prim.y += shift;
      }
      contentBottom += shift;
    }
  }

  return {
    index,
    prims: b.out,
    dark: ctx.dark,
    bg: bgColor(slide, design.t),
    notes: slide.notes || '',
    title: typeof slide.title === 'string'
      ? slide.title
      : (slide.title && (slide.title.text
          || (slide.title.lines || []).map((l) => l.text).join(' '))) || `Slide ${index + 1}`,
    overflow: contentBottom > SAFE_BOTTOM ? Number((contentBottom - SAFE_BOTTOM).toFixed(2)) : 0,
    contentBottom: Number(contentBottom.toFixed(2)),
  };
}

function layoutDeck(spec) {
  if (!spec || !Array.isArray(spec.slides)) {
    throw new Error('Spec must have a top-level "slides:" list.');
  }
  const design = resolveDesign(spec.design);
  const slides = spec.slides.map((s, i) => {
    try {
      return layoutSlide(s || {}, design, i, spec.basedir);
    } catch (err) {
      // Without the slide number, a vocabulary typo in a 30-slide deck is a
      // hunt. With it, it is a one-line fix.
      err.message = `Slide ${i + 1}${s && s.title ? ` ("${typeof s.title === 'string' ? s.title : s.title.text || ''}")` : ''}: ${err.message}`;
      throw err;
    }
  });
  return { meta: spec.meta || {}, design, slides, page: { w: PAGE_W, h: PAGE_H } };
}

module.exports = {
  layoutDeck, layoutSlide, flow, ELEMENTS, GLYPHS,
  PAGE_W, PAGE_H, SAFE_BOTTOM, textHeight, glyphFor,
};
