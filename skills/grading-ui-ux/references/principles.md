# Founding UI/UX principles

Cite these IDs in every option's `principles` list, because a change that cannot name its principle is taste, not design. One line per principle: ID, name, what it demands, and the test that shows a violation.

## Contents

- [Nielsen's 10 usability heuristics (N1-N10)](#nielsens-10-usability-heuristics)
- [Gestalt perception (G1-G6)](#gestalt-perception)
- [Interaction laws (L1-L8)](#interaction-laws)
- [Accessibility, WCAG 2.2 (W1-W7)](#accessibility-wcag-22)
- [Typography and spacing (T1-T6)](#typography-and-spacing)
- [Content and structure (C1-C6)](#content-and-structure)

## Nielsen's 10 usability heuristics

- **N1 Visibility of system status.** Show what the system is doing within a reasonable time. Violation test: an action gives no visible response (no loading state, no saved indicator, no active-tab marker).
- **N2 Match between system and real world.** Use the user's words and conventions, not internal jargon. Violation test: labels like "Submit query" or "Entity" where the user would say "Search" or "Customer".
- **N3 User control and freedom.** Provide undo, cancel, and clear exits. Violation test: a modal or flow with no close or back route.
- **N4 Consistency and standards.** Same thing looks and behaves the same everywhere; follow platform conventions. Violation test: two button styles for the same action, or a link styled like a button.
- **N5 Error prevention.** Prevent errors before they happen with constraints, defaults, and confirmation for destructive actions. Violation test: free-text date entry, a Delete button with no confirmation.
- **N6 Recognition rather than recall.** Keep options, history, and context visible. Violation test: the user must remember a code, path, or earlier screen to continue.
- **N7 Flexibility and efficiency of use.** Offer accelerators for experts without burdening novices. Violation test: no keyboard shortcuts, no bulk action, no defaults for a repeated task.
- **N8 Aesthetic and minimalist design.** Every element competes for attention; remove what does not serve the task. Violation test: decorative elements, redundant copy, or more than one primary call to action per view.
- **N9 Help users recognize, diagnose, and recover from errors.** Error messages in plain language that say what went wrong and how to fix it. Violation test: "Error 400", a red border with no text, an error shown far from the field.
- **N10 Help and documentation.** Make help findable and task-focused. Violation test: an unexplained setting with no hint or tooltip.

## Gestalt perception

- **G1 Proximity.** Elements close together read as a group. Violation test: a label sits equidistant from two fields.
- **G2 Similarity.** Elements that look alike read as the same kind. Violation test: two unrelated things share a color or shape, or related things differ.
- **G3 Continuity.** The eye follows aligned lines and edges. Violation test: misaligned left edges, ragged columns.
- **G4 Closure.** Partial shapes read as whole; a cropped card implies more content. Violation test: a horizontal list with no cue that it scrolls.
- **G5 Figure and ground.** The focus element must separate from its background. Violation test: a modal with no overlay, a card with the same color as the page.
- **G6 Common region.** A border or background groups whatever sits inside it. Violation test: a card border encloses unrelated controls.

## Interaction laws

- **L1 Fitts's law.** Time to hit a target depends on its size and distance. Violation test: a small target far from the cursor's likely position; primary actions smaller than 44x44 px on touch.
- **L2 Hick's law.** Decision time grows with the number of choices. Violation test: more than about 7 top-level options with no grouping.
- **L3 Miller's chunking.** Working memory holds about 4 to 7 chunks. Violation test: a 16-digit field with no grouping, a form with 20 ungrouped inputs.
- **L4 Jakob's law.** Users expect your site to work like the sites they already use. Violation test: cart icon on the left, logo not linking home, search in an unexpected spot.
- **L5 Aesthetic-usability effect.** Users judge attractive interfaces as easier to use, which buys tolerance for minor issues. Violation test: inconsistent radii, shadows, or spacing that read as unfinished.
- **L6 Von Restorff effect.** The item that differs is the one remembered. Violation test: the primary action does not visually differ from secondary ones.
- **L7 Doherty threshold.** Keep response under 400 ms or show progress. Violation test: an action that blocks with no spinner, skeleton, or optimistic update.
- **L8 Progressive disclosure.** Show the essential first; reveal detail on demand. Violation test: advanced options on the same level as the core task.

## Accessibility, WCAG 2.2

- **W1 Contrast.** Text contrast ratio at least 4.5:1 (3:1 for text 24 px or larger, or 19 px bold); UI component and graphic contrast at least 3:1. Violation test: light gray placeholder text as the only label, white text on a light brand color.
- **W2 Target size.** Interactive targets at least 24x24 CSS px (WCAG 2.2 AA), 44x44 recommended for touch. Violation test: icon buttons under 24 px, links stacked with no spacing.
- **W3 Focus visible.** Keyboard focus has a visible indicator with 3:1 contrast. Violation test: `outline: none` with no replacement.
- **W4 Labels and names.** Every input has a programmatic label; icon buttons have an accessible name. Violation test: placeholder-only inputs, `<button><svg/></button>` with no `aria-label`.
- **W5 Non-text content.** Images carry alt text or are marked decorative. Violation test: `<img>` with no `alt`.
- **W6 Use of color.** Color is never the only carrier of meaning. Violation test: a required field marked by red color only, a status shown by a colored dot only.
- **W7 Semantics and order.** Headings nest in order, landmarks exist, reading order matches visual order. Violation test: `<div onClick>` acting as a button, h1 followed by h4.

## Typography and spacing

- **T1 Measure.** Body text lines run 45 to 75 characters. Violation test: a paragraph that spans a 1400 px container.
- **T2 Line height.** Body text line height 1.4 to 1.6; headings 1.1 to 1.3. Violation test: 16 px text at line-height 1.0.
- **T3 Type scale.** Sizes come from one scale (for example 12, 14, 16, 20, 24, 32) with at most 4 to 5 sizes per screen. Violation test: 13, 15, 17, and 18 px all present.
- **T4 Minimum size.** Body text at least 16 px on web, 14 px for secondary text. Violation test: 11 px body copy.
- **T5 Spacing grid.** Margins and padding come from one base unit (4 or 8 px). Violation test: 13 px, 18 px, and 22 px gaps on one screen.
- **T6 Alignment.** Text and controls share a small number of alignment axes. Violation test: centered headings over left-aligned body and right-aligned buttons with no rationale.

## Content and structure

- **C1 Visual hierarchy.** Size, weight, color, and position signal importance; one focal point per view. Violation test: everything bold, or the page title smaller than a card title.
- **C2 Scanning patterns.** Users scan in F or Z patterns on text-heavy and sparse layouts respectively. Violation test: the key action sits in a dead zone (bottom left of a sparse page).
- **C3 Plain language.** Short sentences, active voice, specific verbs on buttons. Violation test: "OK" or "Submit" where "Save changes" is meant.
- **C4 Information scent.** Links and headings predict what follows. Violation test: "Click here", "Learn more" with no object.
- **C5 Empty, loading, and error states.** Every data view has designed empty, loading, and error states. Violation test: a blank table with no message when there are no rows.
- **C6 Real-world analog.** The screen borrows the structure of the physical or established thing it replaces, so users bring working knowledge with them (a food-ordering page reads as a menu joined to a storefront; a ticket app reads as a boarding pass). Violation test: a menu with no sections or item codes, a checkout with no order summary, a settings page laid out like a marketing site.
