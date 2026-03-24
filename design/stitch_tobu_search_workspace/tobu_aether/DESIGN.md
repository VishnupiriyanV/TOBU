# Design System Specification: The Kinetic Studio

## 1. Overview & Creative North Star: "The Digital Obsidian"
This design system moves away from the "SaaS-blue" ubiquity of the past decade toward a "Digital Obsidian" aesthetic. It is inspired by the focused, high-density environments of IDEs like VS Code and knowledge-management tools like Obsidian, but elevated through an editorial lens. 

**The Creative North Star: The Curated Workspace.**
We treat the UI not as a web page, but as a professional instrument. The aesthetic is defined by "Organic Brutalism"—a rigid, high-density functional grid softened by sophisticated lavender accents and deep, tonal layering. We break the "template" look by favoring structural depth over decorative lines and using typography as a primary architectural element.

---

## 2. Colors & Tonal Depth
The palette is rooted in a core of `#131313` (Surface), using a sophisticated lavender (`#c9bfff`) as the surgical strike of color.

### The "No-Line" Rule
**Explicit Instruction:** Designers are prohibited from using 1px solid borders to section content. Boundaries must be defined solely through background color shifts. Use `surface-container-low` for secondary regions and `surface-container-high` for interactive elements. This creates a "milled" look, where the UI feels carved out of a single block of material rather than assembled from boxes.

### Surface Hierarchy & Nesting
Treat the UI as a series of physical layers. Use the following hierarchy to define depth:
*   **Base Layer:** `surface` (#131313) – The primary workspace.
*   **Sunken Layer:** `surface-container-lowest` (#0e0e0e) – For sidebars or "well" containers.
*   **Raised Layer:** `surface-container-low` (#1c1b1b) – For main content cards.
*   **Active Layer:** `surface-container-high` (#2a2a2a) – For hovered states or active panels.

### The "Glass & Signature Texture" Rule
To move beyond a flat "dark mode," use Glassmorphism for floating overlays (Modals, Popovers). Apply a backdrop-blur of `12px` to `surface-container` colors at 80% opacity. 
*   **Signature Gradient:** For primary CTAs, use a linear gradient from `primary` (#c9bfff) to `primary-container` (#9d8cff) at a 135° angle to add "soul" and dimension.

---

## 3. Typography
We utilize a dual-typeface system to separate human-readable interface elements from machine-like data density.

*   **UI Interface (IBM Plex Sans):** Used for all navigation, headers, and labels. It provides a technical, authoritative "Swiss" feel.
    *   **Headline-LG:** 2.0rem / Tracking -0.02em (Commanding presence).
    *   **Title-SM:** 1.0rem / Medium weight (The standard for section headers).
*   **Data & Code (JetBrains Mono):** Used for all numerical values, metadata, and status logs.
    *   **Body-SM:** 0.75rem (High-density data tables).
*   **Editorial Hierarchy:** Use `primary` lavender for `label-md` elements to highlight key metadata without increasing font size.

---

## 4. Elevation & Depth: Tonal Layering
Traditional drop shadows are largely banned in this system. We achieve "lift" through color.

*   **The Layering Principle:** Place a `surface-container-lowest` (#0e0e0e) card on a `surface-container-low` (#1c1b1b) section to create a soft, natural "recessed" look.
*   **Ambient Shadows:** If a floating element (like a context menu) requires a shadow, use a 32px blur at 8% opacity using the `on-surface` color. This mimics ambient light occlusion rather than a harsh artificial shadow.
*   **The "Ghost Border" Fallback:** If accessibility requires a stroke, use `outline-variant` (#484552) at **15% opacity**. Never use 100% opaque borders.

---

## 5. Components

### Buttons & Inputs
*   **Primary Action:** A gradient fill (`primary` to `primary-container`) with `on-primary` text. No border. Radius: `md` (0.375rem).
*   **Secondary/Ghost:** `surface-container-highest` background. Lavender text (`primary`).
*   **Input Fields:** Use `surface-container-lowest` as the fill. On focus, the background transitions to `surface-container-high` with a `primary` bottom-border (2px) only.

### Chips & Status Indicators
*   **Status Chips:** Never use solid fills. Use a `surface-container-high` background with a 4px circular dot of the status color (e.g., `primary` for active, `error` for critical) and `JetBrains Mono` for the label.

### Lists & Navigation
*   **Active State:** Use a "Side-Car" indicator—a 3px vertical pill of `primary` lavender on the left edge of the list item, with the item background shifting to `surface-container-low`.
*   **Forbid Dividers:** Use `0.9rem` (Spacing 4) of vertical whitespace to separate list items instead of lines.

### Specialized Workspace Components
*   **The Breadcrumb Rail:** High-density `JetBrains Mono` text at `label-sm` scale, separated by a forward slash `/` in `outline-variant`.
*   **The Property Grid:** A two-column layout using `surface-container-lowest` for keys and `surface` for values, creating a "zebra-striping" effect through background shifts rather than lines.

---

## 6. Do’s and Don’ts

### Do
*   **Do** lean into high-density layouts. Users of this system value information over "breathing room."
*   **Do** use the `primary` lavender color sparingly. It should feel like a neon light in a dark room—intentional and functional.
*   **Do** use `JetBrains Mono` for any value that can be calculated (dates, counts, IDs).

### Don't
*   **Don't** use `#000000` for backgrounds. Use the `surface` token (#131313) to maintain tonal depth.
*   **Don't** use rounded-full (pills) for buttons. Stick to the `md` (0.375rem) or `sm` (0.125rem) radius to maintain the architectural, "engineered" look.
*   **Don't** use standard blue for links. All interactive triggers must be Lavender (`primary`) or Underlined Neutral.

---

## 7. Token Reference Summary
*   **Primary Accent:** `#c9bfff` (Lavender)
*   **Workspace Base:** `#131313`
*   **UI Font:** IBM Plex Sans
*   **Data Font:** JetBrains Mono
*   **Default Radius:** `0.25rem` (0.4rem for containers)