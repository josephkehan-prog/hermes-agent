---
name: humanizer
description: "Humanize text: strip AI-isms and add real voice."
version: 2.5.1
author: Siqi Chen (@blader, https://github.com/blader/humanizer), ported by Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [writing, editing, humanize, anti-ai-slop, voice, prose, text]
    category: creative
    homepage: https://github.com/blader/humanizer
    related_skills: [songwriting-and-ai-music]
---

# Humanizer: Remove AI Writing Patterns

Identify and remove signs of AI-generated text to make writing sound natural and human. Based on Wikipedia's "Signs of AI writing" guide (maintained by WikiProject AI Cleanup), derived from observations of thousands of AI-generated text instances.

**Key insight:** LLMs use statistical algorithms to guess what should come next. The result tends toward the most statistically likely completion, which is how the telltale patterns below get baked in.

## When to use this skill

Load this skill whenever the user asks to:
- "humanize", "de-AI", "de-slop", or "un-ChatGPT" a piece of text
- rewrite something so it doesn't sound like it was written by an LLM
- edit a draft (blog post, essay, PR description, docs, memo, email, tweet, resume bullet) to sound more natural
- match their voice in writing they're producing
- review text for AI tells before publishing

Also apply this skill to **your own** output when writing user-facing prose — release notes, PR descriptions, documentation, long-form explanations, summaries. Hermes's baseline voice already strips most of these, but a focused pass catches what slips through.

## How to use it in Hermes

The text usually arrives one of three ways:
1. **Inline** — user pastes the text directly into the message. Work on it in-place, reply with the rewrite.
2. **File** — user points at a file. Use `read_file` to load it, then `patch` or `write_file` to apply edits. For markdown docs in a repo, a targeted `patch` per section is cleaner than rewriting the whole file.
3. **Voice calibration sample** — user provides an additional sample of their own writing (inline or by file path) and asks you to match it. Read the sample first, then rewrite. See the Voice Calibration section below.

Always show the rewrite to the user. For file edits, show a diff or the changed section — don't silently overwrite.

## Your task

When given text to humanize:

1. **Identify AI patterns** — scan for the 29 patterns listed below.
2. **Rewrite problematic sections** — replace AI-isms with natural alternatives.
3. **Preserve meaning** — keep the core message intact.
4. **Maintain voice** — match the intended tone (formal, casual, technical, etc.). If a voice sample was provided, match it specifically.
5. **Add soul** — don't just remove bad patterns, inject actual personality. See PERSONALITY AND SOUL below.
6. **Do a final anti-AI pass** — ask yourself: "What makes the below so obviously AI generated?" Answer briefly with any remaining tells, then revise one more time.


## Voice Calibration (optional)

If the user provides a writing sample (their own previous writing), analyze it before rewriting:

1. **Read the sample first.** Note:
   - Sentence length patterns (short and punchy? Long and flowing? Mixed?)
   - Word choice level (casual? academic? somewhere between?)
   - How they start paragraphs (jump right in? Set context first?)
   - Punctuation habits (lots of dashes? Parenthetical asides? Semicolons?)
   - Any recurring phrases or verbal tics
   - How they handle transitions (explicit connectors? Just start the next point?)

2. **Match their voice in the rewrite.** Don't just remove AI patterns — replace them with patterns from the sample. If they write short sentences, don't produce long ones. If they use "stuff" and "things," don't upgrade to "elements" and "components."

3. **When no sample is provided,** fall back to the default behavior (natural, varied, opinionated voice from the PERSONALITY AND SOUL section below).

### How to provide a sample
- Inline: "Humanize this text. Here's a sample of my writing for voice matching: [sample]"
- File: "Humanize this text. Use my writing style from [file path] as a reference."


## PERSONALITY AND SOUL

Avoiding AI patterns is only half the job. Sterile, voiceless writing is just as obvious as slop. Good writing has a human behind it.

### Signs of soulless writing (even if technically "clean"):
- Every sentence is the same length and structure
- No opinions, just neutral reporting
- No acknowledgment of uncertainty or mixed feelings
- No first-person perspective when appropriate
- No humor, no edge, no personality
- Reads like a Wikipedia article or press release

### How to add voice:

**Have opinions.** Don't just report facts — react to them. "I genuinely don't know how to feel about this" is more human than neutrally listing pros and cons.

**Vary your rhythm.** Short punchy sentences. Then longer ones that take their time getting where they're going. Mix it up.

**Acknowledge complexity.** Real humans have mixed feelings. "This is impressive but also kind of unsettling" beats "This is impressive."

**Use "I" when it fits.** First person isn't unprofessional — it's honest. "I keep coming back to..." or "Here's what gets me..." signals a real person thinking.

**Let some mess in.** Perfect structure feels algorithmic. Tangents, asides, and half-formed thoughts are human.

**Be specific about feelings.** Not "this is concerning" but "there's something unsettling about agents churning away at 3am while nobody's watching."

### Before (clean but soulless):
> The experiment produced interesting results. The agents generated 3 million lines of code. Some developers were impressed while others were skeptical. The implications remain unclear.

### After (has a pulse):
> I genuinely don't know how to feel about this one. 3 million lines of code, generated while the humans presumably slept. Half the dev community is losing their minds, half are explaining why it doesn't count. The truth is probably somewhere boring in the middle — but I keep thinking about those agents working through the night.


## AI Writing Pattern Quick Reference

29 patterns grouped by category, with words/phrases to watch. Full problem
statements and before/after examples for each: read
`references/patterns.md` when you need the exact rationale or an example to
model a rewrite on.

**Content patterns:**
1. Undue emphasis on significance — stands/serves as, is a testament, pivotal moment, evolving landscape, indelible mark
2. Undue emphasis on notability — independent coverage, active social media presence
3. Superficial -ing endings — highlighting, underscoring, reflecting, showcasing
4. Promotional language — vibrant, nestled, breathtaking, renowned, must-visit, stunning
5. Vague attributions — industry reports, experts argue, observers have cited
6. Outline-like "Challenges and Future Prospects" sections

**Language & grammar:**
7. Overused AI vocabulary — delve, crucial, tapestry, testament, underscore, pivotal, intricate
8. Copula avoidance — "serves as/stands as/boasts" instead of "is/are"
9. Negative parallelisms & tailing negations — "not just X, it's Y", "no guessing"
10. Rule of three overuse (forcing ideas into groups of three)
11. Elegant variation (synonym cycling instead of repeating a word)
12. False ranges — "from X to Y" on things that aren't on a scale
13. Passive voice / subjectless fragments — "No configuration file needed"

**Style:**
14. Em dash overuse
15. Overuse of boldface
16. Inline-header vertical lists ("- **Performance:** Performance has been...")
17. Title case in headings
18. Emojis decorating headings/bullets
19. Curly quotation marks

**Communication:**
20. Collaborative-communication artifacts — "I hope this helps!", "Let me know"
21. Knowledge-cutoff disclaimers — "as of my last update", "based on available information"
22. Sycophantic/servile tone — "Great question! You're absolutely right"

**Filler & hedging:**
23. Filler phrases — "in order to", "due to the fact that", "at this point in time"
24. Excessive hedging — "could potentially possibly be argued that"
25. Generic positive conclusions — "the future looks bright"
26. Hyphenated word-pair overuse — third-party, cross-functional, data-driven, real-time
27. Persuasive authority tropes — "the real question is", "at its core"
28. Signposting/announcements — "let's dive in", "here's what you need to know"
29. Fragmented headers — heading followed by a sentence that just restates it

---

## Process

1. Read the input text carefully (use `read_file` if it's a file).
2. Identify all instances of the patterns above.
3. Rewrite each problematic section.
4. Ensure the revised text:
   - Sounds natural when read aloud
   - Varies sentence structure naturally
   - Uses specific details over vague claims
   - Maintains appropriate tone for context
   - Uses simple constructions (is/are/has) where appropriate
5. Present a draft humanized version.
6. Prompt yourself: "What makes the below so obviously AI generated?"
7. Answer briefly with the remaining tells (if any).
8. Prompt yourself: "Now make it not obviously AI generated."
9. Present the final version (revised after the audit).
10. If the text came from a file, apply the edit with `patch` (targeted) or `write_file` (full rewrite) and show the user what changed.

## Output Format

Provide:
1. Draft rewrite
2. "What makes the below so obviously AI generated?" (brief bullets)
3. Final rewrite
4. A brief summary of changes made (optional, if helpful)


## Full Example

A complete before → draft → audit → final walkthrough, with a full changelog
of what was removed and why: read `references/example.md` when you want to
see the whole Process (above) applied end to end, or need a model for your
own audit pass.

## Attribution

This skill is ported from [blader/humanizer](https://github.com/blader/humanizer) (MIT licensed), which is itself based on [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), maintained by WikiProject AI Cleanup. The patterns documented there come from observations of thousands of instances of AI-generated text on Wikipedia.

Original author: Siqi Chen ([@blader](https://github.com/blader)). Original repo: https://github.com/blader/humanizer (version 2.5.1). Ported to Hermes Agent with Hermes-native tool references (`read_file`, `patch`, `write_file`) and guidance for when to load the skill; the 29 patterns, personality/soul section, and full worked example are preserved verbatim from the source (moved to `references/` here for progressive disclosure). Original MIT license preserved in the `LICENSE` file alongside this `SKILL.md`.

Key insight from Wikipedia: "LLMs use statistical algorithms to guess what should come next. The result tends toward the most statistically likely result that applies to the widest variety of cases."
