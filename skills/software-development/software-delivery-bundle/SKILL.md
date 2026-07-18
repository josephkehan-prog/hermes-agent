---
name: software-delivery-bundle
description: Route a software change through each delivery stage.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    bundle: true
    domain: software-delivery
    tags: [bundle, software-delivery, implementation, quality]
    related_skills: [plan, spike, test-driven-development, systematic-debugging, simplify-code, requesting-code-review]
---

# Software Delivery Bundle

## Boundary

Move a repository change from request to verified handoff. Use this bundle for
multi-stage delivery, not for a single obvious edit or a request that asks only
for a plan, review, or diagnosis.

## Routing Table

| Request state | Primary skill | Exit evidence |
|---|---|---|
| Requirements or architecture unclear | `plan` | Decisions, paths, gates, and test strategy are explicit |
| A risky unknown needs a cheap probe | `spike` | Time-boxed evidence resolves the named uncertainty |
| New behavior is ready to implement | `test-driven-development` | Behavior test fails first, then passes |
| Existing behavior is broken | `systematic-debugging` | Root cause and reproduction are proven |
| Correct code is unnecessarily complex | `simplify-code` | Behavior is preserved with lower complexity |
| Change is ready for independent scrutiny | `requesting-code-review` | Review findings are addressed or recorded |

## Orchestration Workflow

1. Restate the requested outcome, non-goals, and authoritative acceptance
   evidence. Route ambiguity to `plan`; route one uncertain premise to `spike`.
2. Choose either the implementation lane (`test-driven-development`) or bug
   lane (`systematic-debugging`). Do not run both rituals mechanically.
3. Run the narrowest relevant tests after each behavioral change, then the
   repository-prescribed regression checks.
4. Use `simplify-code` only after correctness is established. Re-run the same
   behavior checks after simplification.
5. Use `requesting-code-review` for changes whose risk or scope benefits from
   an independent pass. Resolve actionable findings before handoff.

## Handoff Record

Carry one record with: requested outcome, assumptions, reproduction or failing
test, files changed, commands run, results, unresolved risks, and review
findings. Each stage appends evidence; it must not replace earlier evidence.

## Stop Conditions

- The request requires a product or security decision the user has not made.
- The reported bug does not reproduce and no stronger evidence is available.
- Tests reveal unrelated pre-existing failures that prevent attribution.
- The next action would publish, deploy, or destroy data without authority.

## Completion Gate

- [ ] Requested behavior is implemented at every relevant call path
- [ ] A behavioral test or equivalent runtime check proves the change
- [ ] Required repository checks pass, with pre-existing failures separated
- [ ] Simplification preserved behavior if it was performed
- [ ] Review findings are resolved or explicitly accepted
- [ ] Every changed file and remaining risk appears in the handoff

## Common Pitfalls

- Planning after implementation instead of resolving uncertainty first
- Treating a spike as production code
- Fixing one symptom without checking sibling call paths
- Refactoring before the behavior is protected
- Reporting "tests pass" without naming the tests actually run
