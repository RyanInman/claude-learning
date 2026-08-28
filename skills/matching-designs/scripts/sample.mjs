#!/usr/bin/env node
// Point-color sampler and edge scanner. Use it to read exact hex values and find
// element boundaries before writing design-spec.json, instead of hand-rolling
// inline pixel-scan scripts per session.
import { readFileSync } from 'node:fs';
import { PNG } from 'pngjs';
import { parseArgs, fail } from './lib.mjs';

const args = parseArgs(process.argv.slice(2), {
  help: `sample.mjs --src <png> --points "[[label,x,y],...]"
  sample.mjs --src <png> --scan row --at <y> [--x0 0] [--x1 width]
  sample.mjs --src <png> --scan col --at <x> [--y0 0] [--y1 height]

Point mode prints the hex color at each [label, x, y]. Scan mode walks one row or
column and prints every x (or y) where the pixel crosses between "light" (rgb all
> 245, i.e. near-white/background) and "other", so element edges show up as a short
list of transitions instead of a wall of per-pixel output.`,
  options: ['src', 'points', 'scan', 'at', 'x0', 'x1', 'y0', 'y1'],
  flags: [],
  required: ['src'],
  defaults: {},
});

const img = (() => { try { return PNG.sync.read(readFileSync(args.src)); } catch (e) { fail(`Cannot read PNG ${args.src}: ${e.message}`); } })();
const px = (x, y) => {
  const idx = (img.width * y + x) << 2;
  return [img.data[idx], img.data[idx + 1], img.data[idx + 2]];
};
const toHex = ([r, g, b]) => '#' + [r, g, b].map(v => v.toString(16).padStart(2, '0')).join('');
const isLight = ([r, g, b]) => r > 245 && g > 245 && b > 245;

if (args.points) {
  let pts;
  try { pts = JSON.parse(args.points); } catch (e) { fail(`--points must be JSON, e.g. '[["btn-bg",100,40]]'. ${e.message}`); }
  for (const [label, x, y] of pts) {
    if (x < 0 || y < 0 || x >= img.width || y >= img.height) fail(`Point "${label}" at (${x},${y}) is outside the image (${img.width}x${img.height}).`);
    console.log(label, toHex(px(x, y)));
  }
} else if (args.scan) {
  if (args.at === undefined) fail(`--scan requires --at <coordinate>.`);
  const at = Number(args.at);
  const transitions = [];
  let prev = null;
  if (args.scan === 'row') {
    const x0 = args.x0 !== undefined ? Number(args.x0) : 0;
    const x1 = args.x1 !== undefined ? Number(args.x1) : img.width;
    for (let x = x0; x < x1; x++) {
      const light = isLight(px(x, at));
      if (prev !== null && prev !== light) transitions.push({ x, to: light ? 'light' : 'other' });
      prev = light;
    }
  } else if (args.scan === 'col') {
    const y0 = args.y0 !== undefined ? Number(args.y0) : 0;
    const y1 = args.y1 !== undefined ? Number(args.y1) : img.height;
    for (let y = y0; y < y1; y++) {
      const light = isLight(px(at, y));
      if (prev !== null && prev !== light) transitions.push({ y, to: light ? 'light' : 'other' });
      prev = light;
    }
  } else {
    fail(`--scan must be "row" or "col". Got "${args.scan}".`);
  }
  console.log(JSON.stringify(transitions, null, 1));
} else {
  fail(`Pass either --points or --scan. Run with --help for usage.`);
}
