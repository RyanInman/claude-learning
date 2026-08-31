#!/usr/bin/env node
// Pixel-diff two PNGs. Writes a heatmap and prints JSON with an overall percent,
// an optional masked percent (text excluded), per-region percents, and the worst grid cells.
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { PNG } from 'pngjs';
import pixelmatch from 'pixelmatch';
import { parseArgs, fail } from './lib.mjs';

const args = parseArgs(process.argv.slice(2), {
  help: `diff.mjs --design <png> --actual <png> --out <heatmap.png> [--sensitivity 0.03]
                 [--mask <rects.json|json>] [--regions <rects.json|json>] [--grid 8]
Rect shape: [{"label":"hero","x":0,"y":0,"width":100,"height":40}, ...] (label optional for --mask).
--mask excludes those rects from the percent, so text can be subtracted to expose layout error alone.
--regions reports a percent inside each rect, so the report names the worst element instead of a color.
--grid N splits the image into NxN cells and lists the five worst.
Exit 0 always on a completed diff; exit 4 when dimensions differ (message names both sizes).`,
  options: ['design', 'actual', 'out', 'sensitivity', 'mask', 'regions', 'grid'], flags: [],
  required: ['design', 'actual', 'out'], defaults: { sensitivity: '0.03' },
});

const load = p => { try { return PNG.sync.read(readFileSync(p)); } catch (e) { fail(`Cannot read PNG ${p}: ${e.message}`); } };
const rects = (v, what) => {
  if (v === undefined) return [];
  const raw = existsSync(v) ? readFileSync(v, 'utf8') : v;
  let parsed;
  try { parsed = JSON.parse(raw); } catch (e) { fail(`--${what} must be a JSON rect array or a path to one. ${e.message}`); }
  if (!Array.isArray(parsed)) fail(`--${what} must be a JSON array of rects.`);
  return parsed;
};

const a = load(args.design), b = load(args.actual);
if (a.width !== b.width || a.height !== b.height)
  fail(`Dimension mismatch: design ${a.width}x${a.height}, actual ${b.width}x${b.height}. Capture at the design's size.`, 4);

const out = new PNG({ width: a.width, height: a.height });
const mismatched = pixelmatch(a.data, b.data, out.data, a.width, a.height, { threshold: Number(args.sensitivity), includeAA: false });
writeFileSync(args.out, PNG.sync.write(out));

// pixelmatch paints a counted difference pure red; anti-aliased pixels yellow; unchanged pixels gray.
const isDiff = idx => out.data[idx] === 255 && out.data[idx + 1] === 0 && out.data[idx + 2] === 0;
const clamp = (v, hi) => Math.max(0, Math.min(hi, Math.round(v)));
const countIn = r => {
  const x0 = clamp(r.x, a.width), y0 = clamp(r.y, a.height);
  const x1 = clamp(r.x + r.width, a.width), y1 = clamp(r.y + r.height, a.height);
  let n = 0;
  for (let y = y0; y < y1; y++) for (let x = x0; x < x1; x++) if (isDiff((a.width * y + x) << 2)) n++;
  return { n, area: Math.max(0, (x1 - x0) * (y1 - y0)) };
};
const pct = (n, area) => area ? +(100 * n / area).toFixed(2) : 0;

const total = a.width * a.height;
const report = { diffPercent: pct(mismatched, total), mismatched, width: a.width, height: a.height, heatmap: args.out };

const maskRects = rects(args.mask, 'mask');
if (maskRects.length) {
  // Paint a coverage map first, because overlapping text rects would otherwise double-count.
  const covered = new Uint8Array(total);
  for (const r of maskRects) {
    const x0 = clamp(r.x, a.width), y0 = clamp(r.y, a.height);
    const x1 = clamp(r.x + r.width, a.width), y1 = clamp(r.y + r.height, a.height);
    for (let y = y0; y < y1; y++) for (let x = x0; x < x1; x++) covered[a.width * y + x] = 1;
  }
  let maskArea = 0, maskedDiff = 0;
  for (let i = 0; i < total; i++) {
    if (covered[i]) { maskArea++; if (isDiff(i << 2)) maskedDiff++; }
  }
  const openArea = total - maskArea;
  report.layoutDiff = pct(mismatched - maskedDiff, openArea);
  report.textDiff = pct(maskedDiff, maskArea);
  report.maskedArea = maskArea;
}

const regionRects = rects(args.regions, 'regions');
if (regionRects.length) {
  report.regions = regionRects.map((r, i) => {
    const { n, area } = countIn(r);
    return { label: r.label || `region-${i + 1}`, percent: pct(n, area), mismatched: n, x: r.x, y: r.y, width: r.width, height: r.height };
  }).sort((p, q) => q.percent - p.percent);
}

if (args.grid) {
  const g = Number(args.grid);
  if (!(g > 0)) fail(`--grid must be a positive integer. Got "${args.grid}".`);
  const cw = a.width / g, ch = a.height / g, cells = [];
  for (let gy = 0; gy < g; gy++) for (let gx = 0; gx < g; gx++) {
    const r = { x: gx * cw, y: gy * ch, width: cw, height: ch };
    const { n, area } = countIn(r);
    if (n) cells.push({ x: clamp(r.x, a.width), y: clamp(r.y, a.height), width: Math.round(cw), height: Math.round(ch), percent: pct(n, area) });
  }
  report.gridTop = cells.sort((p, q) => q.percent - p.percent).slice(0, 5);
}

console.log(JSON.stringify(report));
