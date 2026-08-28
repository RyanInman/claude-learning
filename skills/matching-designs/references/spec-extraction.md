# Extracting a spec from a design image

Read this when the image resists direct reading: JPG noise, no visible grid, or near-identical colors.

## Colors

- Sample a flat region at least 8x8 px, never an edge, because antialiasing and JPG artifacts blend neighboring colors. Take the median of the region.
- Text color: sample the thickest stroke of the largest glyph. Thin strokes are lighter than the true color.
- When two colors sit within 8 RGB units of each other, treat them as one token and use the flat-region value, because the difference is noise.
- Convert to 6-digit lowercase hex.

## Sizes and spacing

- Measure the cap height of a capital letter. Divide it by 0.7 to estimate `font-size` for most sans-serif fonts. Round to the nearest common size: 12, 14, 16, 18, 20, 24, 32, 40, 48, 64.
- Measure gaps between blocks edge to edge. Snap to the nearest 4px, because design tools use a 4 or 8 px grid and an off-grid value is a measurement error.
- Record a container's padding from its edge to the first content pixel.
- Record heights only for fixed bars (header, footer, nav). Content heights depend on text and wrap.

## Selectors

- Give each region a class in the page you will build (`.hero`, `.cta`, `.cards`). Use the same class in the spec, because a selector that matches nothing stops the token check.
- Check one representative per repeated element (`.card:first-child`), not each instance.

## Viewport

- Use the image's exact pixel size.
- For a retina 2x export, downscale the PNG first, because `check.mjs` captures at the image's pixel size. On macOS run `sips -z 900 1440 design.png`. Elsewhere run `magick design.png -resize 50% design.png`. Then measure sizes on the downscaled image.
