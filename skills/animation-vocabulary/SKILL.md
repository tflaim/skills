---
name: animation-vocabulary
description: Reverse-lookup glossary that turns a vague description of a web animation or motion effect into its exact term ("the bouncy thing when a popover opens" → Pop in; "the iOS rubber-band scroll" → Rubber-banding). Use when the user asks "what's it called when...", or describes a motion effect without knowing its name and wants the right word to prompt an AI or designer with. For naming an effect, not designing or building one.
---

Recreated from [emilkowalski/skills](https://github.com/emilkowalski/skills) (MIT, © Emil Kowalski).

# Animation Vocabulary

Turn a vague description of a motion or effect into the precise term, so the user knows what to ask for.

## Quick Start

The user describes an effect loosely. You return the matching term(s) in this format:

```
**Stagger** — Several items animate one after another with a small delay between each, forming a cascade.
```

If several terms could fit, list the best match first, then 1–2 alternates with a one-line note on how they differ.

## Instructions

1. **Read for intent, not keywords.** Users describe what they *see* or *feel* ("springy", "slides off", "draws itself in"), not the technical name. Map the sensation to the glossary below.
2. **Quote the glossary verbatim.** Its descriptions are authoritative — use them as-is, don't paraphrase.
3. **Disambiguate close terms.** When two compete (*Clip-path* vs *Mask*, *Pop in* vs *Bounce*, *Shared element transition* vs *Layout animation*), contrast them so the user can pick.
4. **When nothing matches exactly,** name the closest term and say plainly it's an approximation, or describe the effect in the glossary's vocabulary (e.g. "that's a *stagger* of *scale-in* entrances").
5. **Stay within this glossary.** If a term genuinely isn't here, say so rather than inventing one — though you may explain the concept using these words.
6. **Keep it tight.** A naming question wants a name, not an essay. Lead with the term; expand only if asked.

## Examples

**Example 1 — feel-based**
User: "What's it called when a popover seems to grow out of the button you clicked instead of from its middle?"
Output:
```
**Origin-aware animation** — An element animates out of its trigger, like a popover growing from the button that opened it rather than from its own center (the CSS default).
```

**Example 2 — disambiguation**
User: "The thing where one image turns into another image."
Output:
```
**Morph** — One shape smoothly becomes another shape, e.g. Dynamic Island.

Close alternates:
- **Crossfade** — if they simply fade over each other in place.
- **Shared element transition** — if an element travels and transforms from one position into another.
```

**Example 3 — physics feel**
User: "That iOS scroll where it resists and snaps back when you pull too far."
Output:
```
**Rubber-banding** — Resistance and snap-back when you drag past a boundary (the iOS overscroll feel).
```

## Glossary

### Entrances & Exits — how elements appear and disappear
- **Fade in / Fade out** — Element appears or disappears through an opacity change.
- **Slide in** — Element enters by sliding in from off-screen (any edge).
- **Scale in** — Element grows from smaller to full size as it appears, usually paired with a fade.
- **Pop in** — Element appears with a slight overshoot, as if bouncing into place.
- **Reveal** — Content is uncovered gradually, typically by animating a clip-path or mask.
- **Enter / Exit** — The animation an element plays when added to or removed from the screen.

### Sequencing & Timing — coordinating multiple elements or moments
- **Keyframes** — Defined points in an animation (0%, 50%, 100%) the browser interpolates between.
- **Interpolation / Tween** — Generating the in-between frames from a start value to an end value so motion is continuous.
- **Stagger** — Several items animate one after another with a small delay between each, forming a cascade.
- **Orchestration** — Deliberately timing multiple animations so they read as one coordinated motion.
- **Delay** — Time before an animation starts.
- **Duration** — How long an animation takes.
- **Fill mode** — Whether an element keeps its first or last frame's styles outside the animation (e.g. `forwards`).
- **Stepped animation** — An animation divided into discrete steps, like a countdown timer.

### Movement & Transforms — changing an element's position, size, or angle
- **Translate** — Move an element along the X or Y axis.
- **Scale** — Make an element larger or smaller.
- **Rotate** — Spin an element around a point.
- **Skew** — Slant an element along an axis, shearing it out of its rectangle.
- **3D tilt / Flip** — Rotate in 3D space (rotateX / rotateY) for depth.
- **Perspective** — The strength of the 3D effect — lower values exaggerate depth, as if the viewer were closer.
- **Transform origin** — The anchor point a scale or rotation grows or spins from.
- **Origin-aware animation** — An element animates out of its trigger, like a popover growing from the button that opened it rather than from its own center (the CSS default).

### Transitions Between States — connecting one state, view, or element to another
- **Crossfade** — One element fades out while another fades in, in the same spot.
- **Continuity transition** — A change that keeps the user oriented by visually connecting before and after, e.g. the same rectangle growing and shrinking.
- **Morph** — One shape smoothly becomes another shape, e.g. Dynamic Island.
- **Shared element transition** — An element travels and transforms from one position into another, like a thumbnail expanding into a card.
- **Layout animation** — When an element's size or position changes, it animates to the new spot instead of snapping.
- **Accordion / Collapse** — A section smoothly expands and collapses its height to show or hide content.
- **Direction-aware transition** — Content slides one way going forward and the opposite way going back, giving navigation a sense of direction.

### Scroll — motion tied to scrolling or navigating between views
- **Scroll reveal** — Elements fade or slide into place as they enter the viewport.
- **Scroll-driven animation** — An animation whose progress is tied directly to scroll position.
- **Parallax** — Background and foreground move at different speeds while scrolling, creating depth.
- **Page transition** — An animation played when navigating from one page or route to another.
- **View transition** — The browser morphs between two states or pages, connecting shared elements.

### Feedback & Interaction — responding to the user's actions
- **Hover effect** — Visual change when the cursor moves over an element.
- **Press / Tap feedback** — A subtle scale-down on click so the element feels physical.
- **Hold to confirm** — A progress effect that fills while the user holds a button.
- **Drag** — Moving an element by grabbing it, often with momentum on release.
- **Drag to reorder** — Dragging list items to rearrange them while the others shift to make room.
- **Swipe to dismiss** — Dragging an element off-screen to close it, like a drawer or toast.
- **Rubber-banding** — Resistance and snap-back when you drag past a boundary (the iOS overscroll feel).
- **Shake / Wiggle** — A quick side-to-side jitter signaling an error or rejected input.
- **Ripple** — A circle expanding from the tap point, confirming the press.

### Easing — how speed changes over an animation
- **Easing** — The rate at which an animation accelerates or decelerates.
- **Ease-out** — Starts fast, ends slow. The default for most UI and anything responding to the user.
- **Ease-in** — Starts slow, ends fast. Usually avoided; reads as sluggish.
- **Ease-in-out** — Slow, fast, slow. Good for elements already on screen moving from A to B.
- **Linear** — Constant speed. Avoid for UI; reserve for spinners and marquees.
- **Cubic-bezier** — A custom easing curve defined for precise control.
- **Asymmetric easing** — A curve that accelerates and decelerates at different rates; feels more alive than a symmetric one.

### Spring Animations — physics-based motion as an alternative to fixed-duration easing
- **Spring** — Motion driven by physics (tension, mass, damping) rather than a set duration.
- **Stiffness / Tension** — How strongly the spring pulls toward its target; higher feels snappier.
- **Damping** — How quickly a spring settles; lower damping means more bounce and oscillation.
- **Mass** — How heavy the animated element feels; more mass is slower and more sluggish.
- **Bounce** — A spring that overshoots and settles, adding playfulness.
- **Perceptual duration** — How long a spring *feels* finished, even as it keeps micro-settling underneath.
- **Momentum** — Motion that carries velocity, especially after a drag or interruption.
- **Velocity** — How fast and in which direction an element is moving; a spring carries it into the next animation when interrupted, so a flicked element keeps its speed.
- **Interruptible animation** — An animation that can be smoothly redirected mid-flight instead of finishing first.

### Looping & Ambient Motion — animations that run on their own
- **Marquee** — Text or content scrolling continuously in a loop.
- **Loop** — An animation that repeats, a set number of times or infinitely.
- **Alternate (yoyo)** — A loop that plays forward then reverses each iteration instead of jumping back to the start.
- **Orbit** — An element circling another in a continuous path.
- **Pulse** — A gentle repeating scale or opacity change to draw attention.
- **Float** — A gentle continuous up-and-down drift that makes a static element feel alive and weightless.
- **Idle animation** — Subtle motion that plays while an element sits waiting to be interacted with.

### Polish & Effects — the small touches that separate good from great
- **Blur** — A blur filter used to soften an element or mask tiny imperfections.
- **Clip-path** — Clipping an element to a shape; used for reveals, masks, and before/after sliders.
- **Mask** — Hiding or revealing parts of an element with a shape or gradient — like clip-path, but with soft, fadeable edges.
- **Before / after slider** — A draggable divider that wipes between two overlaid images to compare them.
- **Line drawing** — An SVG path that draws itself in, like an invisible pen tracing it.
- **Text morph** — Text animating character by character when it changes, drawing attention to the new value.
- **Skeleton / Shimmer** — A placeholder with a moving sheen shown while content loads.
- **Number ticker** — Digits rolling or counting up to a value.
- **Tabular numbers** — Fixed-width digits so numbers don't shift as they change; essential for tickers, timers, counters.
- **Typewriter** — Text appearing one character at a time, as if typed.

### Performance — what keeps motion smooth instead of stuttering
- **Frame rate (FPS)** — Frames drawn per second; 60fps is the smoothness baseline, 120fps on newer displays.
- **Jank** — Visible stutter when the browser drops frames because it can't keep up.
- **Dropped frame** — A frame the browser missed its deadline to draw, causing a tiny hitch.
- **Compositing** — Letting the GPU move or fade an element on its own layer without redoing layout or paint.
- **will-change** — A CSS hint that an element is about to animate, so the browser can promote it to its own layer in advance.
- **Layout thrashing** — Animating properties like width, height, top, or left that force layout recalculation every frame, causing jank.

### Principles to Know — concepts that guide when and how to animate
- **Purposeful animation** — Motion serves a function — orient, give feedback, show relationships — not just decorate.
- **Anticipation** — A small wind-up in the opposite direction before a move, hinting at what's coming.
- **Follow-through** — Parts of an element keep moving and settle slightly after the main motion stops, adding weight.
- **Squash & stretch** — Deforming an element as it moves to convey weight, speed, and flexibility.
- **Perceived performance** — The right animation makes an interface feel faster, even when it isn't.
- **Frequency of use** — The more often a user sees an animation, the shorter and subtler it should be.
- **Spatial consistency** — Animating so an element keeps its identity and position across states, so users never lose track of where things went.
- **Hardware acceleration** — Animating transform and opacity lets the GPU keep motion smooth.
- **Reduced motion** — Respecting the user's prefers-reduced-motion setting by toning down or removing motion.
