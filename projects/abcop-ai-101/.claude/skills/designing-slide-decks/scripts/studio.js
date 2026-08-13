#!/usr/bin/env node
'use strict';
// Design studio: a local page for choosing a look and editing slide text, which
// writes the choices back into the spec.
//
//   node studio.js spec.yaml [--port 4321]
//
// Nothing is saved until Save is pressed, so the user can try every combination
// freely. Save rewrites the spec and rebuilds deck.html / deck.pptx, keeping the
// spec the one source both outputs come from.

const crypto = require('crypto');
const fs = require('fs');
const http = require('http');
const path = require('path');
const url = require('url');
const { execFile, spawn } = require('child_process');
const yaml = require(path.join(__dirname, 'node_modules', 'js-yaml'));
const { layoutDeck } = require('./layout');
const { renderDeck, esc } = require('./render_html');
const { THEMES, PERSONALITIES } = require('./themes');

const args = process.argv.slice(2);
const specFile = args.find((a) => !a.startsWith('--'));
const portArg = args.indexOf('--port');
const PORT = portArg > -1 ? parseInt(args[portArg + 1], 10) : 4321;
if (!specFile) {
  console.error('Usage: node studio.js <spec.yaml> [--port 4321]');
  process.exit(2);
}

let specText = fs.readFileSync(specFile, 'utf8');
let spec = yaml.load(specText);
spec.design = spec.design || {};
spec.basedir = path.dirname(path.resolve(specFile));

// Live reload. An edit to the spec on disk — Claude applying feedback, an editor
// save — should reach the browser without restarting the studio. Two guards keep
// that from destroying work: the server refuses to drop its in-memory spec while
// it holds unsaved edits, and the page refuses to reload while it holds unsaved
// picks. Either way the change is announced and Revert loads it on demand.
const clients = new Set();
let specDirty = false;

function announce(payload) {
  const line = `data: ${JSON.stringify(payload)}\n\n`;
  for (const res of clients) res.write(line);
}

function reloadSpec() {
  const raw = fs.readFileSync(specFile, 'utf8');
  const next = yaml.load(raw);
  if (!next || typeof next !== 'object') throw new Error('spec did not parse into an object');
  next.design = next.design || {};
  next.basedir = path.dirname(path.resolve(specFile));
  layoutDeck(next); // A spec that cannot lay out must never replace one that can.
  spec = next;
  specText = raw;
  specDirty = false;
}

function onSpecTouched() {
  if (applyRun) return; // an apply run saves several times; reload once, at the end
  let raw;
  try { raw = fs.readFileSync(specFile, 'utf8'); } catch (err) { return; } // mid-write
  if (raw === specText) return; // the studio's own save, or a touch that changed nothing
  if (specDirty) return announce({ type: 'changed' });
  try { reloadSpec(); } catch (err) { return announce({ type: 'broken', message: err.message }); }
  announce({ type: 'reload' });
}

// Apply: hand the open feedback notes to a headless Claude run, which edits the
// spec, resolves the notes it applied, and rebuilds. It is a fresh session with
// none of the conversation that produced the deck, so the prompt points it at
// Stage 3b of the skill, which is written for exactly this job.
// Every POST here changes a file on disk, and one of them starts an agent. A page
// on any other site can POST to a loopback port without being able to read the
// reply, so a secret the attacking page cannot see is what separates a real click
// in the studio from a drive-by request.
const TOKEN = crypto.randomBytes(18).toString('base64url');

function fromStudioPage(req) {
  const origin = req.headers.origin;
  if (origin && origin !== `http://127.0.0.1:${PORT}`) return false;
  return req.headers['x-studio-token'] === TOKEN;
}

const CLAUDE_BIN = process.env.CLAUDE_BIN || 'claude';
const APPLY_TIMEOUT_MS = 15 * 60 * 1000;
let applyRun = null;

function applyPrompt() {
  const spec = path.resolve(specFile);
  const scripts = __dirname;
  return [
    'Apply the reviewer feedback on a slide deck spec, then rebuild the deck.',
    '',
    `Spec: ${spec}`,
    `Read ${path.join(scripts, '..', 'SKILL.md')} — Stage 3b covers this exact job.`,
    '',
    `1. Read the open notes: node ${path.join(scripts, 'feedback.js')} ${spec}`,
    '2. Edit the spec to address each note. A note is a change request against the',
    '   spec — never edit anything in dist/, and never edit the .html or .pptx.',
    `3. Resolve each note you applied: node ${path.join(scripts, 'feedback.js')} ${spec} --resolve <id>`,
    '   Leave a note open if it is ambiguous or you disagree with it.',
    `4. Rebuild: node ${path.join(scripts, 'build_deck.js')} ${spec}`,
    '   Overflow is a defect — shorten or split the slide and rebuild until it is clean.',
    '5. Finish with one line per note: what you changed, or why you left it open.',
  ].join('\n');
}

function startApply() {
  const child = spawn(CLAUDE_BIN, [
    '-p', applyPrompt(),
    '--output-format', 'stream-json',
    '--verbose',
    '--permission-mode', 'acceptEdits',
    '--allowedTools', 'Read', 'Edit', 'Write', 'Grep', 'Glob', 'Bash(node:*)',
  ], { cwd: process.cwd(), env: process.env });

  applyRun = child;
  announce({ type: 'apply', state: 'start' });

  const timer = setTimeout(() => child.kill('SIGTERM'), APPLY_TIMEOUT_MS);
  let buf = '';
  let result = null;

  child.stdout.on('data', (chunk) => {
    buf += chunk;
    const lines = buf.split('\n');
    buf = lines.pop();
    for (const line of lines) {
      if (!line.trim()) continue;
      let ev;
      try { ev = JSON.parse(line); } catch (err) { continue; }
      if (ev.type === 'assistant') {
        for (const part of (ev.message && ev.message.content) || []) {
          if (part.type === 'text' && part.text.trim()) {
            announce({ type: 'apply', state: 'log', message: part.text.trim().slice(0, 160) });
          } else if (part.type === 'tool_use') {
            announce({ type: 'apply', state: 'log', message: `${part.name}…` });
          }
        }
      } else if (ev.type === 'result') {
        result = ev;
      }
    }
  });

  let stderr = '';
  child.stderr.on('data', (chunk) => { stderr += chunk; });

  child.on('error', (err) => {
    clearTimeout(timer);
    applyRun = null;
    const hint = err.code === 'ENOENT'
      ? `${CLAUDE_BIN} is not on PATH — set CLAUDE_BIN to its full path`
      : err.message;
    announce({ type: 'apply', state: 'error', message: hint });
  });

  child.on('close', (code) => {
    clearTimeout(timer);
    applyRun = null;
    if (result && !result.is_error) {
      announce({ type: 'apply', state: 'done', message: (result.result || '').slice(0, 400) });
    } else {
      const why = (result && result.result) || stderr.trim().slice(0, 300) || `claude exited ${code}`;
      announce({ type: 'apply', state: 'error', message: why });
    }
    // The run rewrote the spec while reloads were suppressed. Catch up now.
    setTimeout(onSpecTouched, 200);
  });
}

// Watch the directory, not the file: an editor that saves by writing a temp file
// and renaming it over the original breaks a watch held on the file itself.
let touchTimer = null;
fs.watch(path.dirname(path.resolve(specFile)), (ev, name) => {
  if (name !== path.basename(specFile)) return;
  clearTimeout(touchTimer); // one save can fire several events
  touchTimer = setTimeout(onSpecTouched, 120);
});

// Feedback notes live in a sidecar next to the spec rather than inside it, so a
// note can never break a build and the spec stays purely a description of the
// deck. Notes are written the moment they are added — unlike design picks, they
// are not a change to the deck, and losing them to a closed tab would be worse
// than the inconsistency of saving them early.
const FEEDBACK_FILE = specFile.replace(/\.(ya?ml|json)$/, '') + '-feedback.json';

function loadFeedback() {
  try {
    return JSON.parse(fs.readFileSync(FEEDBACK_FILE, 'utf8'));
  } catch (err) {
    if (err.code === 'ENOENT') return [];
    throw new Error(`${FEEDBACK_FILE} exists but is not readable JSON: ${err.message}`);
  }
}

function saveFeedback(notes) {
  fs.writeFileSync(FEEDBACK_FILE, JSON.stringify(notes, null, 2) + '\n');
}

function slideTitle(i) {
  const s = spec.slides[i];
  if (!s) return `Slide ${i + 1}`;
  if (typeof s.title === 'string') return s.title;
  if (s.title) return s.title.text || (s.title.lines || []).map((l) => l.text).join(' ');
  return `Slide ${i + 1}`;
}

function setPath(obj, pathArr, value) {
  let cur = obj;
  for (let i = 0; i < pathArr.length - 1; i++) {
    const k = pathArr[i];
    if (cur[k] == null) throw new Error(`Path ${pathArr.join('.')} does not exist in the spec.`);
    cur = cur[k];
  }
  cur[pathArr[pathArr.length - 1]] = value;
}

// A slide may carry `variants:` — alternative element stacks authored up front
// so the picker has something real to compare. Choosing one replaces `elements`.
function slideWithVariant(slide, vi) {
  if (vi == null || !slide.variants || !slide.variants[vi]) return slide;
  const v = slide.variants[vi];
  return Object.assign({}, slide, v.slide || { elements: v.elements });
}

function oneSlideDeck(i, theme, personality, variantIdx) {
  const s = slideWithVariant(spec.slides[i] || {}, variantIdx);
  const deck = layoutDeck({
    meta: spec.meta,
    design: Object.assign({}, spec.design,
      theme ? { theme } : {}, personality ? { personality } : {}),
    slides: [s],
  });
  // The layout numbered this slide 0 because it was laid out alone. Restore the
  // real index so an edit made here patches the slide the user is looking at.
  for (const prim of deck.slides[0].prims) {
    if (prim.src) prim.src = [i].concat(prim.src.slice(1));
  }
  deck.slides[0].index = i;
  return deck;
}

function slidePage(i, q) {
  const deck = oneSlideDeck(i, q.theme, q.personality,
    q.variant == null || q.variant === '' ? null : parseInt(q.variant, 10));
  const editable = q.edit === '1';
  const fitCSS = `
html,body{background:transparent;overflow:hidden}
#stage{display:block;padding:0;gap:0}
.slide{display:block!important;transform-origin:top left;box-shadow:none}
.pageno{display:none}`;
  const fitJS = `
<script>
function fit(){var s=document.querySelector('.slide');
  var k=Math.min(innerWidth/(${deck.page.w}*96),innerHeight/(${deck.page.h}*96));
  s.style.transform='scale('+k+')';}
addEventListener('resize',fit);fit();
${editable ? `
document.querySelectorAll('.ed').forEach(function(n){
  n.setAttribute('contenteditable','plaintext-only');
  n.addEventListener('blur',function(){
    parent.postMessage({type:'edit',src:JSON.parse(n.dataset.src),
      value:n.innerText.replace(/\\u00a0/g,' ')},'*');});});
` : ''}
</script>`;
  return renderDeck(deck, {
    mode: 'grid', title: 'slide', showOverflow: true, editable,
    cellWidth: deck.page.w * 96, extraCSS: fitCSS, extraHead: fitJS,
  }).replace(/<div class="cell"[^>]*>/, '<div>').replace(/<div class="cap">[\s\S]*?<\/div>/, '');
}

function frame(i, q, extra) {
  const p = new URLSearchParams(Object.assign({ i: String(i) }, q));
  return `<iframe src="/slide?${p.toString()}" scrolling="no" ${extra || ''}></iframe>`;
}

function appPage() {
  const slides = spec.slides.map((s, i) => {
    const t = typeof s.title === 'string' ? s.title
      : (s.title && (s.title.text || (s.title.lines || []).map((l) => l.text).join(' '))) || `Slide ${i + 1}`;
    return { i, title: t, variants: (s.variants || []).length };
  });
  const cur = { theme: spec.design.theme || 'ember', personality: spec.design.personality || 'technical' };

  const themeCards = Object.entries(THEMES).map(([k, v]) => ({ k, label: v.label, blurb: v.blurb }));
  const persCards = Object.entries(PERSONALITIES).map(([k, v]) => ({ k, label: v.label, blurb: v.blurb }));

  return `<!doctype html><html><head><meta charset="utf-8"><title>Deck design studio</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font:14px/1.5 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0f1012;color:#e7e9ec;
  display:grid;grid-template-columns:250px 1fr;height:100vh;overflow:hidden}
aside{background:#16181b;border-right:1px solid #26292e;display:flex;flex-direction:column;overflow:hidden}
aside h1{font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:#8b929c;padding:16px 16px 10px}
.tabs{display:flex;gap:4px;padding:0 12px 12px}
.tab{flex:1;padding:7px 4px;text-align:center;background:#1e2126;border:1px solid #2c3037;border-radius:6px;
  cursor:pointer;font-size:12px;color:#aeb5be}
.tab.on{background:#4C8DFF;border-color:#4C8DFF;color:#fff;font-weight:600}
#film{overflow:auto;flex:1;padding:0 12px 12px}
.film-item{display:flex;gap:9px;align-items:center;padding:7px 8px;border-radius:6px;cursor:pointer;color:#c3c9d1}
.film-item:hover{background:#1e2126}
.film-item.on{background:#232830;color:#fff}
.film-item b{font-size:11px;color:#6f7883;width:18px;flex:none}
.film-item span{font-size:12.5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.film-item i{font-size:10px;background:#4C8DFF;color:#fff;border-radius:8px;padding:1px 6px;font-style:normal}
footer{padding:12px;border-top:1px solid #26292e;display:flex;gap:8px}
button{flex:1;padding:9px;border:0;border-radius:6px;background:#4C8DFF;color:#fff;font-weight:600;cursor:pointer;font-size:13px}
button.ghost{background:#242830;color:#c3c9d1}
button:disabled{opacity:.5;cursor:default}
main{overflow:auto;padding:20px}
.head{display:flex;align-items:baseline;gap:12px;margin-bottom:14px}
.head h2{font-size:17px}
.head p{color:#8b929c;font-size:13px}
.opts{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:16px}
.opt{background:#17191d;border:2px solid #2a2e35;border-radius:10px;overflow:hidden;cursor:pointer;
  transition:border-color .12s,transform .12s}
.opt:hover{border-color:#5b6470;transform:translateY(-2px)}
.opt.on,.opt.on:hover{border-color:#4C8DFF}
/* The preview iframe is a separate document, so without this it swallows every
   click and only the label strip under it selects the option. */
.opt iframe{width:100%;aspect-ratio:16/9;border:0;display:block;pointer-events:none;
  opacity:0;transition:opacity .16s}
.opt iframe.rdy{opacity:1}
#big{opacity:0;transition:opacity .16s}
#big.rdy{opacity:1}
.opt .meta{padding:9px 12px}
.opt .meta b{font-size:13px}
.opt .meta p{font-size:11.5px;color:#828a94;margin-top:2px}
#big{width:100%;aspect-ratio:16/9;border:0;background:#000;border-radius:10px}
.hint{color:#828a94;font-size:12.5px;margin-top:10px}
#toast{position:fixed;bottom:16px;right:16px;background:#1d7a4c;color:#fff;padding:10px 16px;
  border-radius:8px;opacity:0;transition:opacity .25s;font-size:13px}
#toast.on{opacity:1}
#toast.err{background:#a33}
.fb{margin-top:18px;background:#17191d;border:1px solid #2a2e35;border-radius:10px;padding:14px}
.fb h3{font-size:13px;margin-bottom:3px}
.fb .sub{color:#828a94;font-size:12px;margin-bottom:10px}
.fb textarea{width:100%;min-height:74px;background:#0f1114;color:#e7e9ec;border:1px solid #333941;
  border-radius:7px;padding:10px;font:13px/1.5 inherit;resize:vertical}
.fb textarea:focus{outline:0;border-color:#4C8DFF}
.fb .row{display:flex;gap:8px;align-items:center;margin-top:9px}
.fb button{flex:none;padding:8px 15px}
.fb .row span{color:#6f7883;font-size:11.5px}
.notes{margin-top:14px;display:flex;flex-direction:column;gap:7px}
.note{display:flex;gap:9px;align-items:flex-start;background:#1c1f24;border-radius:7px;padding:9px 11px}
.note.done{opacity:.45}
.note.done p{text-decoration:line-through}
.note p{flex:1;font-size:12.5px;line-height:1.5;white-space:pre-wrap}
.note em{display:block;color:#6f7883;font-size:10.5px;font-style:normal;margin-bottom:3px}
.note button{background:none;border:0;color:#7d8792;cursor:pointer;font-size:11px;padding:2px 5px;flex:none}
.note button:hover{color:#e7e9ec}
.film-item u{font-size:10px;background:#8a5cf6;color:#fff;border-radius:8px;padding:1px 6px;
  text-decoration:none;flex:none}
</style></head><body>
<aside>
  <h1>Deck Studio</h1>
  <div class="tabs">
    <div class="tab on" data-m="theme">Theme</div>
    <div class="tab" data-m="persona">Pacing</div>
    <div class="tab" data-m="edit">Edit</div>
  </div>
  <div id="film"></div>
  <footer>
    <button class="ghost" id="apply">Apply notes</button>
    <button class="ghost" id="revert">Revert</button>
    <button id="save">Save + build</button>
  </footer>
</aside>
<main><div class="head"><h2 id="mt"></h2><p id="ms"></p></div><div id="body"></div></main>
<div id="toast"></div>
<script>
const TOKEN=${JSON.stringify(TOKEN)};
const SLIDES=${JSON.stringify(slides)};
const THEMES=${JSON.stringify(themeCards)};
const PERS=${JSON.stringify(persCards)};
let sel=${JSON.stringify(cur)}, slide=0, mode='theme', dirty=false, notes=[], built=null;

function q(extra){return new URLSearchParams(Object.assign({theme:sel.theme,personality:sel.personality},extra||{})).toString();}
function el(tag,cls,txt){const n=document.createElement(tag);if(cls)n.className=cls;if(txt!=null)n.textContent=txt;return n;}

function openFor(i){return notes.filter(n=>n.slide===i&&!n.resolved).length;}

function film(){const f=document.getElementById('film');f.textContent='';
  SLIDES.forEach(s=>{const d=el('div','film-item'+(s.i===slide?' on':''));
    d.appendChild(el('b',null,String(s.i+1)));d.appendChild(el('span',null,s.title));
    if(s.variants)d.appendChild(el('i',null,s.variants+' opts'));
    const n=openFor(s.i);if(n)d.appendChild(el('u',null,n+' note'+(n>1?'s':'')));
    d.onclick=()=>{slide=s.i;writeHash();render();};f.appendChild(d);});}

function optCard(key,srcQ,name,blurb,onClick){
  const c=el('div','opt');c.dataset.key=key;
  const fr=document.createElement('iframe');fr.setAttribute('scrolling','no');
  // Fade in on load so a genuine reload resolves smoothly instead of flashing
  // the blank document underneath.
  fr.onload=()=>fr.classList.add('rdy');
  fr.src='/slide?'+srcQ;
  const m=el('div','meta');m.appendChild(el('b',null,name));m.appendChild(el('p',null,blurb));
  c.appendChild(fr);c.appendChild(m);c.onclick=onClick;return c;}

// Which inputs actually change the preview URLs in this tab. Selecting a theme
// on the Theme tab does not change any card's src — each card already forces its
// own theme — so that pick must repaint the highlight, never rebuild the frames.
function srcKey(){
  if(mode==='theme')  return 'theme|p:'+sel.personality+'|s:'+slide;
  if(mode==='persona')return 'persona|t:'+sel.theme+'|s:'+slide;
  return 'edit|t:'+sel.theme+'|p:'+sel.personality+'|s:'+slide;}

function paintSelection(){
  const want=mode==='theme'?sel.theme:mode==='persona'?sel.personality:null;
  document.querySelectorAll('.opt').forEach(o=>
    o.classList.toggle('on',want!=null&&o.dataset.key===want));}

// Selection changes highlight only; the frames stay exactly as they are.
function select(kind,key){
  if(kind==='theme')sel.theme=key;else sel.personality=key;
  dirty=true;paintSelection();}

function render(force){
  film();
  const key=srcKey();
  // Nothing that feeds a preview URL has changed, so leave the frames alone.
  if(!force&&built===key){paintSelection();return;}
  built=key;
  const body=document.getElementById('body');body.textContent='';
  const head=document.getElementById('mt'),sub=document.getElementById('ms');
  const sl=SLIDES[slide];
  if(mode==='theme'||mode==='persona'){
    const isTheme=mode==='theme';
    head.textContent=isTheme?'Colour + type':'Pacing';
    sub.textContent='Previewed on slide '+(slide+1)+' — '+sl.title+'. Click to choose.';
    const grid=el('div','opts');
    (isTheme?THEMES:PERS).forEach(o=>{
      const qq=q(isTheme?{theme:o.k,i:slide}:{personality:o.k,i:slide});
      grid.appendChild(optCard(o.k,qq,o.label,o.blurb,
        ()=>select(isTheme?'theme':'persona',o.k)));});
    body.appendChild(grid);
    paintSelection();
  } else {
    head.textContent='Slide '+(slide+1);
    sub.textContent=sl.variants?'Pick a layout, then edit text directly on the slide.'
      :'Click any highlighted text on the slide to edit it.';
    if(sl.variants){
      const grid=el('div','opts');
      for(let v=0;v<sl.variants;v++){
        grid.appendChild(optCard('v'+v,q({i:slide,variant:v}),'Layout '+(v+1),
          'Use this arrangement',()=>chooseVariant(slide,v)));}
      body.appendChild(grid);
      body.appendChild(el('p','hint','Choosing a layout replaces this slide\\u2019s elements and clears the alternatives.'));
    }
    const fr=document.createElement('iframe');fr.id='big';
    fr.onload=()=>fr.classList.add('rdy');
    fr.setAttribute('scrolling','no');fr.src='/slide?'+q({i:slide,edit:'1'});
    body.appendChild(fr);
    body.appendChild(el('p','hint','Edits save to the spec when you press Save + build. Speaker notes and styling are untouched.'));
    body.appendChild(feedbackPanel());
  }
  document.querySelectorAll('.tab').forEach(t=>t.classList.toggle('on',t.dataset.m===mode));
}

function feedbackPanel(){
  const box=el('div','fb');
  box.appendChild(el('h3',null,'Feedback for Claude \\u2014 slide '+(slide+1)));
  box.appendChild(el('p','sub','Describe what you want changed in your own words. Claude reads these notes and edits the spec; it does not have to be phrased as an instruction.'));
  const ta=document.createElement('textarea');
  ta.placeholder='e.g. "the three cards feel cramped, give the CLI one more room" or "cut the Simon Says bit, it lands flat"';
  box.appendChild(ta);
  const row=el('div','row');
  const add=document.createElement('button');add.textContent='Add note';
  add.onclick=async()=>{const v=ta.value.trim();if(!v)return;
    add.disabled=true;
    try{const j=await post('/api/feedback',{slide:slide,text:v});notes=j.notes;ta.value='';
      toast('Note saved');render(true);}
    catch(e){toast(e.message,true);}
    add.disabled=false;};
  row.appendChild(add);
  row.appendChild(el('span',null,'Saved immediately \\u2014 no need to press Save + build.'));
  box.appendChild(row);

  const mine=notes.filter(n=>n.slide===slide);
  if(mine.length){
    const list=el('div','notes');
    mine.forEach(n=>{
      const item=el('div','note'+(n.resolved?' done':''));
      const p=el('p');p.appendChild(el('em',null,n.resolved?'done':'open'));
      p.appendChild(document.createTextNode(n.text));
      const tog=document.createElement('button');tog.textContent=n.resolved?'reopen':'done';
      tog.onclick=async()=>{try{const j=await post('/api/feedback/resolve',{id:n.id});
        notes=j.notes;render(true);}catch(e){toast(e.message,true);}};
      const del=document.createElement('button');del.textContent='delete';
      del.onclick=async()=>{try{const j=await post('/api/feedback/delete',{id:n.id});
        notes=j.notes;render(true);}catch(e){toast(e.message,true);}};
      item.appendChild(p);item.appendChild(tog);item.appendChild(del);list.appendChild(item);});
    box.appendChild(list);
  }
  return box;
}

function toast(msg,err){const t=document.getElementById('toast');t.textContent=msg;
  t.className='on'+(err?' err':'');setTimeout(()=>t.className=err?'err':'',2600);}

async function post(path,payload){
  const r=await fetch(path,{method:'POST',
    headers:{'Content-Type':'application/json','X-Studio-Token':TOKEN},
    body:JSON.stringify(payload)});
  const j=await r.json();if(!r.ok||j.error)throw new Error(j.error||'request failed');return j;}

async function chooseVariant(i,v){
  try{await post('/api/variant',{slide:i,variant:v});
    SLIDES[i].variants=0;dirty=true;toast('Layout applied');render(true);}
  catch(e){toast(e.message,true);}}

addEventListener('message',async ev=>{
  if(!ev.data||ev.data.type!=='edit')return;
  try{await post('/api/patch',{src:ev.data.src,value:ev.data.value});dirty=true;toast('Text updated');}
  catch(e){toast(e.message,true);}});

// #edit/7 deep-links to a tab and slide, so a rebuilt page or a shared link
// comes back to what the user was looking at instead of slide 1.
function readHash(){const m=/^#(theme|persona|edit)(?:\\/(\\d+))?$/.exec(location.hash);
  if(!m)return;mode=m[1];if(m[2])slide=Math.max(0,Math.min(SLIDES.length-1,parseInt(m[2],10)-1));}
function writeHash(){history.replaceState(null,'','#'+mode+'/'+(slide+1));}
addEventListener('hashchange',()=>{readHash();render();});
document.querySelectorAll('.tab').forEach(t=>t.onclick=()=>{mode=t.dataset.m;writeHash();render();});
document.getElementById('save').onclick=async()=>{
  const b=document.getElementById('save');b.disabled=true;b.textContent='Building\\u2026';
  try{const j=await post('/api/save',{design:sel});
    toast('Saved \\u2014 '+j.written.join(', ')+(j.overflow?' \\u00b7 '+j.overflow+' overflowing':''));
    dirty=false;}
  catch(e){toast(e.message,true);}
  b.disabled=false;b.textContent='Save + build';};
document.getElementById('revert').onclick=async()=>{
  try{await post('/api/revert',{});location.reload();}catch(e){toast(e.message,true);}};
addEventListener('beforeunload',e=>{if(dirty){e.preventDefault();e.returnValue='';}});

// Apply hands the open notes to a headless Claude run, which edits the spec and
// resolves what it applied. The page goes read-only-ish while it works: the run
// owns the spec until it finishes, and the watcher reloads the page at the end.
function applying(on){const b=document.getElementById('apply');
  b.disabled=on;b.textContent=on?'Applying\\u2026':'Apply notes';}
document.getElementById('apply').onclick=async()=>{
  const open=notes.filter(n=>!n.resolved).length;
  if(!open)return toast('No open notes',true);
  if(dirty)return toast('Save + build first \\u2014 this page has unsaved picks',true);
  if(!confirm('Hand '+open+' open note'+(open>1?'s':'')+' to Claude? It will edit the spec and rebuild.'))return;
  applying(true);
  try{await post('/api/apply',{});toast('Claude is working on '+open+' note'+(open>1?'s':''));}
  catch(e){applying(false);toast(e.message,true);}};

// The spec changed on disk. Reload to show it — unless this page is holding
// unsaved picks, in which case say so and let Revert be the deliberate choice.
new EventSource('/api/events').onmessage=ev=>{
  const m=JSON.parse(ev.data);
  if(m.type==='reload'){if(dirty)toast('Spec changed on disk \\u2014 Revert to load it',true);
    else location.reload();}
  else if(m.type==='changed')toast('Spec changed on disk \\u2014 Revert to load it',true);
  else if(m.type==='broken')toast('Spec on disk will not build: '+m.message,true);
  else if(m.type==='apply'){
    if(m.state==='start')applying(true);
    else if(m.state==='log')toast(m.message);
    else if(m.state==='done'){applying(false);toast('Applied \\u2014 '+m.message);}
    else if(m.state==='error'){applying(false);toast('Apply failed: '+m.message,true);}}};
readHash();
fetch('/api/feedback').then(r=>r.json()).then(j=>{notes=j.notes||[];render();}).catch(()=>render());
</script></body></html>`;
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let d = '';
    req.on('data', (c) => {
      d += c;
      if (d.length > 2e6) { reject(new Error('payload too large')); req.destroy(); }
    });
    req.on('end', () => { try { resolve(JSON.parse(d || '{}')); } catch (e) { reject(e); } });
  });
}

function json(res, code, obj) {
  res.writeHead(code, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify(obj));
}

const server = http.createServer(async (req, res) => {
  const u = url.parse(req.url, true);
  try {
    if (req.method === 'POST' && !fromStudioPage(req)) {
      return json(res, 403, { error: 'request did not come from this studio page' });
    }
    if (req.method === 'GET' && (u.pathname === '/' || u.pathname === '/index.html')) {
      res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
      return res.end(appPage());
    }
    if (req.method === 'GET' && u.pathname === '/slide') {
      const i = parseInt(u.query.i, 10) || 0;
      res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
      return res.end(slidePage(i, u.query));
    }
    if (req.method === 'POST' && u.pathname === '/api/patch') {
      const { src, value } = await readBody(req);
      if (!Array.isArray(src)) return json(res, 400, { error: 'edit had no source path' });
      setPath(spec, ['slides'].concat(src), value);
      specDirty = true;
      return json(res, 200, { ok: true });
    }
    if (req.method === 'POST' && u.pathname === '/api/variant') {
      const { slide, variant } = await readBody(req);
      const s = spec.slides[slide];
      const v = s && s.variants && s.variants[variant];
      if (!v) return json(res, 400, { error: 'no such layout option' });
      Object.assign(s, v.slide || { elements: v.elements });
      delete s.variants;
      specDirty = true;
      return json(res, 200, { ok: true });
    }
    if (req.method === 'GET' && u.pathname === '/api/feedback') {
      return json(res, 200, { notes: loadFeedback() });
    }
    if (req.method === 'POST' && u.pathname === '/api/feedback') {
      const { slide, text } = await readBody(req);
      const body = String(text == null ? '' : text).trim();
      if (!body) return json(res, 400, { error: 'note was empty' });
      const notes = loadFeedback();
      notes.push({
        id: `n${Date.now().toString(36)}${Math.floor(Math.random() * 1e4).toString(36)}`,
        slide: typeof slide === 'number' ? slide : null,
        slideTitle: typeof slide === 'number' ? slideTitle(slide) : null,
        text: body,
        created: new Date().toISOString(),
        resolved: false,
      });
      saveFeedback(notes);
      return json(res, 200, { notes });
    }
    if (req.method === 'POST' && u.pathname === '/api/feedback/resolve') {
      const { id } = await readBody(req);
      const notes = loadFeedback();
      const note = notes.find((n) => n.id === id);
      if (!note) return json(res, 400, { error: 'no such note' });
      note.resolved = !note.resolved;
      saveFeedback(notes);
      return json(res, 200, { notes });
    }
    if (req.method === 'POST' && u.pathname === '/api/feedback/delete') {
      const { id } = await readBody(req);
      saveFeedback(loadFeedback().filter((n) => n.id !== id));
      return json(res, 200, { notes: loadFeedback() });
    }
    if (req.method === 'POST' && u.pathname === '/api/revert') {
      reloadSpec();
      return json(res, 200, { ok: true });
    }
    if (req.method === 'POST' && u.pathname === '/api/apply') {
      if (applyRun) return json(res, 409, { error: 'an apply run is already going' });
      // The run reads the spec off disk, so unsaved studio edits would be
      // invisible to it and overwritten by what it writes back.
      if (specDirty) return json(res, 400, { error: 'Save + build first — the studio is holding unsaved edits' });
      const open = loadFeedback().filter((n) => !n.resolved);
      if (!open.length) return json(res, 400, { error: 'no open notes to apply' });
      startApply();
      return json(res, 200, { started: open.length });
    }
    if (req.method === 'GET' && u.pathname === '/api/events') {
      res.writeHead(200, {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        Connection: 'keep-alive',
      });
      res.write('retry: 1000\n\n');
      // A page that loaded mid-run needs to come up with the button already busy.
      if (applyRun) res.write(`data: ${JSON.stringify({ type: 'apply', state: 'start' })}\n\n`);
      clients.add(res);
      const keepalive = setInterval(() => res.write(': ping\n\n'), 25000);
      req.on('close', () => { clearInterval(keepalive); clients.delete(res); });
      return;
    }
    if (req.method === 'POST' && u.pathname === '/api/save') {
      const { design } = await readBody(req);
      spec.design = Object.assign({}, spec.design, design);
      // Validate before touching disk: a spec that cannot lay out must never
      // replace one that can.
      const deck = layoutDeck(spec);
      const onDisk = Object.assign({}, spec);
      delete onDisk.basedir;
      const text = yaml.dump(onDisk, { lineWidth: 100, noRefs: true });
      fs.writeFileSync(specFile, text);
      // Remember what was written so the watcher does not mistake it for an
      // outside edit and reload the page out from under the save.
      specText = text;
      specDirty = false;
      const out = await new Promise((resolve) => {
        execFile(process.execPath, [path.join(__dirname, 'build_deck.js'), specFile, '--quiet'],
          (err, stdout, stderr) => resolve(err ? { error: String(stderr || err.message) } : { ok: true }));
      });
      if (out.error) return json(res, 500, { error: out.error.slice(0, 300) });
      return json(res, 200, {
        written: ['spec', 'html', 'pptx'],
        overflow: deck.slides.filter((s) => s.overflow).length,
      });
    }
    res.writeHead(404); res.end('not found');
  } catch (err) {
    json(res, 500, { error: err.message });
  }
});

// Bind to loopback only. The studio can rewrite files on disk, so it must not be
// reachable from the network.
server.listen(PORT, '127.0.0.1', () => {
  console.log(`Design studio: http://127.0.0.1:${PORT}`);
  console.log(`Editing ${specFile} — nothing is written until you press Save + build.`);
});
