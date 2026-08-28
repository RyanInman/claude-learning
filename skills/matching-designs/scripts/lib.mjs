// Shared helpers. Not a CLI.
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';

export function parseArgs(argv, spec) {
  const out = { ...spec.defaults };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--help' || a === '-h') { console.log(spec.help); process.exit(0); }
    if (!a.startsWith('--')) fail(`Unexpected argument "${a}".\n${spec.help}`);
    const key = a.slice(2);
    if (spec.flags.includes(key)) { out[key] = true; continue; }
    if (!spec.options.includes(key)) fail(`Unknown option --${key}. Known: ${spec.options.map(o => '--' + o).join(', ')}`);
    out[key] = argv[++i];
    if (out[key] === undefined) fail(`--${key} needs a value.`);
  }
  for (const r of spec.required) if (out[r] === undefined) fail(`Missing --${r}.\n${spec.help}`);
  return out;
}

export function fail(msg, code = 1) { console.error(msg); process.exit(code); }

export function toUrl(target) {
  return /^https?:\/\//.test(target) ? target : pathToFileURL(resolve(target)).href;
}

export const NO_MOTION_CSS = `*,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important}`;
