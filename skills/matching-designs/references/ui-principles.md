# UI principles for gaps the image leaves open

Read this only for a decision the design image does not settle. Where the image shows a value, the image wins.

## Spacing

- Use one scale: 4, 8, 12, 16, 24, 32, 48, 64, 96 px. Pick the step nearest the measured value.
- Space related items closer than unrelated ones. Label to field: 8. Field to next field: 16. Section to section: 48 or more.
- Keep horizontal container padding equal on both sides.

## Type

- Use at most three sizes per screen region: heading, body, caption, because a fourth size reads as a new hierarchy level the design did not draw.
- Set body line-height at 1.5x font-size. Set heading line-height at 1.1 to 1.2x.
- Keep body measure between 45 and 75 characters. Cap a paragraph's `max-width` around 60ch.
- Pair one weight jump (400 to 600 or 700) with one size jump for a heading. Two jumps at once look louder than the design intended.

## Color and contrast

- Body text on white needs at least 4.5:1 contrast. Secondary text at `#475569` or darker passes on white. `#94a3b8` fails for body copy and works for captions only.
- Use one accent color for primary actions. Give secondary actions a border and the text color, not a second accent, because two accents compete for the primary action's attention.
- Keep borders at 1px in a gray between `#e2e8f0` and `#cbd5e1` on white.

## Hierarchy

- Put one primary action per region. Make it the highest-contrast element.
- Align text to a common left edge. Center only what the design centers.
- Give cards the same height in a row, because ragged rows read as broken.
