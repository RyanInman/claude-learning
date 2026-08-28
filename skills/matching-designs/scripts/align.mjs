#!/usr/bin/env node
// Bounding-box aligner. Finds the pixel bbox of a target color in two PNGs and
// prints the delta, so a large element gets one measured move instead of guessed shifts.
import { readFileSync } from 'node:fs';
import { PNG } from 'pngjs';
import { parseArgs, fail } from './lib.mjs';

const args = parseArgs(process.argv.slice(2), {
  help: `align.mjs --design <png> --actual <png> --rgb RRGGBB [--tolerance 12] [--x0 0] [--x1 width] [--y0 0] [--y1 height]
Finds every pixel within --tolerance of --rgb in both images and prints each bbox plus
the delta (design minus actual) to shift the actual element onto the design position.
Bound the search with --x0/--x1/--y0/--y1 when other elements share the color (e.g. white text
elsewhere on the page), because an unbounded scan mixes bboxes from unrelated regions.`,
  options: ['design', 'actual', 'rgb', 'tolerance', 'x0', 'x1', 'y0', 'y1'],
  flags: [],
  required: ['design', 'actual', 'rgb'],
  defaults: { tolerance: '12' },
});

const load = p => { try { return PNG.sync.read(readFileSync(p)); } catch (e) { fail(`Cannot read PNG ${p}: ${e.message}`); } };
const target = args.rgb.match(/^#?([0-9a-f]{6})$/i);
if (!target) fail(`--rgb must be 6 hex digits, e.g. ffffff. Got "${args.rgb}".`);
const tr = parseInt(target[1].slice(0, 2), 16), tg = parseInt(target[1].slice(2, 4), 16), tb = parseInt(target[1].slice(4, 6), 16);
const tol = Number(args.tolerance);

function bbox(img) {
  const x0 = args.x0 !== undefined ? Number(args.x0) : 0;
  const x1 = args.x1 !== undefined ? Number(args.x1) : img.width;
  const y0 = args.y0 !== undefined ? Number(args.y0) : 0;
  const y1 = args.y1 !== undefined ? Number(args.y1) : img.height;
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity, count = 0;
  for (let y = y0; y < y1; y++) {
    for (let x = x0; x < x1; x++) {
      const idx = (img.width * y + x) << 2;
      const r = img.data[idx], g = img.data[idx + 1], b = img.data[idx + 2];
      if (Math.abs(r - tr) <= tol && Math.abs(g - tg) <= tol && Math.abs(b - tb) <= tol) {
        if (x < minX) minX = x; if (x > maxX) maxX = x;
        if (y < minY) minY = y; if (y > maxY) maxY = y;
        count++;
      }
    }
  }
  if (count === 0) return null;
  return { minX, maxX, minY, maxY, width: maxX - minX, height: maxY - minY, pixels: count };
}

const design = bbox(load(args.design));
const actual = bbox(load(args.actual));
if (!design) fail(`No pixel within --tolerance ${tol} of #${target[1]} found in the design image inside the given bounds.`, 5);
if (!actual) fail(`No pixel within --tolerance ${tol} of #${target[1]} found in the actual screenshot inside the given bounds.`, 5);

console.log(JSON.stringify({
  design, actual,
  deltaX: design.minX - actual.minX,
  deltaY: design.minY - actual.minY,
  widthRatio: +(design.width / actual.width).toFixed(4),
  heightRatio: +(design.height / actual.height).toFixed(4),
}, null, 1));
