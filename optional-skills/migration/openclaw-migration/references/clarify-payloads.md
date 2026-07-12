# Exact `clarify` Payload Shapes & Call Hygiene

## `clarify` call hygiene

The Hermes CLI `clarify` tool is limited to one choice at a time, up to 4
predefined choices, and an automatic `Other` free-text option — it does
**not** support true multi-select checkboxes in a single prompt.

For every `clarify` call:

- always include a non-empty `question`
- include `choices` only for real selectable prompts
- keep `choices` to 2-4 plain string options
- never emit placeholder or truncated options such as `...`
- never pad or stylize choices with extra whitespace
- never include fake form fields in the question such as `enter directory here`, blank lines to fill in, or underscores like `_____`
- for open-ended path questions, ask only the plain sentence; the user types in the normal CLI prompt below the panel

If a `clarify` call returns an error, inspect the error text, correct the payload, and retry once with a valid `question` and clean choices.

Do not end the turn with a normal assistant message such as "Let me present
the choices", "What would you like to do?", or "Here are the options" when a
user decision is required — collect it via `clarify` before producing more
prose. If multiple unresolved decisions remain, do not insert an explanatory
assistant message between them; after one `clarify` response is received,
your next action should usually be the next required `clarify` call.

## Payload shapes

Copy-paste JSON payloads for the decision flow described in SKILL.md's User
interaction protocol. Use these as the default pattern for each of the four
decision points plus the workspace-path follow-up.

- `{"question":"Your existing SOUL.md conflicts with the imported one. What should I do?","choices":["keep existing","overwrite with backup","review first"]}`
- `{"question":"One or more imported OpenClaw skills already exist in Hermes. How should I handle those skill conflicts?","choices":["keep existing skills","overwrite conflicting skills with backup","import conflicting skills under renamed folders"]}`
- `{"question":"Choose migration mode: migrate only user data, or run the full compatible migration including allowlisted secrets?","choices":["user-data only","full compatible migration","cancel"]}`
- `{"question":"Do you want to copy the OpenClaw workspace instructions file into a Hermes workspace?","choices":["skip workspace instructions","copy to a workspace path","decide later"]}`
- `{"question":"Please provide an absolute path where the workspace instructions should be copied."}`
