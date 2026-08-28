#!/usr/bin/env node
// Compare computed styles on a rendered page against design-spec.json tokens.
import { readFileSync } from 'node:fs';
import { chromium } from 'playwright';
import { parseArgs, fail, toUrl, NO_MOTION_CSS } from './lib.mjs';

const args = parseArgs(process.argv.slice(2), {
  help: `tokens.mjs --page <file|url> --spec <design-spec.json> [--px-tolerance 1]
Spec shape: {"viewport":{"width":W,"height":H},"tokens":[{"selector":"h1","property":"color","expected":"#1a1a1a"}, ...]}
Prints JSON {checked, mismatches:[{selector,property,expected,actual}]}. Exit 0 when all match, 2 when any mismatch, 5 when a selector matches nothing.`,
  options: ['page', 'spec', 'px-tolerance'], flags: [], required: ['page', 'spec'], defaults: { 'px-tolerance': '1' },
});

let spec;
try { spec = JSON.parse(readFileSync(args.spec, 'utf8')); } catch (e) { fail(`Cannot parse spec ${args.spec}: ${e.message}`); }
if (!spec.viewport?.width || !spec.viewport?.height || !Array.isArray(spec.tokens))
  fail('Spec needs viewport.width, viewport.height, and a tokens array.');

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
  const missing = spec.tokens.filter((t, i) => actuals[i] === null).map(t => t.selector);
  if (missing.length) fail(`Selectors matched nothing: ${[...new Set(missing)].join(', ')}. Fix the selector in the spec or add the element.`, 5);
  const tol = Number(args['px-tolerance']);
  const mismatches = spec.tokens.map((t, i) => ({ ...t, actual: actuals[i].trim() })).filter(t => !same(t.expected, t.actual, tol));
  console.log(JSON.stringify({ checked: spec.tokens.length, mismatches }, null, 1));
  process.exit(mismatches.length ? 2 : 0);
} finally { await browser.close(); }
