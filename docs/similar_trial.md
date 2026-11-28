# Similar trial

The initial target is one eligible Similar at each `(archetypeKey, level)` pair. Check existing reviewed stock first. Active legacy stock still qualifies under the existing bank rules. A shared pair can cover multiple questions. The coverage report measures bank stock by pair. Check same-level and parent availability and look for worked-example exhaustion before promising a specific item. The learner can ask for another near-repeat or a broader scoped drill. Give an availability estimate for the selected authoring workflow.

## Authoring a parameter instance

The trial supports one family, `radical-equation-v1`, for the L3 radical-equation case check. It uses four bounded positive integer parameters named `a`, `b`, `d`, and `c`. The family requires two distinct rational candidates, exactly one real solution, and rejection of the same candidate class. It rules out denominator and coefficient degeneracies and trivial cancellation or guesses. Its numeric answer and worked path retain the same form as the independently checked parent. Other families, free-form edits, new contexts and context changes use the full workflow in [rule 07](../rules/07_problem_generation.md).

Authors can use `python -m math_engine.variant_bank --instance-template A B D C` to render a candidate parent problem for the full blind-solve and review workflow. Ingest that parent as a regular drill problem or variant after it passes independently. Keep the template's wording and steps. Use its drill problem locator (`DRL-.../Q...`) or the ID of an active reviewed variant in the destination bank.

In the usual `--add` draft, an instance entry contains only `parameterInstance`. Within it, supply `parent` and a `parameters` object with the four integer values. The bank computes the item and its provenance. Use `--sources-dir` to select the local source cache when needed. The batch is saved only after uniqueness, leak, quality, distractor provenance and originality checks pass. Missing originality data requires the full authoring workflow. On an ordinary draft entry, use `parentProblem` to select a drill parent at the exact pair when several match. A new, changed or removed story or an ambiguous parent requires a fresh independent context verdict and review.

## Measurement

For each authoring batch, record aggregate requested and ready counts, elapsed authoring time and time to fulfil, failed checks by kind, and tokens split into uncached input, cache reads, cache writes when reported, and output. Mark missing metrics as unmeasured and keep raw prompts, answers and learner records out of the log. Report any observed stock exhaustion and voluntary learner feedback separately. Use these observations to describe the trial. The sample provides no causal estimate of cost savings, retention or mastery.
