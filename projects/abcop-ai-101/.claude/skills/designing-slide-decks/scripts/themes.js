'use strict';
// Design tokens. A "design" is one THEME (palette + type pairing) plus one
// PERSONALITY (density/scale). The studio picker varies exactly these two axes,
// so any pick is reproducible from the spec's `design:` block alone.

// Fonts are restricted to faces present on both macOS and Windows PowerPoint.
// A font the renderer substitutes silently is a layout bug you only see after
// sending the deck to someone else.
const SAFE_FONTS = [
  'Arial', 'Helvetica', 'Verdana', 'Trebuchet MS', 'Tahoma',
  'Georgia', 'Times New Roman', 'Courier New', 'Consolas',
];

const THEMES = {
  ember: {
    label: 'Ember',
    blurb: 'Warm charcoal and terracotta. Grounded, workshop-like.',
    sans: 'Arial', mono: 'Courier New',
    bg: 'FFFFFF', text: '2A2621', muted: '6E675F', line: 'E4DFD9', fill: 'F4F1ED',
    accent: 'C96442', accentText: 'FFFFFF', tint: 'F6E7DE',
    dark: '26221E', darkText: 'F2EDE6', darkMuted: 'B8B1A8', darkLine: '4A443C',
    panel: '1A1714', panelBar: '332E28', code: 'EDE6DD', codeDim: '9C948A',
    ok: '3E7C4F', bad: 'B0442F', okCode: '8FCB9B', badCode: 'E8938A',
  },
  ink: {
    label: 'Ink',
    blurb: 'Near-black on cool white with a cyan signal. Precise, technical.',
    sans: 'Helvetica', mono: 'Consolas',
    bg: 'FFFFFF', text: '14181D', muted: '5C6672', line: 'DFE4EA', fill: 'F3F5F8',
    accent: '0E7C86', accentText: 'FFFFFF', tint: 'DCF0F2',
    dark: '14181D', darkText: 'EEF2F6', darkMuted: 'A3AEBA', darkLine: '39424D',
    panel: '0D1117', panelBar: '242C36', code: 'E6EDF3', codeDim: '8B949E',
    ok: '2F7D4F', bad: 'B23A34', okCode: '7EE787', badCode: 'FF9492',
  },
  slate: {
    label: 'Slate',
    blurb: 'Cool grey with amber highlights. Corporate but not sterile.',
    sans: 'Trebuchet MS', mono: 'Courier New',
    bg: 'FFFFFF', text: '23282E', muted: '646C75', line: 'E1E5E9', fill: 'F2F4F6',
    accent: 'B7791F', accentText: 'FFFFFF', tint: 'FAEDD4',
    dark: '23282E', darkText: 'F0F2F4', darkMuted: 'AEB5BC', darkLine: '444B53',
    panel: '181C21', panelBar: '2E343B', code: 'E9EDF1', codeDim: '939BA3',
    ok: '3B7A4E', bad: 'A8412F', okCode: '90CFA0', badCode: 'EE9C8E',
  },
  mono: {
    label: 'Mono',
    blurb: 'Near-black on white, one red accent. Austere, high contrast.',
    sans: 'Verdana', mono: 'Consolas',
    bg: 'FFFFFF', text: '111111', muted: '5E5E5E', line: 'E0E0E0', fill: 'F5F5F5',
    accent: 'D62828', accentText: 'FFFFFF', tint: 'FBE3E3',
    dark: '111111', darkText: 'F4F4F4', darkMuted: 'A8A8A8', darkLine: '3A3A3A',
    panel: '0A0A0A', panelBar: '242424', code: 'EDEDED', codeDim: '8F8F8F',
    ok: '2E7D46', bad: 'C62828', okCode: '86D39B', badCode: 'F19191',
  },
  forest: {
    label: 'Forest',
    blurb: 'Deep green on bone, serif headlines. Calm and considered.',
    sans: 'Georgia', mono: 'Courier New',
    bg: 'FBFAF6', text: '1C2620', muted: '5D6B62', line: 'DFE3DA', fill: 'EFF2EB',
    accent: '2F6B4F', accentText: 'FFFFFF', tint: 'DCEBE0',
    dark: '16221B', darkText: 'F0F4EE', darkMuted: 'A9B7AC', darkLine: '3C4A40',
    panel: '101A14', panelBar: '253328', code: 'E8EFE6', codeDim: '8FA093',
    ok: '2F7D4F', bad: 'A8412F', okCode: '8FD3A3', badCode: 'EC9A8B',
  },
  violet: {
    label: 'Violet',
    blurb: 'Indigo on cool white, compact sans. Modern and product-like.',
    sans: 'Tahoma', mono: 'Consolas',
    bg: 'FFFFFF', text: '1A1726', muted: '5F5A73', line: 'E3E0EC', fill: 'F4F2F9',
    accent: '5B3FD6', accentText: 'FFFFFF', tint: 'E6E0FB',
    dark: '1A1726', darkText: 'F1EFF8', darkMuted: 'AEA8C2', darkLine: '3E3956',
    panel: '13111C', panelBar: '272235', code: 'EBE8F5', codeDim: '948DAB',
    ok: '2F7D5C', bad: 'B03A5B', okCode: '89D8B4', badCode: 'F292AC',
  },
  carbon: {
    label: 'Carbon',
    blurb: 'Graphite and hazard orange. Industrial, built for dense technical decks.',
    sans: 'Helvetica', mono: 'Consolas',
    bg: 'F7F7F5', text: '1B1D1E', muted: '5A5F62', line: 'DCDEDC', fill: 'ECEEEC',
    accent: 'E2621B', accentText: 'FFFFFF', tint: 'FBE4D5',
    dark: '1B1D1E', darkText: 'F2F3F2', darkMuted: 'A6ABAC', darkLine: '3B3F40',
    panel: '111314', panelBar: '272A2B', code: 'EDEFEE', codeDim: '8D9294',
    ok: '3C7A50', bad: 'B4432C', okCode: '8CCFA0', badCode: 'F09A85',
  },
  press: {
    label: 'Press',
    blurb: 'Serif headlines on warm paper with ultramarine. Editorial.',
    sans: 'Georgia', mono: 'Courier New',
    bg: 'FBF9F5', text: '1F1D1A', muted: '655F57', line: 'E2DCD2', fill: 'F2EEE6',
    accent: '2D4A9E', accentText: 'FFFFFF', tint: 'DFE5F5',
    dark: '1F1D1A', darkText: 'F5F1EA', darkMuted: 'B5AEA3', darkLine: '474139',
    panel: '17150F', panelBar: '2F2A22', code: 'F0EBE1', codeDim: '9A9287',
    ok: '3A6E4C', bad: 'A03C2E', okCode: '92C7A1', badCode: 'E79A8C',
  },
};

// Personality scales type and air. Same spec, same content, different pacing.
const PERSONALITIES = {
  technical: {
    label: 'Technical',
    blurb: 'Dense and utilitarian. More per slide, tighter rhythm.',
    titleSize: 30, kickerSize: 11, subtitleSize: 14, bodySize: 13, codeSize: 12,
    scale: 1.0, elementGap: 0.24, contentTop: 0.42, margin: 0.58,
    gapAfterTitle: 0.24, titleWeight: true, kickerRule: false, vcenter: false,
  },
  keynote: {
    label: 'Keynote',
    blurb: 'Sparse and large. Fewer words, lots of air, reads from the back.',
    titleSize: 40, kickerSize: 12, subtitleSize: 17, bodySize: 15, codeSize: 13,
    scale: 1.14, elementGap: 0.4, contentTop: 0.72, margin: 0.85,
    gapAfterTitle: 0.44, titleWeight: true, kickerRule: false, vcenter: true,
  },
  editorial: {
    label: 'Editorial',
    blurb: 'Magazine pacing. Rules under kickers, generous margins, calm scale.',
    titleSize: 34, kickerSize: 11, subtitleSize: 16, bodySize: 14, codeSize: 12,
    scale: 1.06, elementGap: 0.32, contentTop: 0.56, margin: 0.95,
    gapAfterTitle: 0.36, titleWeight: false, kickerRule: true, vcenter: true,
  },
};

const DEFAULT_DESIGN = { theme: 'ember', personality: 'technical' };

function resolveDesign(design) {
  const d = Object.assign({}, DEFAULT_DESIGN, design || {});
  const theme = THEMES[d.theme];
  if (!theme) {
    throw new Error(
      `Unknown theme "${d.theme}". Available: ${Object.keys(THEMES).join(', ')}`);
  }
  const persona = PERSONALITIES[d.personality];
  if (!persona) {
    throw new Error(
      `Unknown personality "${d.personality}". Available: ${Object.keys(PERSONALITIES).join(', ')}`);
  }
  // `overrides` lets a spec nudge single tokens without forking a whole theme.
  const tokens = Object.assign({}, theme, d.overrides || {});
  for (const [k, v] of Object.entries(d.overrides || {})) {
    if (/color|bg|text|accent|tint|dark|panel|code|line|fill|ok|bad/i.test(k)
        && typeof v === 'string' && !/^[0-9A-Fa-f]{6}$/.test(v)
        && !SAFE_FONTS.includes(v)) {
      throw new Error(
        `Design override "${k}: ${v}" is not a 6-digit hex without "#". ` +
        `A "#" prefix corrupts the pptx file.`);
    }
  }
  return {
    key: d.theme, personaKey: d.personality, t: tokens, p: persona,
    // Deck-wide vertical-centring override; individual slides may still opt out.
    vcenter: d.vcenter,
  };
}

module.exports = { THEMES, PERSONALITIES, DEFAULT_DESIGN, SAFE_FONTS, resolveDesign };
