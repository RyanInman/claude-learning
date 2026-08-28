#!/usr/bin/env node
// Screenshot a page at a fixed viewport with animations off and fonts loaded.
import { chromium } from 'playwright';
import { parseArgs, toUrl, NO_MOTION_CSS } from './lib.mjs';

const args = parseArgs(process.argv.slice(2), {
  help: `capture.mjs --page <file|url> --width <px> --height <px> --out <png> [--full-page]
Prints JSON {out,width,height} on success. Exit 1 on bad args, 3 on page load failure.`,
  options: ['page', 'width', 'height', 'out'], flags: ['full-page'], required: ['page', 'width', 'height', 'out'], defaults: {},
});

const width = Number(args.width), height = Number(args.height);
if (!(width > 0 && height > 0)) { console.error('--width and --height must be positive integers.'); process.exit(1); }

const browser = await chromium.launch();
try {
  const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 1, reducedMotion: 'reduce' });
  const res = await page.goto(toUrl(args.page), { waitUntil: 'networkidle' }).catch(e => { console.error(`Page load failed: ${e.message}`); process.exit(3); });
  if (res && !res.ok() && !toUrl(args.page).startsWith('file:')) { console.error(`Page returned HTTP ${res.status()}.`); process.exit(3); }
  await page.addStyleTag({ content: NO_MOTION_CSS });
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({ path: args.out, fullPage: Boolean(args['full-page']) });
  console.log(JSON.stringify({ out: args.out, width, height }));
} finally { await browser.close(); }
