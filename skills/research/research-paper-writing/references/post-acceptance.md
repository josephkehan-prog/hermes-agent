# Post-Acceptance Deliverables & Workshop/Short Papers

Detailed guidance for Phase 8 (posters, talks, blog posts/social media) and for workshop and short-paper variants of the pipeline.

---

## Contents

- [Conference Poster](#conference-poster)
- [Conference Talk / Spotlight](#conference-talk--spotlight)
- [Blog Post / Social Media](#blog-post--social-media)
- [Workshop Papers](#workshop-papers)
- [ACL Short Papers & Findings](#acl-short-papers--findings)

---

## Conference Poster

Most conferences require a poster session. Poster design principles:

| Element | Guideline |
|---------|-----------|
| **Size** | Check venue requirements (typically 24"x36" or A0 portrait/landscape) |
| **Content** | Title, authors, 1-sentence contribution, method figure, 2-3 key results, conclusion |
| **Flow** | Top-left to bottom-right (Z-pattern) or columnar |
| **Text** | Title readable at 3m, body at 1m. No full paragraphs — bullet points only. |
| **Figures** | Reuse paper figures at higher resolution. Enlarge key result. |

**Tools**: LaTeX (`beamerposter` package), PowerPoint/Keynote, Figma, Canva.

**Production**: Order 2+ weeks before the conference. Fabric posters are lighter for travel. Many conferences now support virtual/digital posters too.

## Conference Talk / Spotlight

If awarded an oral or spotlight presentation:

| Talk Type | Duration | Content |
|-----------|----------|---------|
| **Spotlight** | 5 min | Problem, approach, one key result. Rehearse to exactly 5 minutes. |
| **Oral** | 15-20 min | Full story: problem, approach, key results, ablations, limitations. |
| **Workshop talk** | 10-15 min | Adapt based on workshop audience — may need more background. |

**Slide design rules:**
- One idea per slide
- Minimize text — speak the details, don't project them
- Animate key figures to build understanding step-by-step
- Include a "takeaway" slide at the end (single sentence contribution)
- Prepare backup slides for anticipated questions

## Blog Post / Social Media

An accessible summary significantly increases impact:

- **Twitter/X thread**: 5-8 tweets. Lead with the result, not the method. Include Figure 1 and key result figure.
- **Blog post**: 800-1500 words. Written for ML practitioners, not reviewers. Skip formalism, emphasize intuition and practical implications.
- **Project page**: HTML page with abstract, figures, demo, code link, BibTeX. Use GitHub Pages.

**Timing**: Post within 1-2 days of paper appearing on proceedings or arXiv camera-ready.

---

## Workshop Papers

Workshop papers and short papers (e.g., ACL short papers, Findings papers) follow the same pipeline (Phases 0-7) but with different constraints and expectations.

| Property | Workshop | Main Conference |
|----------|----------|-----------------|
| **Page limit** | 4-6 pages (typically) | 7-9 pages |
| **Review standard** | Lower bar for completeness | Must be complete, thorough |
| **Review process** | Usually single-blind or light review | Double-blind, rigorous |
| **What's valued** | Interesting ideas, preliminary results, position pieces | Complete empirical story with strong baselines |
| **arXiv** | Post anytime | Timing matters (see [submission-prep.md](submission-prep.md)) |
| **Contribution bar** | Novel direction, interesting negative result, work-in-progress | Significant advance with strong evidence |

**When to target a workshop:**
- Early-stage idea you want feedback on before a full paper
- Negative result that doesn't justify 8+ pages
- Position piece or opinion on a timely topic
- Replication study or reproducibility report

## ACL Short Papers & Findings

ACL venues have distinct submission types:

| Type | Pages | What's Expected |
|------|-------|-----------------|
| **Long paper** | 8 | Complete study, strong baselines, ablations |
| **Short paper** | 4 | Focused contribution: one clear point with evidence |
| **Findings** | 8 | Solid work that narrowly missed main conference |

**Short paper strategy**: Pick ONE claim and support it thoroughly. Don't try to compress a long paper into 4 pages — write a different, more focused paper.
