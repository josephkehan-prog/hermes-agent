# Code Wiki — Pitfalls, Verification, Re-Run Details

Read this when you're about to write output and want the full detail behind
the body's short pitfall list, or when re-running the skill against an
already-generated wiki.

## Pitfalls (full detail)

- **Fabricating components.** Every diagram node and claimed function call must be in the source. `read_file` before writing. The single biggest failure mode for auto-generated docs is plausible-sounding fabrication.
- **Generic AI prose.** "This module is responsible for..." is content-free. Say what the module actually does in domain-specific terms.
- **Restating code as prose.** A module doc that says "the `process` function processes things by calling `process_item` on each item" is worse than just linking to the function.
- **Mermaid > 50 nodes.** They don't render legibly. Split them.
- **Documenting tests, generated code, or vendored deps as if they were product code.** Skip them.
- **In-repo output without asking.** Default is `~/.hermes/wikis/`. Only write into the repo when the user explicitly requests it.
- **Mermaid special chars need quotes:** `A["Tool / Agent"]` not `A[Tool / Agent]`. `<br>` for line breaks inside a node.
- **Nested code fences in SKILL.md.** When writing a markdown example that contains a Mermaid block, use 4-backtick outer fences so the 3-backtick inner ` ```mermaid ` doesn't close the outer.
- **classDiagram generics** render as `~T~` (e.g. `List~Tool~`), not `<T>`.
- **GitHub Mermaid theme is fixed** — don't include `%%{init: ...}%%` blocks; they're stripped on render.

## Verification (full script)

After writing, verify:

1. **Mermaid blocks balance** — opens equal closes per file:
   ```bash
   for f in "$OUTPUT_DIR"/diagrams/*.md "$OUTPUT_DIR"/architecture.md; do
     opens=$(grep -c '^```mermaid' "$f")
     total=$(grep -c '^```' "$f")
     echo "$f: $opens mermaid blocks, $total total fences (expect total = opens*2)"
   done
   ```
2. **All expected files exist** —
   ```bash
   ls "$OUTPUT_DIR"/{README.md,architecture.md,getting-started.md,.codewiki-state.json} \
      "$OUTPUT_DIR"/modules/ "$OUTPUT_DIR"/diagrams/
   ```
3. **Module count matches what you intended** — `ls "$OUTPUT_DIR/modules" | wc -l` should equal the number of modules you committed to in Step 3.
4. **No fabricated paths** — sanity-check 2–3 source links resolve to real files.

## Re-Run / Update (full detail)

If `.codewiki-state.json` already exists at the target path:

- Read it for previous SHA and module list
- If source SHA matches: ask user if they want to regenerate or skip
- If SHA differs: offer to regenerate only modules with changed files (`git diff --name-only <old-sha> HEAD`)

Full incremental-regeneration is a future enhancement — for now, regenerating the whole thing is acceptable.
