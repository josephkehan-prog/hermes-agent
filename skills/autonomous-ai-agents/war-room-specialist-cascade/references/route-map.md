# Niche route map

Choose by primary deliverable, not by incidental input format.

| If the user primarily needs | Route | Do not route when |
|---|---|---|
| A formatted dramatic script, scene, or adaptation | screenplay | Prose manuscript remains primary |
| Spoken-book or voiceover WAV files | audiobook | Music or sound design is primary |
| Timed words, transcript, SRT, or VTT | transcript-caption | The transcript is only an input to research |
| Validated fields from document pixels | structured-document | Visual inspection without a target schema is enough |
| Shot grammar, boards, animatic, or motion proof | previsualization | A complete edited video is already requested |

Resolve mixed work in dependency order, but invoke one worker per handoff:

1. screenplay before narration or previs;
2. narration before caption alignment;
3. still boards before motion proof;
4. extraction before archival synthesis.

Keep secondary needs in the handoff to the visible lead. Never invoke multiple
workers merely because several output formats were mentioned.
