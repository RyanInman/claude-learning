#!/usr/bin/env node
'use strict';
// CLI: spec -> deck.html + deck.pptx (+ contact-sheet grid).
//
//   node build_deck.js spec.yaml
//   node build_deck.js spec.yaml --out dist/talk --theme ink --personality keynote
//   node build_deck.js spec.yaml --check          # layout only, write nothing

const fs = require('fs');
const path = require('path');
const yaml = require(path.join(__dirname, 'node_modules', 'js-yaml'));
const { layoutDeck } = require('./layout');
const { renderDeck } = require('./render_html');

function parseArgs(argv) {
  const a = { spec: null, out: null, theme: null, personality: null, check: false, quiet: false };
  for (let i = 0; i < argv.length; i++) {
    const v = argv[i];
    if (v === '--check') a.check = true;
    else if (v === '--quiet') a.quiet = true;
    else if (v === '--out') a.out = argv[++i];
    else if (v === '--theme') a.theme = argv[++i];
    else if (v === '--personality') a.personality = argv[++i];
    else if (v.startsWith('--')) throw new Error(`Unknown flag ${v}`);
    else if (!a.spec) a.spec = v;
  }
  if (!a.spec) throw new Error('Usage: node build_deck.js <spec.yaml> [--out base] [--theme t] [--personality p] [--check]');
  return a;
}

function loadSpec(file) {
  const raw = fs.readFileSync(file, 'utf8');
  // js-yaml v4 `load` is safe by default — it is the old `safeLoad`, and
  // constructing arbitrary types requires explicitly passing a custom schema.
  const spec = file.endsWith('.json') ? JSON.parse(raw) : yaml.load(raw);
  if (!spec || typeof spec !== 'object') throw new Error(`${file} did not parse into an object.`);
  spec.basedir = path.dirname(path.resolve(file));
  return spec;
}

function build(specFile, opts) {
  const o = opts || {};
  const spec = loadSpec(specFile);
  spec.design = Object.assign({}, spec.design);
  if (o.theme) spec.design.theme = o.theme;
  if (o.personality) spec.design.personality = o.personality;

  const deck = layoutDeck(spec);
  const title = (spec.meta && spec.meta.title) || path.basename(specFile).replace(/\.(ya?ml|json)$/, '');
  const base = o.out || path.join(path.dirname(specFile), 'dist', title.toLowerCase().replace(/[^a-z0-9]+/g, '-'));
  const overflows = deck.slides.filter((s) => s.overflow);

  const result = { deck, base, overflows, written: [] };
  if (o.check) return result;

  fs.mkdirSync(path.dirname(base) || '.', { recursive: true });
  const htmlPath = `${base}.html`;
  fs.writeFileSync(htmlPath, renderDeck(deck, { mode: 'deck', title }));
  result.written.push(htmlPath);

  const gridPath = `${base}-contact-sheet.html`;
  fs.writeFileSync(gridPath, renderDeck(deck, { mode: 'grid', title: `${title} — all slides` }));
  result.written.push(gridPath);

  return result;
}

function buildPptx(result) {
  const { renderPptx } = require('./render_pptx');
  const out = `${result.base}.pptx`;
  return renderPptx(result.deck, out).then(() => { result.written.push(out); return out; });
}

if (require.main === module) {
  (async () => {
    try {
      const a = parseArgs(process.argv.slice(2));
      const r = build(a.spec, a);
      if (!a.check) await buildPptx(r);
      if (!a.quiet) {
        const d = r.deck.design;
        console.log(`${r.deck.slides.length} slides · theme ${d.key} · personality ${d.personaKey}`);
        for (const f of r.written) console.log(`  wrote ${f}`);
        if (r.overflows.length) {
          console.log(`\n${r.overflows.length} slide(s) overflow the safe area — split or shorten in the spec:`);
          for (const s of r.overflows) {
            console.log(`  slide ${s.index + 1} "${s.title}" runs ${s.overflow}" past 7.05"`);
          }
        } else {
          console.log('  no overflow');
        }
      }
      process.exit(r.overflows.length && a.check ? 1 : 0);
    } catch (err) {
      console.error(`\nBuild failed: ${err.message}\n`);
      process.exit(2);
    }
  })();
}

module.exports = { build, buildPptx, loadSpec };
