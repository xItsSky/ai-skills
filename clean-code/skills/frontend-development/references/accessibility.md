# Accessibility

Accessibility is part of the definition of done for any UI change, not a later pass. The rules below track WCAG 2.2 AA and are framework-agnostic. Apply them whenever you add or change markup, interaction, or visual state.

## Semantic HTML first

- Reach for the real element before anything else: `button`, `a`, `nav`, `header`, `main`, `ul`/`ol`/`li`, `table`, `label`, `fieldset`.
- One `h1` per page. Headings descend without skipping levels. They describe structure, not font size.
- A control that navigates is an `a` with an `href`. A control that acts is a `button`. Never a clickable `div`.
- Native elements bring focus, keyboard behavior, and the correct role for free. A `div` gives you none of it and you end up rebuilding all of it by hand.

## ARIA fills gaps, it does not replace semantics

- No ARIA is better than wrong ARIA. A misused role breaks the experience more than a missing one.
- Never override a native role. Do not put `role="button"` on a `button` or `role="link"` on an `a`.
- Use ARIA for what HTML cannot express: `aria-expanded`, `aria-current`, `aria-live`, `aria-controls`, `aria-selected`.
- If you build a widget from generic elements (tabs, combobox, tree), implement the full ARIA Authoring Practices pattern including keyboard, or use a vetted headless library.

## Keyboard

- Every interactive element is reachable and operable with the keyboard alone. Tab to reach, Enter/Space to activate, Escape to dismiss, arrows to move within a composite widget.
- Do not add positive `tabindex` values. Order comes from DOM order. Use `tabindex="0"` to make a custom widget focusable and `tabindex="-1"` for programmatic focus only.
- Never trap the user. If focus enters a dialog, Escape and a close action must let it out.
- Do a full keyboard pass on any new UI before you consider it done.

## Focus visibility and order

- Keep a visible focus indicator. Never `outline: none` without an equally clear replacement. Prefer `:focus-visible` so it shows for keyboard users.
- Keep the focused element visible. Sticky headers, footers, and cookie banners must not cover it (WCAG 2.2 Focus Not Obscured). Watch `scroll-margin` and sticky offsets.
- Focus order follows reading order. If the visual order and DOM order disagree, fix the DOM, not with `tabindex`.

## Focus management

- Opening a dialog moves focus into it and traps focus while open. Closing returns focus to the element that opened it.
- Opening a menu moves focus to the first item; Escape closes it and returns focus to the trigger.
- On client-side route change, move focus to the new page's heading or main region and announce the change. Otherwise the user is stranded on stale focus.

## Forms

- Every input has a programmatic label. Prefer a visible `<label for="id">`. `aria-label` or `aria-labelledby` only when a visible label is genuinely absent.
- Placeholder text is not a label. It disappears on input and fails contrast.
- Associate errors with their field via `aria-describedby`, and mark the field `aria-invalid="true"` while it is in error.
- Group related controls (radio sets, address blocks) in a `fieldset` with a `legend`.
- Do not rely on color alone to show an error. Pair it with text and an icon or marker.

## Color and contrast

- Text meets 4.5:1 against its background; large text (24px, or 18.66px bold) meets 3:1.
- Interactive controls, focus indicators, and meaningful graphics meet 3:1 against adjacent colors.
- Never use color as the only signal. Status, selection, links in body text, and validation all need a second cue: text, underline, icon, shape.

## Images and icons

- Informative images get an `alt` that conveys the meaning, not the filename.
- Decorative images get `alt=""` so screen readers skip them. A missing `alt` is not the same and will be read as the file path.
- An icon-only button needs an accessible name: `aria-label` on the button, or visually hidden text. Do not label the `svg`; label the control.

## Live regions

- Announce async updates the user did not directly trigger: toast, inline save confirmation, background error, search-result count.
- Use `aria-live="polite"` for non-urgent updates and `aria-live="assertive"` sparingly for urgent ones. The container must exist in the DOM before you write into it.
- Do not overuse live regions. Constant chatter is as useless as silence.

## Motion and target size

- Respect `prefers-reduced-motion`. Reduce or remove non-essential animation, parallax, and auto-play when it is set.
- Interactive targets are at least 24x24 CSS pixels, ideally 44x44 for primary touch actions. Small adjacent targets need spacing.

## Checklist before shipping UI

- Every interactive element is a native control or a fully implemented ARIA widget.
- Full keyboard pass: reach everything, operate everything, escape everything, no trap.
- Focus is always visible and its order matches the visual flow.
- Dialogs, menus, and route changes manage focus correctly.
- Inputs have labels; errors are associated and not color-only.
- Text and controls meet contrast; no information is carried by color alone.
- Images have correct `alt`; icon buttons have accessible names.
- Async updates announce through a live region.
- Reduced motion is respected.

## How to test

- Keyboard pass with the mouse untouched.
- Screen reader spot check (VoiceOver, NVDA, or TalkBack) on the changed flow.
- Automated scan with axe (`@axe-core/*` or the browser extension). Automation catches maybe half of the issues, so it supplements the manual passes rather than replacing them.

## Do / Instead of

| Do | Instead of |
|---|---|
| `<button>` / `<a href>` | clickable `<div>` with a click handler |
| native element for its role | `role="button"` on a `<button>` |
| `<label for="id">` | placeholder text as the label |
| `aria-describedby` + `aria-invalid` for errors | color-only error state |
| `:focus-visible` outline | `outline: none` with no replacement |
| `aria-live` region for async updates | silent DOM changes |
| `alt=""` on decorative images | omitting `alt` entirely |
| move focus into an opened dialog | leave focus on the trigger |
| respect `prefers-reduced-motion` | always-on animation |
