#!/usr/bin/env node
// Crops a PNG to a pixel rect, with an optional color-key matte to transparency.
// Use it to strip browser chrome from a screenshotted design, or to lift a photo
// straight out of the design image when no source asset exists.
import { readFileSync, writeFileSync } from 'node:fs';
import { PNG } from 'pngjs';
import { parseArgs, fail } from './lib.mjs';

const args = parseArgs(process.argv.slice(2), {
  help: `crop.mjs --src <png> --out <png> --x <n> --y <n> --width <n> --height <n> [--matte RRGGBB] [--tolerance 20]
Crops [x, y, x+width, y+height] out of --src. With --matte, any pixel in the crop within
--tolerance of that hex color gets alpha 0, so a lifted photo blends into any background
instead of carrying a visible seam of the design's own background color.`,
  options: ['src', 'out', 'x', 'y', 'width', 'height', 'matte', 'tolerance'],
  flags: [],
  required: ['src', 'out', 'x', 'y', 'width', 'height'],
  defaults: { tolerance: '20' },
});

const src = (() => { try { return PNG.sync.read(readFileSync(args.src)); } catch (e) { fail(`Cannot read PNG ${args.src}: ${e.message}`); } })();
const x = Number(args.x), y = Number(args.y), w = Number(args.width), h = Number(args.height);
if (x < 0 || y < 0 || x + w > src.width || y + h > src.height)
  fail(`Crop rect [${x},${y},${x + w},${y + h}] falls outside the source image (${src.width}x${src.height}).`);

const out = new PNG({ width: w, height: h });
PNG.bitblt(src, out, x, y, w, h, 0, 0);

if (args.matte) {
  const m = args.matte.match(/^#?([0-9a-f]{6})$/i);
  if (!m) fail(`--matte must be 6 hex digits, e.g. efd455. Got "${args.matte}".`);
  const mr = parseInt(m[1].slice(0, 2), 16), mg = parseInt(m[1].slice(2, 4), 16), mb = parseInt(m[1].slice(4, 6), 16);
  const tol = Number(args.tolerance);
  for (let i = 0; i < out.data.length; i += 4) {
    const r = out.data[i], g = out.data[i + 1], b = out.data[i + 2];
    if (Math.abs(r - mr) <= tol && Math.abs(g - mg) <= tol && Math.abs(b - mb) <= tol) out.data[i + 3] = 0;
  }
}

writeFileSync(args.out, PNG.sync.write(out));
console.log(JSON.stringify({ out: args.out, width: w, height: h, matted: !!args.matte }));
