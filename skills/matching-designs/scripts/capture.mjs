#!/usr/bin/env node
// Screenshot a page at a fixed viewport with animations off and fonts loaded.
// Optionally renders at a higher device pixel ratio and box-downsamples to the target size,
// so a design exported from a 2x capture is compared through the same resampling.
import { writeFileSync } from 'node:fs';
import { chromium } from 'playwright';
import { PNG } from 'pngjs';
import { parseArgs, fail, toUrl, NO_MOTION_CSS } from './lib.mjs';

const args = parseArgs(process.argv.slice(2), {
  help: `capture.mjs --page <file|url> --width <px> --height <px> --out <png> [--full-page] [--dpr 1] [--rects-out <json>]
--dpr N renders at deviceScaleFactor N, then averages each NxN block down to the target size.
--rects-out writes the bounding box of every visible text run to a JSON rect array, for diff.mjs --mask.
Prints JSON {out,width,height,dpr,textRects} on success. Exit 1 on bad args, 3 on page load failure.`,
  options: ['page', 'width', 'height', 'out', 'dpr', 'rects-out'], flags: ['full-page'],
  required: ['page', 'width', 'height', 'out'], defaults: { dpr: '1' },
});

const width = Number(args.width), height = Number(args.height), dpr = Number(args.dpr);
if (!(width > 0 && height > 0)) fail('--width and --height must be positive integers.');
if (!(Number.isInteger(dpr) && dpr >= 1)) fail('--dpr must be an integer of 1 or more.');

function downsample(buf, factor) {
  const src = PNG.sync.read(buf);
  const w = Math.floor(src.width / factor), h = Math.floor(src.height / factor);
  const dst = new PNG({ width: w, height: h });
  const n = factor * factor;
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    let r = 0, g = 0, b = 0, al = 0;
    for (let dy = 0; dy < factor; dy++) for (let dx = 0; dx < factor; dx++) {
      const i = (src.width * (y * factor + dy) + (x * factor + dx)) << 2;
      r += src.data[i]; g += src.data[i + 1]; b += src.data[i + 2]; al += src.data[i + 3];
    }
    const o = (w * y + x) << 2;
    dst.data[o] = Math.round(r / n); dst.data[o + 1] = Math.round(g / n);
    dst.data[o + 2] = Math.round(b / n); dst.data[o + 3] = Math.round(al / n);
  }
  return PNG.sync.write(dst);
}

const browser = await chromium.launch();
try {
  const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: dpr, reducedMotion: 'reduce' });
  const res = await page.goto(toUrl(args.page), { waitUntil: 'networkidle' }).catch(e => fail(`Page load failed: ${e.message}`, 3));
  if (res && !res.ok() && !toUrl(args.page).startsWith('file:')) fail(`Page returned HTTP ${res.status()}.`, 3);
  await page.addStyleTag({ content: NO_MOTION_CSS });
  await page.evaluate(() => document.fonts.ready);

  let textRects = 0;
  if (args['rects-out']) {
    const rects = await page.evaluate(() => {
      const out = [];
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      for (let n = walker.nextNode(); n; n = walker.nextNode()) {
        if (!n.nodeValue.trim()) continue;
        const range = document.createRange();
        range.selectNodeContents(n);
        for (const r of range.getClientRects()) {
          if (r.width < 1 || r.height < 1) continue;
          out.push({ x: Math.floor(r.left) - 2, y: Math.floor(r.top) - 2, width: Math.ceil(r.width) + 4, height: Math.ceil(r.height) + 4 });
        }
      }
      return out;
    });
    writeFileSync(args['rects-out'], JSON.stringify(rects));
    textRects = rects.length;
  }

  const shot = await page.screenshot({ fullPage: Boolean(args['full-page']) });
  writeFileSync(args.out, dpr > 1 ? downsample(shot, dpr) : shot);
  console.log(JSON.stringify({ out: args.out, width, height, dpr, textRects }));
} finally { await browser.close(); }
