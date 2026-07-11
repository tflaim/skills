---
name: apple-design
description: Apple's approach to interface design and fluid, physical motion, translated for the web. Use when building or reviewing gesture-driven UI, spring animations, drag/swipe/sheet interactions, momentum and interruptible transitions, translucent materials and depth, typography (optical sizing, tracking, leading), reduced-motion, or the design foundations (feedback, spatial consistency, restraint) behind Apple-style interfaces.
---

Recreated from [emilkowalski/skills](https://github.com/emilkowalski/skills) (MIT, © Emil Kowalski).

# Apple Design

How Apple builds interfaces that stop feeling like a computer and start feeling like an extension of you. Distilled from Apple's WWDC design talks — chiefly *Designing Fluid Interfaces* (WWDC 2018) — and translated to the web platform (CSS, Pointer Events, `requestAnimationFrame`, spring libraries like Motion/Framer Motion).

The through-line: **an interface feels alive when motion starts from the current on-screen value, inherits the user's velocity, projects momentum forward, and can be grabbed and reversed at any instant.** Springs make all of this natural because they are inherently interruptible and velocity-aware.

## The Core Idea

> "When we align the interface to the way we think and move, something magical happens — it stops feeling like a computer and starts feeling like a seamless extension of us."

An interface is fluid when it behaves like the physical world: responds instantly, moves continuously, carries momentum, resists at boundaries, and can be redirected mid-motion. Apple frames design as serving four human needs — **safety/predictability, understanding, achievement, and joy** — and every rule below serves one of them.

## 1. Response — kill latency

The moment lag appears, directness "falls off a cliff." Response is the foundation.

- **Respond on pointer-down, not release.** Highlight the instant the press lands; waiting for `click`/touch-up feels dead.
- **Audit every latency** — debounces, artificial timers, transition waits, the ~300ms tap delay. Anything nonessential on the input path is a regression.
- **Feedback is continuous during the interaction**, not just at the end. Drags, sliders, and drawers track the pointer 1:1 the whole way.

```css
.button:active { transform: scale(0.97); transition: transform 100ms ease-out; }
```

## 2. Direct manipulation — 1:1 tracking

> "Touch and content should move together."

A dragged element stays glued to the finger — and respects the offset from *where it was grabbed*. Snapping to center on grab breaks the illusion instantly.

- Pointer Events with `setPointerCapture` so tracking survives the pointer leaving the element.
- Keep a short **position/velocity history** (last few `pointermove` events) — you need release velocity later.

```js
el.addEventListener('pointerdown', (e) => {
  el.setPointerCapture(e.pointerId);
  const grabOffset = e.clientY - el.getBoundingClientRect().top; // respect the grab point
  // ...track position + timestamp history for velocity
});
```

## 3. Interruptibility — the single most important principle

> "The thought and the gesture happen in parallel."

Every animation must be grabbable and redirectable at any moment. A closing modal the user grabs again follows the finger — it does not finish closing first.

- **Never lock out input during a transition.**
- **Animate from the *presentation* (current on-screen) value, never the logical target.** On interrupt, read the live transform and start there, or the element visibly jumps.
- **Avoid CSS transitions and keyframes for gesture-driven motion** — they can't be grabbed mid-flight. Springs start from the current value by default.
- **Blend velocity on reversal — never hard-cut it.** Swapping animations at a reversal creates a velocity "brick wall." Use a spring library that re-targets carrying current velocity (the web analog of iOS additive animations).
- **Decompose 2D motion into independent X and Y springs** — one spring on the 2D distance desyncs when the axes carry different velocities.

## 4. Behavior over animation — use springs

> "Think of animation as a conversation between you and the object, not something prescribed by the interface."

A fixed-duration script can't respond to new input; a spring just gets a new target and stays continuous. Reach for springs on anything a user can touch.

Apple replaced the physics triplet with two designer-friendly parameters — think in these:

- **Damping ratio** — overshoot control. `1.0` = critically damped, no bounce. Below `1.0` = oscillates; lower = bouncier.
- **Response** — how quickly the value approaches the target, in seconds. Lower = snappier. **Not a duration** — settle time emerges from the parameters.

**Defaults:** start most UI at **damping `1.0`** (graceful, non-distracting). Add bounce (**damping ~`0.8`**) **only when the gesture carried momentum** — overshoot on a flicked card feels right; overshoot on a menu that faded in feels wrong.

**Values Apple ships:**

| Interaction | Damping | Response |
| --- | --- | --- |
| Move / reposition (e.g. PiP) | `1.0` | `0.4` |
| Rotation | `0.8` | `0.4` |
| Drawer / sheet | `0.8` | `0.3` |

**Web mapping (Motion / Framer Motion):** the `bounce` + `duration` spring API maps closely to damping + response. House style: `damping 1.0` springs by default; bounce reserved for momentum-driven physical interactions.

```js
import { animate } from 'motion';

// Critically damped default (no overshoot)
animate(el, { y: 0 }, { type: 'spring', bounce: 0, duration: 0.4 });

// Momentum interaction — slight bounce, only because a flick preceded it
animate(el, { y: target }, { type: 'spring', bounce: 0.2, duration: 0.4 });
```

## 5. Velocity handoff — the seam between drag and animation

When a gesture ends, the animation continues at the finger's exact velocity — no visible seam between dragging and animating. This is the detail that most separates "fluid" from "fine."

Pass release velocity as the spring's initial velocity. APIs that want **relative** velocity normalize by remaining distance:

```
relativeVelocity = gestureVelocity / (targetValue − currentValue)
```

Element at `y=50`, target `y=150` (100px to go), finger at 50px/s → initial spring velocity `0.5`. Motion / Framer Motion take absolute px/s directly (the `velocity` option).

## 6. Momentum projection — animate to where the gesture is *going*

> "Take a small input and make a big output."

Don't snap to the nearest boundary from the *release point*. Project the resting position from velocity — like scroll deceleration — then snap to the target nearest the projection. This is what makes a flick feel like a throw.

Apple's exact projection function (from the *Designing Fluid Interfaces* sample code):

```js
// decelerationRate ≈ 0.998 for normal scroll feel; 0.99 for snappier
function project(initialVelocity /* px/s */, decelerationRate = 0.998) {
  return (initialVelocity / 1000) * decelerationRate / (1 - decelerationRate);
}

const projectedEndpoint = currentPosition + project(releaseVelocity);
const target = nearestSnapPoint(projectedEndpoint);    // choose target from the projection
animateSpringTo(target, { velocity: releaseVelocity }); // then hand off velocity (§5)
```

Note: the physics-textbook `v²/(2·decel)` is *not* what Apple ships — use the exponential-decay form above. This is the standard behavior in good bottom-sheets and carousels (Vaul, Embla).

## 7. Spatial consistency — symmetric paths, anchored origins

> "If something disappears one way, we expect it to emerge from where it came."

- **Enter and exit along the same path.** In-from-right / out-the-bottom feels disconnected.
- **Anchor to the source.** Menus, popovers, sheets originate from their trigger — set `transform-origin` there so the spatial relationship is obvious.
- **Mirror the easing on reversible transitions** (inverse cubic-bezier control points for the two directions).

## 8. Hint in the direction of the gesture

Humans predict the final state from a trajectory. Intermediate motion should telegraph the outcome — Control Center modules "grow up and out toward your finger." Make the in-between frames point at the destination, not just interpolate blindly.

## 9. Rubber-banding — soft boundaries

At an edge, resist progressively instead of stopping hard. A hard stop reads as "frozen"; continuous resistance reads as "responsive, but there's nothing more here."

```js
// The further past the bound, the less the element follows
function rubberband(overshoot, dimension, constant = 0.55) {
  return (overshoot * dimension * constant) / (dimension + constant * Math.abs(overshoot));
}
```

## 10. Gesture design details (the "feel" checklist)

- **Tap:** highlight on touch-*down*, commit on touch-*up*. ~10px hysteresis/hit padding; allow cancel by dragging away (and back).
- **Drag/swipe:** small movement threshold (~10px) before committing to a direction, then 1:1 tracking.
- **Detect all plausible gestures in parallel from the first move**, then cancel the losers once intent is clear. Avoid recognizers that only report a final state (`swipeleft`-style events) — they discard the continuous tracking feedback needs.
- **Minimize disambiguation delays.** Double-tap detection inherently delays single taps; pay that cost only where double-tap truly exists.

## 11. Frame-level smoothness

Smoothness is about *what's in the frames*, not just frame rate.

- Keep per-frame positional change below the perception threshold to avoid strobing.
- For very fast motion, subtle **motion blur / stretch** encodes speed better than a hard streak.
- `requestAnimationFrame` is the web's display-synced clock (Apple's is `CADisplayLink`). Animate compositor-friendly properties only — `transform`, `opacity` — and hint with `will-change` where motion is imminent.

## 12. Materials & depth — translucency conveys hierarchy

Apple uses translucent materials as a floating functional layer. Approximate with `backdrop-filter`.

- **Nav/toolbars/sheets are translucent layers** (`backdrop-filter: blur()` + semi-transparent background) with content scrolling underneath — not opaque strips.
- **Material weight encodes hierarchy:** heavier/darker separates structure (sidebars); lighter draws attention to interactive elements. **Never stack a light translucent surface on another** — legibility collapses.
- **Bigger surfaces read thicker:** stronger blur, deeper shadow than small chips. Consider context-aware shadows — heavier over busy content, lighter over plain backgrounds.
- **Dim to focus, separate to keep flow.** Modal tasks pair the surface with a scrim and push the background back; parallel non-blocking panels use translucency and offset without a scrim. Stacked sheets progressively dim and push back each parent.
- **Vibrancy keeps text legible** over changing backgrounds: higher contrast, slightly heavier weight, a small letter-spacing bump. Put color on a solid layer, not the translucent foreground.
- **Scroll edge effects, not hard dividers:** fade a small blur/gradient mask where content meets floating chrome, only where they actually overlap.
- **Materialize, don't just fade:** animate blur radius and scale together on glass surfaces entering/exiting, so the material reads as arriving, not fading.

```css
.toolbar {
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(20px) saturate(180%);
  border-top: 1px solid rgba(255, 255, 255, 0.4); /* bright top edge = light catching the material */
}
```

## 13. Multimodal feedback — motion + sound + haptics

From *Designing Audio-Haptic Experiences*:

1. **Causality** — it must be obvious what caused the feedback; trigger on the causal event and match its physical character.
2. **Harmony** — visual, sound, and haptic fire on the **same frame**; latency between them destroys the illusion.
3. **Utility** — feedback only where it earns its place (success, error, commit, snap). Over-feedback trains people to ignore all of it.

## 14. Reduced motion & accessibility

Reduced motion means a gentler, non-vestibular equivalent — not silence. Respond to three independent signals:

- **`prefers-reduced-motion: reduce`** — replace slides/springs/parallax with short opacity **cross-fades**; drop elastic/overshoot; keep comprehension-aiding opacity/color changes.
- **`prefers-reduced-transparency: reduce`** — frostier/solid surfaces: raise background opacity, drop blur.
- **`prefers-contrast: more`** — near-solid backgrounds with a defined, contrasting border.

Also: no full-viewport moving backgrounds; avoid slow loops near 0.2 Hz (one cycle per ~5s); ease dark↔light theme changes; make large moving objects semi-transparent while traveling; fade big surfaces out during a large reposition, back in once settled.

```css
@media (prefers-reduced-motion: reduce) {
  .sheet { transition: opacity 200ms ease; transform: none !important; }
}
@media (prefers-reduced-transparency: reduce) {
  .toolbar { background: white; backdrop-filter: none; }
}
```

## 15. Typography — optical sizing, tracking, leading

From *The Details of UI Typography* (WWDC 2020). Type changes shape with size; apply the same discipline on the web.

- **Tracking is size-specific — never one value for all sizes.** Large display text wants *negative* tracking; small text wants slightly *positive*. A fixed `letter-spacing` is wrong somewhere. Tighten headings; body near `0`.
- **Leading tracks size inversely.** Tight on large headings, looser on body. Increase for scripts with tall ascenders/descenders; tighten for dense UI.
- **Hierarchy = weight + size + leading as a set.** Emphasize with weight — presence without extra space.
- **Respect the user's text-size setting** (Dynamic Type). Spacing in `rem`/`em`, not fixed px, so larger fonts don't break layout.
- **Default to the platform's system font** — it ships optical sizing, tracking tables, and legibility tuning. Override only with a reason.

```css
:root { font: 100%/1.5 system-ui, sans-serif; } /* body: system font, comfortable leading */

.display {
  font-size: clamp(2rem, 5vw, 4rem);
  line-height: 1.05;        /* tight leading for large text */
  letter-spacing: -0.02em;  /* negative tracking as it grows */
  font-optical-sizing: auto;
}
```

## 16. Design foundations — the eight principles

From *Principles of Great Design* (WWDC 2026). Use these as the names you reason with:

1. **Purpose.** Make with intention; decide what *not* to build. Every feature spends the user's time, attention, and trust.
2. **Agency.** Keep people in control: choices over forced paths; easy undo for slips; confirmation dialogs only for genuinely destructive, irreversible actions (overuse trains click-through).
3. **Responsibility.** Act in the user's interest. Privacy asked at the right moment, only what's needed. Anticipate misuse and harm — especially with AI. Cut features whose risk outweighs their value.
4. **Familiarity.** Build on what people know. Metaphors neither too literal nor too abstract; honor their physics. Consistency: same look = same behavior = same place. Break a familiar pattern only when you can prove better — then test it.
5. **Flexibility.** Design for contexts, devices, and the full range of abilities. Adapt to the platform and situation; design inclusively; when no one layout fits everyone, let people personalize.
6. **Simplicity — not minimalism.** Strip the unnecessary so the core purpose shines; burying everything in one place looks minimal but isn't simple. Concise and clear, hierarchy doing the work; sometimes *adding* context simplifies. Common path first, advanced options one level deeper.
7. **Craft.** Uncompromising detail builds trust. Nothing random — every spacing, timing, and alignment value is a defensible choice. Jittery scroll and misaligned icons read as carelessness. Craft needs iteration and longevity.
8. **Delight.** The result of getting the other seven right, not confetti on top. Decide the emotion (calm, confident, excited) and reinforce it everywhere.

Tactical rules that serve these:

- **Feedback comes in four kinds:** status, completion, warning, error. Confirm meaningful actions, expose ongoing status, warn before problems, validate inline.
- **Wayfinding.** Every screen answers: Where am I? Where can I go? What's there? How do I get out? Never trap the user.
- **Grouping & mapping.** Proximity implies relationship; put controls near what they affect, arranged to mirror what they change. If a control needs a label to explain it, the mapping is weak.
- **Direct, specific labels beat safe generic ones.** "Progress", "Library" — not "Home". Specificity creates predictability.

## 17. Process

- **Prototype interactively** — a working demo is worth "a million static designs," and it sets a bar that prevents a mediocre final implementation.
- **Design interaction and visuals together.** "You shouldn't be able to tell where one ends and the other begins." Motion is not a layer applied after the pixels.
- **Test with real people in real context**; review motion with fresh eyes and in slow motion / frame-by-frame.

## Quick Reference

| Need | Technique | Concrete value |
| --- | --- | --- |
| Default UI spring | Critically damped, no overshoot | `damping 1.0`, `response 0.3–0.4` |
| Momentum / flick spring | Under-damped, slight bounce | `damping ~0.8`, `response 0.3–0.4` |
| Gesture → spring velocity | Hand off release velocity | `gestureVelocity / (target − current)` if normalized |
| Flick landing point | Project momentum | `current + (v/1000)·d/(1−d)`, `d ≈ 0.998` |
| Interrupt cleanly | Start from presentation (live) value | read the on-screen transform |
| Avoid reversal "brick wall" | Carry velocity through re-target | spring that blends velocity |
| Reversible transition | Mirror the easing curve | inverse cubic-bezier |
| Decide reverse vs. commit | Use velocity **sign**, not position | at release |
| 1:1 drag | Pointer Events + capture | respect the grab offset |
| Feedback | On pointer-down, continuous | never only at the end |
| Boundary | Rubber-band, don't hard-stop | progressive resistance |
| Translucent chrome | `backdrop-filter` layer | content scrolls under |
| Type tracking | Size-specific, never fixed | tighten large text (`-0.02em`), body near `0` |
| Reduced motion | Cross-fade, not slide/spring | `@media (prefers-reduced-motion)` |
