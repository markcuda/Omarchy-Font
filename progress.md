# Omarchy Font — Progress Log

## Current state

The repository is on GitHub at https://github.com/markcuda/Omarchy-Font.

The public demo is deployed at https://demo-rust-rho-59.vercel.app.

The repository is intentionally small: `Omarchy Font.ttf` and `README.md`.

## What was done

1. Located the `Delta Corps Priest 1.flf` source in the public xero/figlet-fonts collection.
2. Built a custom TrueType generator that translated each FIGlet block character into vector rectangles.
3. Added full-block, upper-half, lower-half, left-half, and right-half block geometry.
4. Validated the generated file with FontTools and the system font scanner. It reports family `Omarchy Font` and printable ASCII coverage U+0020–U+007E.
5. Published the TTF to GitHub.
6. Built a static Vercel demo with editable text, size, spacing, line-height, copy, and download controls.
7. Removed the demo source from GitHub at the user’s request; the demo remains independently deployed on Vercel.

## Known failure

The live demo does not visually reproduce the target Omarchy logo style. The screenshot shows ordinary fallback/condensed text rather than the intended solid block-built glyphs. The last attempted fix changed the generated geometry from square cells to narrow terminal-proportioned cells and added slight overlap between adjacent block rows, but the result still did not match the target.

Do not treat the current TTF as visually correct merely because metadata scanners accept it. Browser rendering needs to be tested directly.

## Important target

The desired result is the solid pixel/block style shown in the supplied Omarchy references: continuous vertical and horizontal forms, no visible row seams, and proportions matching the reference wordmark. It should behave as a normal installed font, not require FIGlet line breaks, and render ordinary typed text as those block-built letters.

## Likely investigation paths

- Verify in a real browser whether `@font-face` successfully loads the TTF; the screenshot strongly suggests fallback rendering.
- Inspect browser console and network status for the font request.
- Compare one glyph, especially `O`, `M`, and `A`, against the reference at the same size.
- Validate the TTF with a browser-compatible font parser, not only `fc-scan`.
- Reconsider the conversion model from the ground up if the font loads but the contours remain unlike the reference.

## Do not assume

- Passing `fc-scan` means Chrome will accept every table in the font.
- Narrowing cell width alone solves the visual mismatch.
- The current Vercel demo source belongs in this repository; it was deliberately kept separate.
