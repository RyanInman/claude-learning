'use strict';
// Draws laid-out primitives as absolutely-positioned HTML at 96px per inch.
// It computes nothing: every x/y/w/h comes from layout.js, so what the browser
// shows is the same geometry the .pptx will receive.

const fs = require('fs');
const path = require('path');

const PX = 96;

const MIME = {
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
  '.gif': 'image/gif', '.webp': 'image/webp', '.svg': 'image/svg+xml',
};

function dataURI(file) {
  const ext = path.extname(file).toLowerCase();
  const mime = MIME[ext];
  if (!mime) throw new Error(`Unsupported image type "${ext}" for ${file}.`);
  return `data:${mime};base64,${fs.readFileSync(file).toString('base64')}`;
}

function esc(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function hex(c) { return c == null ? 'transparent' : `#${String(c).replace('#', '')}`; }

function runSpan(run, prim, editable) {
  const st = [];
  if (run.size) st.push(`font-size:${run.size}pt`);
  if (run.color) st.push(`color:${hex(run.color)}`);
  if (run.bold) st.push('font-weight:700');
  if (run.italic) st.push('font-style:italic');
  if (run.mono) st.push('font-family:var(--mono)');
  const text = esc(run.text).replace(/\n/g, '<br>');
  // Provenance rides on the run, not the primitive, so each run of a mixed
  // paragraph — a Pro/Con label beside its body, a callout's bold lead-in —
  // edits back to its own spec field instead of being fused into one string.
  const ed = editable && run.src
    ? ` class="ed" data-src="${esc(JSON.stringify(run.src))}"` : '';
  return `<span${ed} style="${st.join(';')}">${text}</span>`;
}

function primHTML(prim, i, opts) {
  const box = `left:${prim.x * PX}px;top:${prim.y * PX}px;width:${prim.w * PX}px;`;
  if (prim.kind === 'rect' || prim.kind === 'ellipse') {
    const st = [box, `height:${prim.h * PX}px`];
    st.push(`background:${hex(prim.fill)}`);
    if (prim.kind === 'ellipse') st.push('border-radius:50%');
    else if (prim.radius) st.push(`border-radius:${prim.radius * PX}px`);
    if (prim.lineWidth) {
      st.push(prim.dashed
        ? `outline:${prim.lineWidth}px dashed ${hex(prim.lineColor)};outline-offset:-${prim.lineWidth}px`
        : `box-shadow:inset 0 0 0 ${prim.lineWidth}px ${hex(prim.lineColor)}`);
    }
    if (prim.background) st.push('z-index:0');
    return `<div class="p" style="${st.join(';')}"></div>`;
  }
  if (prim.kind === 'line') {
    return `<div class="p" style="${box}height:${prim.thickness}px;background:${hex(prim.color)}"></div>`;
  }
  if (prim.kind === 'image') {
    // Embedded rather than linked: the deck is one file people email around and
    // open from anywhere, so a path relative to the spec would break the moment
    // the html moved out of its build directory.
    return `<img class="p" style="${box}height:${prim.h * PX}px;object-fit:contain" `
      + `src="${dataURI(prim.path)}" alt="${esc(prim.alt)}">`;
  }
  if (prim.kind === 'text') {
    const st = [box, `height:${prim.h * PX}px`];
    st.push(`font-family:${prim.font === undefined ? 'var(--sans)' : `'${prim.font}',var(--sans)`}`);
    st.push(`font-size:${prim.size}pt`, `color:${hex(prim.color)}`);
    st.push('display:flex', `justify-content:${
      prim.align === 'center' ? 'center' : prim.align === 'right' ? 'flex-end' : 'flex-start'}`);
    st.push(`align-items:${prim.valign === 'middle' ? 'center' : 'flex-start'}`);
    st.push(`text-align:${prim.align || 'left'}`);
    if (prim.letterSpacing) st.push(`letter-spacing:${prim.letterSpacing}em`);
    if (prim.noWrap) st.push('white-space:pre', 'overflow:hidden');
    return `<div class="p t" style="${st.join(';')}"><div>`
      + prim.runs.map((r) => runSpan(r, prim, opts.editable)).join('') + '</div></div>';
  }
  throw new Error(`Renderer has no case for primitive kind "${prim.kind}".`);
}

function slideHTML(slide, layout, opts) {
  const warn = slide.overflow && opts.showOverflow
    ? `<div class="overflow">content runs ${slide.overflow}" past the safe area</div>` : '';
  return `<section class="slide${slide.dark ? ' dark' : ''}" data-i="${slide.index}" `
    + `data-title="${esc(slide.title)}" style="background:${hex(slide.bg)}">`
    + slide.prims.map((p, i) => primHTML(p, i, opts)).join('')
    + warn
    + `<div class="pageno">${slide.index + 1}</div>`
    + '</section>';
}

const BASE_CSS = `
*{box-sizing:border-box;margin:0;padding:0}
:root{--sans:Arial,Helvetica,sans-serif;--mono:'Courier New',Consolas,monospace}
body{background:#111214;font-family:var(--sans);-webkit-font-smoothing:antialiased}
.slide{position:relative;width:{{W}}px;height:{{H}}px;overflow:hidden;flex:none}
.p{position:absolute;z-index:1}
.t{line-height:1.28}
.t>div{width:100%}
.pageno{position:absolute;right:22px;bottom:14px;font-size:10pt;opacity:.35;z-index:2}
.overflow{position:absolute;left:0;right:0;bottom:0;background:#B0442F;color:#fff;
  font-size:11pt;padding:4px 12px;z-index:5}
.ed{border-radius:3px}
.ed:focus{outline:2px solid #4C8DFF;outline-offset:2px}
.ed:hover{background:rgba(76,141,255,.14);box-shadow:0 0 0 2px rgba(76,141,255,.14)}
/* A run that is currently empty still needs somewhere to click. */
.ed:empty{display:inline-block;min-width:1.4em;min-height:1em;background:rgba(76,141,255,.12)}
`;

const DECK_CSS = `
#stage{display:flex;align-items:center;justify-content:center;min-height:100vh}
.slide{display:none;box-shadow:0 24px 70px rgba(0,0,0,.5)}
.slide.on{display:block}
#bar{position:fixed;left:0;right:0;bottom:0;height:34px;background:#1b1c1f;color:#8b8f96;
  display:flex;align-items:center;gap:16px;padding:0 14px;font-size:12px;z-index:50}
#bar b{color:#e6e8ea;font-weight:600}
#notes{position:fixed;right:0;top:0;bottom:34px;width:330px;background:#191a1d;color:#c8ccd2;
  padding:18px;overflow:auto;font-size:13px;line-height:1.55;display:none;z-index:40}
#notes.on{display:block}
#notes h4{color:#fff;font-size:11px;letter-spacing:.09em;text-transform:uppercase;margin-bottom:10px}
`;

const GRID_CSS = `
#stage{display:grid;grid-template-columns:repeat(auto-fill,{{CELLW}}px);gap:22px;padding:22px;justify-content:center}
.cell{background:#000;border-radius:8px;overflow:hidden;position:relative;width:{{CELLW}}px}
.cell>.slide{transform-origin:top left;display:block}
.cap{position:absolute;left:0;right:0;bottom:0;background:rgba(10,10,12,.86);color:#d6d9dd;
  font-size:12px;padding:5px 10px;z-index:10}
`;

const DECK_JS = `
const slides=[...document.querySelectorAll('.slide')];
const notesData=window.__NOTES__||[];
let i=0,notesOn=false;
function show(n){i=Math.max(0,Math.min(slides.length-1,n));
  slides.forEach((s,k)=>s.classList.toggle('on',k===i));
  document.getElementById('pos').textContent=(i+1)+' / '+slides.length;
  document.getElementById('name').textContent=slides[i].dataset.title||'';
  document.getElementById('nbody').innerHTML=(notesData[i]||'<i style="opacity:.5">No speaker notes.</i>')
    .replace(/\\n/g,'<br>');
  location.hash=String(i+1);}
function fit(){const s=slides[i];const pad=notesOn?360:40;
  const k=Math.min((innerWidth-pad)/{{W}},(innerHeight-70)/{{H}});
  slides.forEach(x=>{x.style.transform='scale('+k+')';x.style.transformOrigin='center center';});}
addEventListener('keydown',e=>{
  if(e.target.isContentEditable)return;
  if(e.key==='ArrowRight'||e.key==='PageDown'||e.key===' ')  {show(i+1);fit();e.preventDefault();}
  if(e.key==='ArrowLeft'||e.key==='PageUp')  {show(i-1);fit();}
  if(e.key==='Home'){show(0);fit();} if(e.key==='End'){show(slides.length-1);fit();}
  if(e.key==='n'){notesOn=!notesOn;document.getElementById('notes').classList.toggle('on',notesOn);fit();}});
addEventListener('resize',fit);
show(location.hash?parseInt(location.hash.slice(1),10)-1||0:0);fit();
`;

function renderDeck(deck, opts) {
  const o = Object.assign({ mode: 'deck', title: 'Deck', showOverflow: true, editable: false, extraHead: '', extraBody: '' }, opts);
  const W = deck.page.w * PX;
  const H = deck.page.h * PX;
  const fill = (s) => s.replace(/\{\{W\}\}/g, String(W)).replace(/\{\{H\}\}/g, String(H));
  const t = deck.design.t;
  const fonts = `:root{--sans:'${t.sans}',Arial,sans-serif;--mono:'${t.mono}','Courier New',monospace}`;

  let body;
  let css = fill(BASE_CSS) + fonts;
  let js = '';
  if (o.mode === 'grid') {
    const cellW = o.cellWidth || 430;
    css += GRID_CSS.replace(/\{\{CELLW\}\}/g, String(cellW));
    const scale = cellW / W;
    body = '<div id="stage">' + deck.slides.map((s) =>
      `<div class="cell" style="height:${Math.round(H * scale)}px">`
      + slideHTML(s, deck, o).replace('class="slide', `style="transform:scale(${scale})" class="slide`)
      + `<div class="cap">${s.index + 1}. ${esc(s.title)}${s.overflow ? ' — OVERFLOW' : ''}</div></div>`
    ).join('') + '</div>';
  } else {
    css += DECK_CSS;
    js = fill(DECK_JS);
    body = '<div id="stage">' + deck.slides.map((s) => slideHTML(s, deck, o)).join('') + '</div>'
      + '<div id="notes"><h4>Speaker notes</h4><div id="nbody"></div></div>'
      + '<div id="bar"><b id="pos"></b><span id="name"></span>'
      + '<span style="margin-left:auto;opacity:.7">← → move · N notes</span></div>';
  }

  return `<!doctype html><html><head><meta charset="utf-8">
<title>${esc(o.title)}</title>
<style>${css}${o.extraCSS || ''}</style></head>
<body>${body}${o.extraBody}
<script>window.__NOTES__=${JSON.stringify(deck.slides.map((s) => esc(s.notes)))};</script>
<script>${js}</script>${o.extraHead}
</body></html>`;
}

module.exports = { renderDeck, primHTML, slideHTML, esc, hex, PX };
