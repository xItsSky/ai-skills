# Client Performance

Measure first, optimize second. Most performance work fails because it targets a bottleneck that was never there. Profile the real thing, find where the time actually goes, then change one thing and measure again. Guessing wastes effort and often makes code worse.

## Profile before you touch anything

- Reproduce the slow path and record it: browser Performance panel, the framework's own profiler (React DevTools Profiler, Angular DevTools), and Lighthouse for load-time.
- Test on conditions your users actually have: mid-tier CPU throttling and a throttled network, not your dev machine on localhost.
- Find the dominant cost before writing any fix. Optimizing a 5ms function while a 300ms one sits next to it is wasted work.
- After each change, measure again. If the number did not move, revert it. Speculative optimization is not free; it costs readability.

## Priority order

Work top to bottom. The cheapest win is work you never do.

1. Avoid unnecessary work: dead effects, redundant fetches, recomputation, work done on every render that could be done once.
2. Get the architecture right: where state lives, how far updates propagate, what re-renders when data changes.
3. Ship less JavaScript: code splitting, dynamic import, tree-shaking, dropping heavy dependencies.
4. Load less up front: lazy-load routes and heavy components, defer below-the-fold work.
5. Optimize assets: images and fonts.
6. Reduce render cost: keys, stable references, targeted memoization, virtualization.

## Ship less JavaScript

- Split by route so a page pays only for its own code.
- Dynamically import heavy, rarely-used components (rich editors, charts, maps, date pickers) at the point of use.
- Keep imports tree-shakeable: import named members, not whole namespaces. Watch for barrel files that drag in everything.
- Audit the bundle. A single oversized dependency often outweighs every micro-optimization combined.

## Lazy-load routes and heavy components

- Every route is a split point. Load the route's code when the user navigates to it.
- Defer components that are off-screen or behind interaction (modals, tabs, drawers) until they are needed.
- Pair lazy loading with a real loading state so deferral does not read as a broken page.

## Images and fonts

- Serve responsive images (`srcset`/`sizes`) and modern formats (AVIF, WebP) with fallbacks.
- Always set width and height (or an aspect ratio) so images reserve their space and do not shift layout as they load.
- Lazy-load below-the-fold images; do not lazy-load the LCP image, and consider preloading it.
- Subset fonts, self-host or preconnect, and set `font-display: swap` to avoid invisible text. Preload the critical font.

## Reduce render cost

- Give lists stable, identity-based keys. Index keys cause needless re-renders and state bugs on reorder.
- Keep object, array, and function references stable across renders when they feed memoized children or dependency arrays.
- Memoize only after profiling proves a component is a hot path. Blanket memoization adds cost and hides the real problem.
- Modern framework reactivity (React Compiler, Angular signals, Solid, Svelte runes) handles much of this. Do not hand-memoize what the compiler already covers; measure to confirm. Vue's Vapor mode is newer, so verify it applies to your version before relying on it.

## Virtualize long lists

- Render only the visible rows for long or unbounded lists. Rendering thousands of DOM nodes stalls the main thread regardless of how fast each row is.

## Defer and offload expensive work

- Break long tasks so the main thread can respond to input; yield between chunks.
- Move heavy computation (parsing, image processing, crypto) to a Web Worker so the UI stays responsive.
- Debounce or throttle high-frequency handlers (scroll, resize, input) that trigger real work.

## Budget with Core Web Vitals

- LCP (Largest Contentful Paint): the main content is visible fast. Driven by server response, render-blocking resources, and the hero image.
- INP (Interaction to Next Paint): interactions feel responsive. Driven by long tasks and heavy event handlers. INP replaced FID as a Core Web Vital in 2024; measure INP, not FID.
- CLS (Cumulative Layout Shift): nothing jumps. Driven by unsized media, injected content, and late-loading fonts.
- Set targets, watch them in the field, and treat a regression as a defect.

## Do / Instead of

| Do | Instead of |
|---|---|
| profile, then fix the dominant cost | optimize on a hunch |
| measure after every change | assume the change helped |
| route-level and on-demand code splitting | one bundle for the whole app |
| import named members | `import * as` from large packages |
| width/height or aspect-ratio on images | unsized images that shift layout |
| stable identity-based list keys | array index as key |
| memoize proven hot paths | memoize everything preemptively |
| virtualize long lists | render thousands of DOM nodes |
| offload heavy work to a Web Worker | block the main thread |
| track LCP/INP/CLS in the field | ship and hope |
