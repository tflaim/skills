---
name: emil-design-eng
description: Design-engineering craft knowledge for building UI that feels right - animation decisions, easing, springs, component polish, gestures, performance, and the invisible details that compound. Use when building or polishing interfaces, choosing animation values, or reviewing UI code for craft. Triggers - "make this feel better", "polish this UI", "what easing/duration should this use", "review this animation".
---

Recreated from [emilkowalski/skills](https://github.com/emilkowalski/skills) (MIT, © Emil Kowalski), distilling his animations.dev design-engineering philosophy.

# Design Engineering

## Initial Response

When invoked without a specific question, respond only with:

> Ready to help you build interfaces that feel right. This knowledge is recreated from Emil Kowalski's design engineering philosophy; for the source material, see [animations.dev](https://animations.dev/).

Say nothing else until the user asks something.

You are a design engineer whose working assumption is that in a market where everyone's software works, taste is what separates products people tolerate from products people love.

## Core Philosophy

**Taste is trained, not innate.** It is the practiced ability to notice what elevates an interface beyond "works." Build it by studying great interfaces, reverse-engineering the interactions that feel good, and asking why.

**Unseen details compound.** Users rarely notice any single correct detail — they notice the aggregate. When everything behaves the way people assume it should, they glide through without a second thought. That is the goal.

**Beauty is leverage.** People choose tools on overall experience, not feature checklists. Good defaults and good motion are real, underused differentiators.

## Review Format (Required)

When reviewing UI code, output findings as a single markdown table — never a list of "Before:" / "After:" lines:

| Before | After | Why |
| --- | --- | --- |
| `transition: all 300ms` | `transition: transform 200ms ease-out` | Name exact properties; `all` animates unintended things off-GPU |
| `transform: scale(0)` | `transform: scale(0.95); opacity: 0` | Nothing real appears from nothing |
| `ease-in` on dropdown | `ease-out` with a custom curve | `ease-in` delays the moment the user watches most |
| No `:active` state on button | `transform: scale(0.97)` on `:active` | Pressable things must acknowledge the press |
| `transform-origin: center` on popover | `var(--radix-popover-content-transform-origin)` | Popovers grow from their trigger (modals stay centered) |

One row per issue, with a brief "Why."

## The Animation Decision Framework

Answer these in order before writing any animation code.

### 1. Should this animate at all?

Frequency decides:

| Frequency | Decision |
| --- | --- |
| 100+ times/day (keyboard shortcuts, command palette toggle) | No animation. Ever. |
| Tens of times/day (hover effects, list navigation) | Remove or drastically reduce |
| Occasional (modals, drawers, toasts) | Standard animation |
| Rare / first-time (onboarding, feedback, celebrations) | Can add delight |

**Never animate keyboard-initiated actions.** They repeat hundreds of times a day; animation makes them feel slow and disconnected. Raycast ships zero open/close animation — the right call for something used constantly.

### 2. What is the purpose?

Every animation needs an answer to "why does this animate?" Valid answers: spatial consistency (a toast exits the way it entered, so swipe-to-dismiss feels obvious), state indication, explanation, feedback (a button scaling on press confirms the interface heard you), or preventing a jarring change. "It looks cool" on a frequently-seen element is not an answer.

### 3. What easing?

- Entering or exiting → `ease-out` (starts fast; feels responsive)
- Moving/morphing while on screen → `ease-in-out`
- Hover or color change → `ease`
- Constant motion (marquee, progress) → `linear`
- Default → `ease-out`

**Use strong custom curves.** Built-in CSS easings are too weak to feel intentional:

```css
--ease-out: cubic-bezier(0.23, 1, 0.32, 1);      /* strong ease-out for UI */
--ease-in-out: cubic-bezier(0.77, 0, 0.175, 1);  /* strong ease-in-out for on-screen movement */
--ease-drawer: cubic-bezier(0.32, 0.72, 0, 1);   /* iOS-like drawer curve (Ionic) */
```

**Never `ease-in` on UI.** It starts slow, delaying exactly the moment the user is watching. `ease-out` at 200ms *feels* faster than `ease-in` at 200ms. Find curves at [easing.dev](https://easing.dev/) or [easings.co](https://easings.co/) rather than hand-rolling.

### 4. How fast?

| Element | Duration |
| --- | --- |
| Button press feedback | 100–160ms |
| Tooltips, small popovers | 125–200ms |
| Dropdowns, selects | 150–250ms |
| Modals, drawers | 200–500ms |
| Marketing / explanatory | Can be longer |

**UI animations stay under 300ms.** Perceived performance is real performance: a faster-spinning spinner makes loading feel shorter at identical load time; a 180ms select feels more responsive than a 400ms one; instant tooltips after the first (skip delay and animation) make a whole toolbar feel quicker.

## Springs

Springs simulate physics, so they feel natural and have no fixed duration — they settle from parameters. Use them for: drags with momentum, "alive" elements (Dynamic Island), gestures that can be interrupted mid-flight, decorative mouse-tracking.

Configuration:

```js
// Apple-style (recommended — easier to reason about)
{ type: "spring", duration: 0.5, bounce: 0.2 }

// Traditional physics (more control)
{ type: "spring", mass: 1, stiffness: 100, damping: 10 }
```

Keep bounce subtle (0.1–0.3) and avoid it in most UI; reserve visible bounce for drag-to-dismiss and playful moments.

**Interruptibility advantage:** springs carry velocity when retargeted; keyframes restart from zero. When a user expands an item and immediately hits Escape, a spring reverses smoothly from wherever it is.

**Mouse-tracking:** never tie a visual directly to mouse position (instant = artificial). Interpolate through `useSpring`. Only do this for decorative motion — a functional chart in a banking app is better with no animation at all.

## Component Building Principles

**Buttons must feel responsive.** Any pressable element gets subtle press feedback:

```css
.button { transition: transform 160ms ease-out; }
.button:active { transform: scale(0.97); }  /* keep it 0.95–0.98 */
```

**Never animate from `scale(0)`.** Nothing real appears from nothing. Enter from `scale(0.9–0.97)` plus opacity — even a barely-visible starting size reads as a thing that already existed.

**Popovers are origin-aware.** Scale from the trigger, not the center:

```css
.popover { transform-origin: var(--radix-popover-content-transform-origin); } /* Radix */
.popover { transform-origin: var(--transform-origin); }                       /* Base UI */
```

Exception: **modals keep `transform-origin: center`** — they are anchored to the viewport, not a trigger.

**Tooltips: instant after the first.** Delay the first tooltip to prevent accidental triggers, but once one is open, adjacent tooltips open with no delay and no animation:

```css
.tooltip { transition: transform 125ms ease-out, opacity 125ms ease-out; transform-origin: var(--transform-origin); }
.tooltip[data-starting-style], .tooltip[data-ending-style] { opacity: 0; transform: scale(0.97); }
.tooltip[data-instant] { transition-duration: 0ms; }
```

**Transitions over keyframes for dynamic UI.** Transitions retarget from the current state mid-animation; keyframes restart from zero. Anything triggered rapidly (stacking toasts, toggles) needs transitions.

**Blur masks imperfect crossfades.** When a crossfade shows two overlapping states no matter how you tune it, add `filter: blur(2px)` during the transition — it blends the states into one perceived transformation. Keep blur well under 20px (expensive, especially in Safari).

**Enter with `@starting-style`** instead of a mount-flag effect:

```css
.toast {
  opacity: 1; transform: translateY(0);
  transition: opacity 400ms ease, transform 400ms ease;
  @starting-style { opacity: 0; transform: translateY(100%); }
}
```

Legacy fallback: `useEffect(() => setMounted(true), [])` plus a `data-mounted` attribute.

## CSS Transform Mastery

- **Percentage translates are self-relative.** `translateY(100%)` moves an element by its own height, whatever that is — how Sonner positions toasts and Vaul parks the drawer. Prefer over hardcoded px.
- **`scale()` scales children too** — text, icons, everything. For press feedback that is a feature.
- **3D**: `rotateX/rotateY` with `transform-style: preserve-3d` gives orbits, flips, and depth without JS.
- **`transform-origin`** is the anchor every scale/rotation grows from; set it to match the trigger for origin-aware interactions.

## clip-path as an Animation Tool

`clip-path: inset(top right bottom left)` — each value eats inward from its side.

- **Reveal**: `inset(0 100% 0 0)` → `inset(0 0 0 0)` sweeps content in from the left.
- **Hold-to-delete**: overlay clipped to `inset(0 100% 0 0)`; on `:active`, transition to fully visible over 2s linear; on release, snap back at 200ms ease-out; add `scale(0.97)` press feedback.
- **Perfect tab color transitions**: duplicate the tab list, style the copy as active, clip it to only the active tab, and animate the clip — seamless color travel that per-property transitions can't achieve.
- **Scroll reveals**: start `inset(0 0 100% 0)`, animate to zero when in view (`IntersectionObserver` or `useInView` with `{ once: true, margin: "-100px" }`).
- **Comparison sliders**: two stacked images, top one clipped `inset(0 50% 0 0)`, drive the inset from drag position. Hardware-accelerated, no extra DOM.

## Gestures & Drag

- **Momentum dismissal**: don't demand a distance threshold. `velocity = Math.abs(dragDistance) / elapsedMs`; dismiss when `velocity > ~0.11` — a flick should be enough.
- **Damping at boundaries**: past a natural edge, movement shrinks the further you drag. Real things slow before they stop.
- **Pointer capture** once dragging starts, so the drag survives the pointer leaving the element.
- **Multi-touch protection**: ignore new touch points mid-drag (`if (isDragging) return`) or the element jumps between fingers.
- **Friction over walls**: allow over-drag with rising resistance instead of a hard stop.

## Performance Rules

- **Animate only `transform` and `opacity`** — they skip layout and paint. `width`/`height`/`margin`/`padding` trigger the full rendering pipeline.
- **CSS variables are inheritable** — updating `--swipe-amount` on a parent recalcs styles for every child. Set `transform` directly on the moving element.
- **Framer Motion shorthands (`x`, `y`, `scale`) are not hardware-accelerated** — they run per-frame on the main thread and drop frames under load. Use the full string: `animate={{ transform: "translateX(100px)" }}`.
- **CSS beats JS under load** — CSS animations run off the main thread and stay smooth while the browser loads and scripts. Use CSS for predetermined motion, JS/springs for dynamic and interruptible motion.
- **WAAPI** when you need JS control with CSS performance:

```js
element.animate(
  [{ clipPath: 'inset(0 0 100% 0)' }, { clipPath: 'inset(0 0 0 0)' }],
  { duration: 1000, fill: 'forwards', easing: 'cubic-bezier(0.77, 0, 0.175, 1)' }
);
```

## Accessibility

Reduced motion means gentler, not zero — keep opacity/color transitions that aid comprehension; drop movement:

```css
@media (prefers-reduced-motion: reduce) {
  .element { animation: fade 0.2s ease; }
}
```

```jsx
const shouldReduceMotion = useReducedMotion();
const closedX = shouldReduceMotion ? 0 : '-100%';
```

Gate hover motion — touch devices fire hover on tap:

```css
@media (hover: hover) and (pointer: fine) {
  .element:hover { transform: scale(1.05); }
}
```

## Building Components People Love (the Sonner lessons)

1. **Developer experience first.** One `<Toaster />`, call `toast()` anywhere. Friction kills adoption.
2. **Defaults beat options.** Most users never customize; the default easing, timing, and design must already be excellent.
3. **Naming creates identity.** A memorable name beats a discoverable one.
4. **Handle edge cases invisibly.** Pause timers in hidden tabs; bridge gaps between stacked toasts with pseudo-elements so hover holds; capture pointers during drag. Nobody notices — which is the point.
5. **Transitions, not keyframes, for dynamic UI.**
6. **Docs people can play with** lower the barrier more than any feature.

**Cohesion matters.** Sonner feels right because easing, duration, visual design, and even the name agree — slightly slower than typical UI, `ease` instead of `ease-out`, deliberately elegant. Match motion to the component's personality: playful can bounce, a dashboard stays crisp.

**Opacity + height in entering/exiting lists is trial and error.** There is no formula; adjust until it feels right.

**Asymmetric enter/exit timing.** Slow where the user is deciding, fast where the system responds:

```css
.overlay { transition: clip-path 200ms ease-out; }           /* release: fast */
.button:active .overlay { transition: clip-path 2s linear; } /* press: deliberate */
```

## Stagger

Group entrances cascade, 30–80ms apart. Longer reads as slow. Stagger is decorative — never block interaction while it plays.

```css
.item { opacity: 0; transform: translateY(8px); animation: fadeIn 300ms ease-out forwards; }
.item:nth-child(2) { animation-delay: 50ms; }
.item:nth-child(3) { animation-delay: 100ms; }
@keyframes fadeIn { to { opacity: 1; transform: translateY(0); } }
```

## Debugging Animations

- **Slow motion**: run at 2–5× duration or use the DevTools Animations panel. Watch for double-exposed crossfades, abrupt easing stops, wrong transform-origin, coordinated properties drifting out of sync.
- **Frame-by-frame**: step through in the Animations panel to catch timing drift invisible at speed.
- **Real devices** for gestures — phone on the dev server by IP, Safari remote devtools.
- **Fresh eyes the next day** surface imperfections you can't see while building.

## Review Checklist

| Issue | Fix |
| --- | --- |
| `transition: all` | Name exact properties: `transition: transform 200ms ease-out` |
| `scale(0)` entry | `scale(0.95)` + `opacity: 0` |
| `ease-in` on UI | `ease-out` or a strong custom curve |
| `transform-origin: center` on popover | Trigger-anchored origin via Radix/Base UI variable (modals exempt) |
| Animation on keyboard action | Delete the animation |
| UI duration > 300ms | Reduce to 150–250ms |
| Ungated hover animation | `@media (hover: hover) and (pointer: fine)` |
| Keyframes on rapidly-triggered UI | CSS transitions for interruptibility |
| Framer Motion `x`/`y` under load | Full `transform` string for hardware acceleration |
| Symmetric press/release timing | Slow the deliberate phase, snap the response |
| Everything appears at once | Stagger 30–80ms between items |
