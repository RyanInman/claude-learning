#!/usr/bin/env node
// One verification round: capture, diff, tokens. Records the round; promotes a baseline on pass.
import { execFileSync } from 'node:child_process';
import { existsSync, readFileSync, writeFileSync, mkdirSync, copyFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs, fail } from './lib.mjs';

const here = dirname(fileURLToPath(import.meta.url));
if (!existsSync(join(here, 'node_modules'))) fail(`Scripts not installed. Run: cd ${here} && npm install && npx playwright install chromium`);
const { PNG } = await import('pngjs');
const args = parseArgs(process.argv.slice(2), {
  help: `check.mjs --design <png> --page <file|url> --spec <design-spec.json> [--out-dir .design-check] [--threshold 3] [--max-rounds 5] [--sensitivity 0.03] [--px-tolerance 1] [--reset]
Runs capture -> diff -> tokens, appends the round to <out-dir>/rounds.json, prints a JSON report.
Exit 0 pass (diff <= threshold and no token mismatch), 2 fail with rounds left, 6 fail at round cap.`,
  options: ['design', 'page', 'spec', 'out-dir', 'threshold', 'max-rounds', 'sensitivity', 'px-tolerance'], flags: ['reset'], required: ['design', 'page', 'spec'],
  defaults: { 'out-dir': '.design-check', threshold: '3', 'max-rounds': '5', sensitivity: '0.03', 'px-tolerance': '1' },
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
const actual = join(args['out-dir'], `round-${round}.png`);
const heatmap = join(args['out-dir'], `round-${round}-diff.png`);

const cap = run('capture.mjs', ['--page', args.page, '--width', String(design.width), '--height', String(design.height), '--out', actual]);
if (cap.code) fail(`capture failed: ${cap.err}`, cap.code);
const dif = run('diff.mjs', ['--design', args.design, '--actual', actual, '--out', heatmap, '--sensitivity', args.sensitivity]);
if (dif.code) fail(`diff failed: ${dif.err}`, dif.code);
const tok = run('tokens.mjs', ['--page', args.page, '--spec', args.spec, '--px-tolerance', args['px-tolerance']]);
if (tok.code && tok.code !== 2) fail(`tokens failed: ${tok.err}`, tok.code);

const diffPercent = JSON.parse(dif.out).diffPercent;
const mismatches = JSON.parse(tok.out).mismatches;
const threshold = Number(args.threshold);
const pass = diffPercent <= threshold && mismatches.length === 0;

rounds.push({ round, diffPercent, tokenMismatches: mismatches.length, pass });
writeFileSync(roundsPath, JSON.stringify(rounds, null, 1));
if (pass) copyFileSync(actual, join(args['out-dir'], 'baseline.png'));

console.log(JSON.stringify({
  round, maxRounds, pass, diffPercent, threshold, actual, heatmap, mismatches,
  history: rounds.map(r => `${r.round}:${r.diffPercent}%/${r.tokenMismatches}tok`).join(' '),
  baseline: pass ? join(args['out-dir'], 'baseline.png') : null,
}, null, 1));
process.exit(pass ? 0 : round >= maxRounds ? 6 : 2);
