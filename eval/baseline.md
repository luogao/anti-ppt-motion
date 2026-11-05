# Shared technical baseline

This file is identical in both arms. It paraphrases technical guidance from:
- https://www.remotion.dev/docs/animating-properties
- https://www.remotion.dev/docs/interpolate
- https://www.remotion.dev/docs/cli/render

Use the provided React / Remotion starter. Export `Scene` from `src/Scene.tsx`.
The common Root owns dimensions, duration and the shared narration; do not modify it.
Do not add or alter audio in Scene; the only audio is the common narration.
Drive animation using useCurrentFrame() and useVideoConfig(). Clamp interpolation.
No wall-clock state, unseeded randomness, CSS animation or transitions.
Use installed dependencies, inline CSS, SVG and public assets. Do not fetch remote assets.
Keep relevant information legible on a phone; preserve the brief's facts and units.
The renderer runs after generation. Do not start a browser, install packages or render yourself.
Only edit src/Scene.tsx and plan.md. Do not inspect other projects, other runs or global skills.

The same baseline is supplied to both arms. It is a technical summary, not a copy
of the full official Remotion Skill package and not an anti-PPT design treatment.
