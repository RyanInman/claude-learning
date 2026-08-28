#!/usr/bin/env node
// Pixel-diff two PNGs. Writes a heatmap and prints JSON {diffPercent, mismatched, width, height}.
import { readFileSync, writeFileSync } from 'node:fs';
import { PNG } from 'pngjs';
import pixelmatch from 'pixelmatch';
import { parseArgs, fail } from './lib.mjs';

const args = parseArgs(process.argv.slice(2), {
  help: `diff.mjs --design <png> --actual <png> --out <heatmap.png> [--sensitivity 0.03]
Exit 0 always on a completed diff; exit 4 when dimensions differ (message names both sizes).`,
  options: ['design', 'actual', 'out', 'sensitivity'], flags: [], required: ['design', 'actual', 'out'], defaults: { sensitivity: '0.03' },
});

const load = p => { try { return PNG.sync.read(readFileSync(p)); } catch (e) { fail(`Cannot read PNG ${p}: ${e.message}`); } };
const a = load(args.design), b = load(args.actual);
if (a.width !== b.width || a.height !== b.height)
  fail(`Dimension mismatch: design ${a.width}x${a.height}, actual ${b.width}x${b.height}. Capture at the design's size.`, 4);

const out = new PNG({ width: a.width, height: a.height });
const mismatched = pixelmatch(a.data, b.data, out.data, a.width, a.height, { threshold: Number(args.sensitivity), includeAA: false });
writeFileSync(args.out, PNG.sync.write(out));
const diffPercent = +(100 * mismatched / (a.width * a.height)).toFixed(2);
console.log(JSON.stringify({ diffPercent, mismatched, width: a.width, height: a.height, heatmap: args.out }));
