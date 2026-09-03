# CSS and Styling

Conventions for CSS and SCSS that hold up across Angular, React, Next.js, and Vue. The goal is styling that stays predictable as the codebase grows: one source of truth for design decisions, low specificity, and layout that expresses intent.

## Design tokens are the source of truth

- Define color, spacing, typography, radius, shadow, and z-index as design tokens, exposed as CSS custom properties.
- Components read tokens. They do not hardcode hex values, pixel offsets, or font stacks.
- Change a token in one place and the whole app follows. That is the point of having them.

```css
:root {
  --color-surface: #ffffff;
  --color-text: #1a1a1a;
  --space-2: 0.5rem;
  --space-4: 1rem;
  --radius-md: 0.5rem;
}
```

## Consistent scales

- Spacing, type sizes, and colors come from a defined scale, not from whatever number looked right.
- Use a spacing step (4px or 8px based) and compose from it. Reject one-off values like `13px` or `27px`.
- Font sizes and line heights come from a type scale, referenced by token.

## Layout with flexbox and grid

- Flexbox for one-dimensional layout (a row of actions, a toolbar). Grid for two-dimensional layout (page regions, card galleries).
- Do not lay out with `float` or with `position: absolute`. Absolute positioning is for overlays and decoration relative to a positioned ancestor, not for arranging content.
- Prefer `gap` over margins for spacing between flex and grid children.

## Logical properties

- Use logical properties so layout adapts to writing direction: `margin-inline`, `padding-block`, `inset-inline-start`, `border-inline-end`.
- Avoid `left`/`right`/`margin-left` for layout that should mirror in RTL. Logical properties flip for free.

## Container queries

- Style a component by the space it actually sits in, using container queries, when the component is reused in columns, sidebars, and full-width slots.
- Reserve viewport media queries for genuinely page-level concerns. A card should respond to its container, not to the window.

```css
.card-list { container-type: inline-size; }

@container (min-width: 30rem) {
  .card { grid-template-columns: auto 1fr; }
}
```

## Parent and state selection with :has()

- Use `:has()` to style a parent from its children or from sibling state: `.field:has(input:invalid)`, `.card:has(img)`. It removes a whole class of state-mirroring JavaScript.
- It is widely available across current browsers. It counts toward specificity like any other pseudo-class, so keep the arguments simple.

## Keep specificity low and flat

- Aim for a single class selector per rule. Avoid IDs and long descendant chains.
- Do not nest selectors more than one level deep. Deep nesting inflates specificity and couples styles to markup structure.
- No `!important` outside genuine utility overrides. If you need it to win, the real problem is specificity elsewhere.
- Pick one naming approach and hold to it: BEM for component classes, or a utility-class approach. Do not blend them at random.

## Scope and colocate

- Keep a component's styles next to the component and scoped to it: CSS Modules, Vue `scoped`, Angular view encapsulation, or a scoped naming convention.
- Global styles are reserved for resets, tokens, and base element defaults. Everything else is local to a component.

## Responsive, mobile-first

- Write the base styles for small screens, then layer enhancements upward with `min-width` queries.
- Let content dictate breakpoints. Add a breakpoint where the layout breaks, not at fixed device widths.

## Dark mode through tokens

- Implement theming by swapping token values, not by writing a second set of component rules.
- Redefine tokens under a theme selector or `prefers-color-scheme`. Components stay untouched.

```css
@media (prefers-color-scheme: dark) {
  :root {
    --color-surface: #121212;
    --color-text: #f2f2f2;
  }
}
```

## Motion

- Wrap non-essential animation in `prefers-reduced-motion: no-preference`, or disable it under `reduce`. Do not ship motion that ignores the setting.

## Do / Instead of

| Do | Instead of |
|---|---|
| `var(--space-4)` | `margin: 16px` |
| `gap` on a flex/grid parent | margins on each child |
| `display: grid` for page regions | `float` or absolute positioning |
| `margin-inline-start` | `margin-left` for mirrorable layout |
| container query for a reused component | viewport media query |
| `:has()` for parent/state styling | a JS class toggle mirroring child state |
| single class selector | `#main .list .item a span` |
| swap token values for a theme | duplicate rules per theme |
| `min-width` mobile-first queries | `max-width` desktop-first queries |
| tokens for every color/size | inline hex and magic numbers |
