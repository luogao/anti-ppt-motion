# Protocol v0.1 — freeze before formal runs

## Question

Does adding this Skill change the output of the same coding model on three
narrated motion tasks? This is a small exploratory comparison, not a statistical
claim of general improvement.

## Shared conditions

- 1080×1440, 30 fps, 300 frames; identical narration bytes for each pair.
- Same starter, pinned dependency lock, technical baseline and topic brief.
- Same model (`gpt-6.1-sol`) and reasoning setting (`medium`), chosen during infrastructure pilot before formal freeze.
  The initial xhigh pilot was aborted on connection timeouts, not scored. Record actual CLI and tool versions.
- Fresh nonpersistent `codex exec` sessions; ignore user config for these calls,
  disable host skill discovery, memories, plugins and multi-agent execution;
  omit project/global AGENTS context through the per-run config. Do not change
  global settings or bypass execution policy. Record the experimental discovery
  flag as an environment limitation.
- The model returns a plan and Scene TSX through a JSON schema. All content it
  needs is in the prompt. Tool use is forbidden and an observed tool call fails
  protocol validation. This constrains filesystem/context contamination.
- Both arms receive the same technical baseline, paraphrased from official
  Remotion documentation. B additionally receives this Skill and its references
  as explicit instruction context. This measures explicit loading, not automatic
  skill discovery quality.

## Budget and sequence

Pilot: T1 A/B once, excluded from formal counts. Fix infrastructure before freeze.

Formal: T1, T2, T3 × two repetitions × A/B = 12 tasks / 6 pairs.
Order: T1r1 AB, T1r2 BA, T2r1 BA, T2r2 AB, T3r1 AB, T3r2 BA.

One initial generation + at most one uniform review pass per task. Every model
call has the same 600-second ceiling. Review receives the current source,
compiler/render diagnostics and frames at 0, 5 and 9.5 seconds. This is frame-
assisted model review, not evidence that the model watched a complete video.
Save both stages, usage and elapsed time. Up to 24 source/render versions result.

No extra aesthetic intervention by the experiment author. A failed final render
remains failed; do not rerun until a preferred output appears. Abort a protocol-
invalid batch rather than silently substituting a new condition.

Freeze hashes of Skill contents, common inputs, audio, starter and dependency
lock. Record immutable source states for each stage. Post-freeze changes need a
new experiment/version. Do not claim exact model-output reproducibility.

## Viewing and reporting

Check video integrity, audio, start/middle/end seek and actual browser playback.
Then prepare anonymous clips for three independent viewers. Ask the common
comprehension question before asking preference, readability, narration
alignment and slideshow feel. Record involvement and whether group labels were
known. Keep raw responses; do not substitute model scores for human votes.

Proposed decision guide: in at least two topics, both repeats are judged clearer
and more coherent by at least two of three viewers, without repeated readability
regression in another topic. This is a product decision guide, not significance.
Report technical failures, time, tokens and manual work separately. Missing
billing data is unknown, not free.

Main video example is preselected T1r1. If it cannot play, show that failure and
use T1r2 as the predetermined visual fallback. Include all other cases in the
results index. Same crop, scale, playback speed, duration and audio treatment in
both presentation arms.

Before release, fill results with actual states. An experimental release may
state that human review is pending; it must not claim a quality improvement.
