# Design System: Horizonte Cerrado

## Overview
- **Display Name:** Horizonte Cerrado
- **Project:** TDS LMS Lite v2
- **Asset ID:** `415bb7ccbae543ccb3451d9539124914`

## Theme Configuration
- **Color Mode:** LIGHT
- **Primary Color:** `#007BA7`
- **Secondary Color:** `#E9B44C`
- **Tertiary Color:** `#A44A3F`
- **Neutral Color:** `#4D4639`
- **Font:** LEXEND (Headings & Body)
- **Roundness:** ROUND_EIGHT

### Named Colors Palette
| Token | Hex |
|---|---|
| Background | `#fff8f2` |
| Primary | `#006184` |
| Primary Container | `#007ba7` |
| Secondary | `#7c5800` |
| Secondary Container | `#fdc65c` |
| Tertiary | `#953f34` |
| Tertiary Container | `#b4564a` |
| Surface | `#fff8f2` |
| Surface Container High | `#f2e7d5` |
| Surface Container Highest | `#ede1cf` |
| On Surface | `#201b10` |
| Outline | `#6f787f` |

## Specification Markdown
# Design System Specification: The Sun-Drenched Horizon

## 1. Overview & Creative North Star: "Organic Editorial"
The Brazilian Cerrado is not a place of rigid lines or sterile surfaces; it is a landscape of vast horizons, gnarled silhouettes, and sudden, vibrant blooms. This design system moves away from the "standard tech" aesthetic toward **Organic Editorial**. 

Our North Star is the "Sun-Drenched Horizon." We achieve this through:
*   **Intentional Asymmetry:** Breaking the 12-column grid with overlapping elements that mimic the natural scatter of Ipe petals.
*   **Atmospheric Depth:** Using tonal layering instead of borders to create a sense of heat-haze and physical stacking.
*   **High-Contrast Warmth:** Pairing the deep sky blue (`primary`) with the earthy terracotta (`tertiary`) to create a visual tension that feels premium and intentional.

## 2. Color & Atmospheric Layering
The palette is rooted in the "Golden Hour." Every surface should feel like it’s being struck by low-latitude sunlight.

### The "No-Line" Rule
**Explicit Instruction:** Designers are prohibited from using 1px solid borders for sectioning. Boundaries must be defined solely through background color shifts. To separate a navigation bar from a hero section, transition from `surface` to `surface-container-low`.

### Surface Hierarchy & Nesting
Treat the UI as a series of physical layers—like stacked sheets of fine, handmade paper.
*   **Base:** `surface` (#fff8f2) is our canvas.
*   **Subtle Recess:** Use `surface-container-low` (#fef2e0) for secondary content areas.
*   **Elevation:** Use `surface-container-highest` (#ede1cf) for high-importance cards.
*   **The Glass Rule:** For floating elements (modals, dropdowns), use `surface` at 80% opacity with a `backdrop-filter: blur(12px)`. This mimics the shimmering air of the Cerrado.

### Signature Textures
Apply a subtle linear gradient to main CTAs transitioning from `primary` (#006184) to `primary_container` (#007ba7) at a 135-degree angle. This provides a "soul\" and depth that flat hex codes cannot achieve.

## 3. Typography: The Warm Lexend
We use **Lexend** exclusively. To avoid the \"geometric-cold\" feel, we lean into warmer weights and generous tracking for headings.

*   **Display (lg/md/sm):** Set with -2% letter spacing. Use `on_surface` (#201b10). These are your \"Horizon\" moments—wide, breathable, and commanding.
*   **Headlines:** Use `primary` (#006184) for headlines to draw the eye like a clear sky.
*   **Body (lg/md):** Use `on_surface_variant` (#3f484e) for long-form text. The slight gray-blue shift reduces eye strain against the sun-drenched `surface`.
*   **Labels:** Always uppercase with +5% letter spacing. Use `tertiary` (#953f34) for small labels to inject the \"earthy red\" energy into functional details.

## 4. Elevation & Depth: Tonal Layering
Traditional shadows are too \"digital.\" We use environment-based depth.

*   **The Layering Principle:** Place a `surface_container_lowest` (#ffffff) card on a `surface_container` (#f8ecda) background. The contrast alone creates a soft, natural lift.
*   **Ambient Shadows:** If a floating effect is required (e.g., a FAB), use shadow color of `on_secondary_container` (#745200) at 6% opacity with a 32px blur. It should look like a soft shadow cast on sand, not a black glow.
*   **The \"Ghost Border\" Fallback:** If a border is required for accessibility, use `outline_variant` (#bfc8cf) at 15% opacity. Never use 100% opaque borders.

## 5. Components

### Buttons: The \"Pebble\" Shape
*   **Primary:** High-roundness (`xl`: 1.5rem). Use the `primary` to `primary_container` gradient. Text is `on_primary`.
*   **Secondary:** `secondary_container` (#fdc65c) with `on_secondary_container` text. This is our \"Golden Ipe\" state.
*   **Tertiary:** No background. Bold Lexend text in `tertiary` (#953f34).

### Cards: The \"Terracotta\" vessels
*   **Style:** No borders. Use `surface-container-low` for card body. 
*   **Interaction:** On hover, card should transition to `surface-container-highest` and shift -4px Y-axis.
*   **Rule:** Forbid divider lines within cards. Use 24px of vertical white space (from spacing scale) to separate the header from the body.

### Input Fields: Sun-Bleached Solots
*   **Background:** `surface_container_high` (#f2e7d5).
*   **Active State:** A 2px bottom-only border in `secondary` (#7c5800). No full-box focus ring; we want to maintain the \"horizontal\" feel of the Cerrado.

### Chips: Organic Seeds
*   **Shape:** `full` (9999px) for soft, organic seed-like appearance.
*   **Color:** Use `secondary_fixed` (#ffdea7) for unselected and `primary` for selected states.

## 6. Do’s and Don’ts

### Do:
*   **Do** embrace negative space. The Cerrado is vast; your layout should be too.
*   **Do** overlap images and text. Let photo of dry grass bleed into a `surface_container` area.
*   **Do** use `tertiary` (#953f34) for callouts and error states to maintain earthy, sun-baked theme.

### Don't:
*   **Don't** use pure black (#000000) or pure white (#FFFFFF) except for `surface_container_lowest`.
*   **Don't** use 90-degree sharp corners. Everything should have at least `DEFAULT` (0.5rem) radius to feel organic.
*   **Don't** use \"Card-in-Card\" layouts. Use background tonal shifts to indicate nesting, never nested borders.
