#!/usr/bin/env node
'use strict';
// Read and close out the feedback the user left in the studio.
//
//   node feedback.js spec.yaml                 # open notes, grouped by slide
//   node feedback.js spec.yaml --all           # include already-resolved notes
//   node feedback.js spec.yaml --resolve n123  # mark one note done
//   node feedback.js spec.yaml --resolve-all   # mark every open note done
//   node feedback.js spec.yaml --json          # machine-readable
//
// Exit 0 when there are open notes, 3 when there are none, 2 on error — so a
// caller can branch on "is there anything to do" without parsing the output.

const fs = require('fs');

const argv = process.argv.slice(2);
const specFile = argv.find((a) => !a.startsWith('--'));
if (!specFile) {
  console.error('Usage: node feedback.js <spec.yaml> [--all] [--resolve <id>] [--resolve-all] [--json]');
  process.exit(2);
}
const file = specFile.replace(/\.(ya?ml|json)$/, '') + '-feedback.json';

let notes;
try {
  notes = JSON.parse(fs.readFileSync(file, 'utf8'));
} catch (err) {
  if (err.code === 'ENOENT') {
    console.log(`No feedback file yet (${file}). Nothing to apply.`);
    process.exit(3);
  }
  console.error(`Could not read ${file}: ${err.message}`);
  process.exit(2);
}

const save = () => fs.writeFileSync(file, JSON.stringify(notes, null, 2) + '\n');

if (argv.includes('--resolve-all')) {
  const n = notes.filter((x) => !x.resolved).length;
  notes.forEach((x) => { x.resolved = true; });
  save();
  console.log(`Marked ${n} note(s) resolved.`);
  process.exit(0);
}

const ri = argv.indexOf('--resolve');
if (ri > -1) {
  const id = argv[ri + 1];
  const note = notes.find((x) => x.id === id);
  if (!note) { console.error(`No note with id ${id}.`); process.exit(2); }
  note.resolved = true;
  save();
  console.log(`Resolved ${id}.`);
  process.exit(0);
}

const showAll = argv.includes('--all');
const shown = showAll ? notes : notes.filter((n) => !n.resolved);

if (argv.includes('--json')) {
  console.log(JSON.stringify(shown, null, 2));
  process.exit(shown.length ? 0 : 3);
}

if (!shown.length) {
  console.log('No open feedback.');
  process.exit(3);
}

const bySlide = new Map();
for (const n of shown) {
  const k = n.slide == null ? 'deck' : n.slide;
  if (!bySlide.has(k)) bySlide.set(k, []);
  bySlide.get(k).push(n);
}

const keys = [...bySlide.keys()].sort((a, b) =>
  (a === 'deck' ? -1 : b === 'deck' ? 1 : a - b));

console.log(`${shown.length} open note(s) in ${file}\n`);
for (const k of keys) {
  const head = k === 'deck' ? 'Whole deck' : `Slide ${k + 1} — ${bySlide.get(k)[0].slideTitle || ''}`;
  console.log(head);
  for (const n of bySlide.get(k)) {
    console.log(`  [${n.id}]${n.resolved ? ' (resolved)' : ''} ${n.text.replace(/\n/g, '\n      ')}`);
  }
  console.log('');
}
process.exit(0);
