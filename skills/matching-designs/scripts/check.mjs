#!/usr/bin/env node
// One verification round: verify the spec against the design, capture, diff, check tokens.
// Records the round, keeps the best page, promotes a baseline on pass.
import { execFileSync } from 'node:child_process';
import { existsSync, readFileSync, writeFileSync, mkdirSync, copyFileSync } from 'node:fs';
import { join, dirname, basename } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs, fail } from './lib.mjs';

const here = dirname(fileURLToPath(import.meta.url));
if (!existsSync(join(here, 'node_modules'))) fail(`Scripts not installed. Run: cd ${here} && npm install && npx playwright install chromium`);
const { PNG } = await import('pngjs');
const args = parseArgs(process.argv.slice(2), {
  help: `check.mjs --design <png> --page <file|url> --spec <design-spec.json> [--out-dir .design-check]
       [--threshold 3] [--layout-threshold 2] [--max-rounds 5] [--sensitivity 0.03] [--px-tolerance 1]
       [--box-tolerance 4] [--sample-tolerance 6] [--dpr <n>] [--reset] [--allow-no-boxes]
Verifies each color token carrying "at":[x,y] against the design image, then runs
capture -> diff (overall, text-masked, per-box, grid) -> tokens, appends the round to
<out-dir>/rounds.json, keeps the best page in <out-dir>/best/, prints a JSON report.
Pass needs zero token mismatches AND either diffPercent <= --threshold or layoutDiff <= --layout-threshold,
because glyph rendering puts an irreducible floor on the overall percent that layout error does not share.
Exit 0 pass, 2 fail with rounds left, 4 the spec contradicts the design, 6 fail at round cap.`,
  options: ['design', 'page', 'spec', 'out-dir', 'threshold', 'layout-threshold', 'max-rounds', 'sensitivity',
            'px-tolerance', 'box-tolerance', 'sample-tolerance', 'dpr'],
  flags: ['reset', 'allow-no-boxes'], required: ['design', 'page', 'spec'],
  defaults: { 'out-dir': '.design-check', threshold: '3', 'layout-threshold': '2', 'max-rounds': '5',
              sensitivity: '0.03', 'px-tolerance': '1', 'box-tolerance': '4', 'sample-tolerance': '6', dpr: '1' },
});

const run = (script, a) => {
  try { return { code: 0, out: execFileSync('node', [join(here, script), ...a], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }) }; }
  catch (e) { return { code: e.status, out: e.stdout || '', err: e.stderr || '' }; }
};

mkdirSync(args['out-dir'], { recursive: true });
const roundsPath = join(args['out-dir'], 'rounds.json');
if (args.reset && existsSync(roundsPath)) writeFileSync(roundsPath, '[]');
const rounds = existsSync(roundsPath) ? JSON.parse(readFileSync(roundsPath, 'utf8')) : [];
const round = rounds.length + 1;
const maxRounds = Number(args['max-rounds']);

let design;
try { design = PNG.sync.read(readFileSync(args.design)); } catch (e) { fail(`Cannot read design PNG ${args.design}: ${e.message}`); }
let spec;
try { spec = JSON.parse(readFileSync(args.spec, 'utf8')); } catch (e) { fail(`Cannot parse spec ${args.spec}: ${e.message}`); }
if (spec.viewport?.width !== design.width || spec.viewport?.height !== design.height)
  fail(`Spec viewport ${spec.viewport?.width}x${spec.viewport?.height} != design ${design.width}x${design.height}. Set spec.viewport to the design's size.`, 4);

const boxes = spec.boxes ?? [];
if (!boxes.length && !args['allow-no-boxes'])
  fail(`Spec has no boxes. Add a boxes array measuring at least the main container and each repeated block, because a color-only spec reports a perfect score on a page whose blocks sit in the wrong place. Pass --allow-no-boxes only for a page with no layout to measure.`, 4);

// The spec must match the design before the page is judged against the spec.
const px = (x, y) => { const i = (design.width * y + x) << 2; return [design.data[i], design.data[i + 1], design.data[i + 2]]; };
const hex = ([r, g, b]) => '#' + [r, g, b].map(v => v.toString(16).padStart(2, '0')).join('');
const sampleTol = Number(args['sample-tolerance']);
const sampleErrors = [];
for (const t of spec.tokens) {
  if (!Array.isArray(t.at) || !/^#[0-9a-f]{3,8}$/i.test(String(t.expected))) continue;
  const [x, y] = t.at;
  if (x < 0 || y < 0 || x >= design.width || y >= design.height) { sampleErrors.push(`${t.selector} ${t.property}: at [${x},${y}] is outside the design (${design.width}x${design.height})`); continue; }
  const got = px(x, y);
  const want = (() => { const s = t.expected.replace('#', ''); const f = s.length === 3 ? s.split('').map(c => c + c).join('') : s.slice(0, 6); return [0, 2, 4].map(i => parseInt(f.slice(i, i + 2), 16)); })();
  if (!want.every((v, i) => Math.abs(v - got[i]) <= sampleTol))
    sampleErrors.push(`${t.selector} ${t.property}: spec says ${t.expected}, design pixel at [${x},${y}] is ${hex(got)}`);
}
if (sampleErrors.length)
  fail(`Spec contradicts the design image:\n  ${sampleErrors.join('\n  ')}\nRe-sample with sample.mjs and correct the spec, because fixing the page toward a wrong token moves it away from the design.`, 4);

const actual = join(args['out-dir'], `round-${round}.png`);
const heatmap = join(args['out-dir'], `round-${round}-diff.png`);
const textRects = join(args['out-dir'], `round-${round}-text.json`);
const regionsFile = join(args['out-dir'], 'regions.json');

const cap = run('capture.mjs', ['--page', args.page, '--width', String(design.width), '--height', String(design.height),
  '--out', actual, '--rects-out', textRects, '--dpr', args.dpr]);
if (cap.code) fail(`capture failed: ${cap.err}`, cap.code);

const tok = run('tokens.mjs', ['--page', args.page, '--spec', args.spec, '--px-tolerance', args['px-tolerance'], '--box-tolerance', args['box-tolerance']]);
if (tok.code && tok.code !== 2) fail(`tokens failed: ${tok.err}`, tok.code);
const mismatches = JSON.parse(tok.out).mismatches;

// Region rects come from the spec's boxes, so the diff reports a percent per named element.
writeFileSync(regionsFile, JSON.stringify(boxes
  .filter(b => b.width !== undefined && b.height !== undefined)
  .map(b => ({ label: b.selector, x: b.x ?? 0, y: b.y ?? 0, width: b.width, height: b.height }))));

const dif = run('diff.mjs', ['--design', args.design, '--actual', actual, '--out', heatmap,
  '--sensitivity', args.sensitivity, '--mask', textRects, '--regions', regionsFile, '--grid', '8']);
if (dif.code) fail(`diff failed: ${dif.err}`, dif.code);
const d = JSON.parse(dif.out);

const threshold = Number(args.threshold);
const layoutThreshold = Number(args['layout-threshold']);
const layoutDiff = d.layoutDiff ?? d.diffPercent;
const clean = mismatches.length === 0;
const pass = clean && (d.diffPercent <= threshold || layoutDiff <= layoutThreshold);
const passReason = !clean ? null : d.diffPercent <= threshold ? 'diffPercent within threshold'
  : layoutDiff <= layoutThreshold ? 'layout matches; remaining diff is glyph rendering' : null;

rounds.push({ round, diffPercent: d.diffPercent, layoutDiff, textDiff: d.textDiff ?? null, tokenMismatches: mismatches.length, pass });
writeFileSync(roundsPath, JSON.stringify(rounds, null, 1));

// Keep the best page, so a round that makes things worse is visible and revertible.
const prior = rounds.slice(0, -1);
const bestPrior = prior.length ? prior.reduce((a, b) => (b.layoutDiff ?? b.diffPercent) < (a.layoutDiff ?? a.diffPercent) ? b : a) : null;
const bestPriorDiff = bestPrior ? (bestPrior.layoutDiff ?? bestPrior.diffPercent) : Infinity;
const improved = layoutDiff < bestPriorDiff;
const regressed = layoutDiff > bestPriorDiff + 0.01;
const bestDir = join(args['out-dir'], 'best');
if (improved && existsSync(args.page)) {
  mkdirSync(bestDir, { recursive: true });
  copyFileSync(args.page, join(bestDir, basename(args.page)));
  copyFileSync(actual, join(bestDir, 'render.png'));
  writeFileSync(join(bestDir, 'best.json'), JSON.stringify({ round, diffPercent: d.diffPercent, layoutDiff }, null, 1));
}
const best = improved ? { round, diffPercent: d.diffPercent, layoutDiff } : { round: bestPrior.round, diffPercent: bestPrior.diffPercent, layoutDiff: bestPrior.layoutDiff ?? bestPrior.diffPercent };
const previous = prior.at(-1);
const stalled = Boolean(previous && Math.abs((previous.layoutDiff ?? previous.diffPercent) - layoutDiff) < 0.3 && Math.abs(previous.diffPercent - d.diffPercent) < 0.3);

if (pass) copyFileSync(actual, join(args['out-dir'], 'baseline.png'));

console.log(JSON.stringify({
  round, maxRounds, pass, passReason,
  diffPercent: d.diffPercent, layoutDiff, textDiff: d.textDiff ?? null,
  threshold, layoutThreshold,
  regressed, best, stalled,
  actual, heatmap, mismatches,
  regions: (d.regions ?? []).slice(0, 5), gridTop: d.gridTop ?? [],
  history: rounds.map(r => `${r.round}:${r.diffPercent}%/L${r.layoutDiff ?? '?'}%/${r.tokenMismatches}tok`).join(' '),
  bestPage: existsSync(bestDir) ? join(bestDir, basename(args.page)) : null,
  baseline: pass ? join(args['out-dir'], 'baseline.png') : null,
}, null, 1));
process.exit(pass ? 0 : round >= maxRounds ? 6 : 2);
