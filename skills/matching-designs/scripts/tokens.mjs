#!/usr/bin/env node
// Compare a rendered page against design-spec.json: computed-style tokens, element
// geometry (boxes), and font availability. Geometry catches a shifted or mis-sized
// block, which a color-only spec reports as a perfect match.
import { readFileSync } from 'node:fs';
import { chromium } from 'playwright';
import { parseArgs, fail, toUrl, NO_MOTION_CSS } from './lib.mjs';

const args = parseArgs(process.argv.slice(2), {
  help: `tokens.mjs --page <file|url> --spec <design-spec.json> [--px-tolerance 1] [--box-tolerance 4]
Spec shape: {"viewport":{"width":W,"height":H},
             "tokens":[{"selector":"h1","property":"color","expected":"#1a1a1a"}],
             "boxes":[{"selector":".modal","x":248,"y":40,"width":820,"height":500,"tolerance":4}],
             "fonts":["Inter"]}
Boxes compare getBoundingClientRect against the design's measured rect. Omit any of x/y/width/height to skip it.
Fonts fail when the family is not actually loaded, because a silent fallback shifts every line.
Prints JSON {checked, mismatches:[{selector,property,expected,actual}]}. Exit 0 all match, 2 any mismatch, 5 a selector matched nothing.`,
  options: ['page', 'spec', 'px-tolerance', 'box-tolerance'], flags: [], required: ['page', 'spec'],
  defaults: { 'px-tolerance': '1', 'box-tolerance': '4' },
});

let spec;
try { spec = JSON.parse(readFileSync(args.spec, 'utf8')); } catch (e) { fail(`Cannot parse spec ${args.spec}: ${e.message}`); }
if (!spec.viewport?.width || !spec.viewport?.height || !Array.isArray(spec.tokens))
  fail('Spec needs viewport.width, viewport.height, and a tokens array.');
const boxes = spec.boxes ?? [];
if (!Array.isArray(boxes)) fail('spec.boxes must be an array.');
const fonts = spec.fonts ?? [];

const hexToRgb = h => { const s = h.replace('#', ''); const f = s.length === 3 ? s.split('').map(c => c + c).join('') : s; return [0, 2, 4].map(i => parseInt(f.slice(i, i + 2), 16)); };
const rgbOf = s => { const m = s.match(/rgba?\(([^)]+)\)/); const c = m ? m[1].split(',').map(Number) : /^#/.test(s) ? hexToRgb(s) : null; return c && c.length === 3 ? [...c, 1] : c; };
const pxOf = s => { const m = String(s).match(/^(-?[\d.]+)px$/); return m ? Number(m[1]) : null; };

function same(expected, actual, tol) {
  const er = rgbOf(expected), ar = rgbOf(actual);
  if (er && ar) return er.every((v, i) => v === ar[i]);
  const ep = pxOf(expected), ap = pxOf(actual);
  if (ep !== null && ap !== null) return Math.abs(ep - ap) <= tol;
  return String(expected).trim().toLowerCase() === String(actual).trim().toLowerCase();
}

const browser = await chromium.launch();
try {
  const page = await browser.newPage({ viewport: spec.viewport, deviceScaleFactor: 1 });
  await page.goto(toUrl(args.page), { waitUntil: 'networkidle' }).catch(e => fail(`Page load failed: ${e.message}`, 3));
  await page.addStyleTag({ content: NO_MOTION_CSS });
  await page.evaluate(() => document.fonts.ready);

  const actuals = await page.evaluate(tokens => tokens.map(t => {
    const el = document.querySelector(t.selector);
    return el ? getComputedStyle(el).getPropertyValue(t.property) : null;
  }), spec.tokens);
  const rects = await page.evaluate(sel => sel.map(s => {
    const el = document.querySelector(s);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return { x: r.left, y: r.top, width: r.width, height: r.height };
  }), boxes.map(b => b.selector));
  const missingFonts = await page.evaluate(list => list.filter(f => !document.fonts.check(`16px "${f}"`)), fonts);

  const missing = [...spec.tokens.filter((t, i) => actuals[i] === null).map(t => t.selector),
                   ...boxes.filter((b, i) => rects[i] === null).map(b => b.selector)];
  if (missing.length) fail(`Selectors matched nothing: ${[...new Set(missing)].join(', ')}. Fix the selector in the spec or add the element.`, 5);

  const tol = Number(args['px-tolerance']);
  const boxTol = Number(args['box-tolerance']);
  const mismatches = spec.tokens
    .map((t, i) => ({ selector: t.selector, property: t.property, expected: t.expected, actual: actuals[i].trim() }))
    .filter(t => !same(t.expected, t.actual, tol));

  boxes.forEach((b, i) => {
    const t = b.tolerance !== undefined ? Number(b.tolerance) : boxTol;
    for (const side of ['x', 'y', 'width', 'height']) {
      if (b[side] === undefined) continue;
      const actual = Math.round(rects[i][side] * 100) / 100;
      if (Math.abs(actual - Number(b[side])) > t)
        mismatches.push({ selector: b.selector, property: `box-${side}`, expected: `${b[side]}px`, actual: `${actual}px` });
    }
  });

  for (const f of missingFonts)
    mismatches.push({ selector: 'document', property: 'font-loaded', expected: f, actual: 'not loaded (fallback in use)' });

  console.log(JSON.stringify({ checked: spec.tokens.length + boxes.length + fonts.length, mismatches }, null, 1));
  process.exit(mismatches.length ? 2 : 0);
} finally { await browser.close(); }
