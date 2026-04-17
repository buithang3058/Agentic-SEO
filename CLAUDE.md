
## SEO Agentic commands

These commands are handled by reading skill files directly — do NOT use the Skill tool for them.

| User types | Read this file and follow its instructions |
|-----------|-------------------------------------------|
| `project list` / `project switch` / `project new` / `project status` | `resources/skills/seo-project.md` |
| `write content <topic>` | `resources/skills/content-writer.md` |
| `seo audit <url>` | `resources/skills/seo-audit.md` |
| `seo page <url>` | `resources/skills/seo-page.md` |
| `seo plan <url>` | `resources/skills/seo-plan.md` |
| `seo geo <url>` | `resources/skills/seo-geo.md` |
| `content audit <url>` | `resources/skills/content-audit.md` |
| Any other `seo <sub-skill> <url>` | `resources/skills/seo-<sub-skill>.md` |

If unsure which file to read, check the commands table in `SKILL.md`.

## Skill routing (gstack — developer tools only)

When the user's request matches a gstack developer skill, invoke it using the Skill
tool as your FIRST action.

Key routing rules:
- Product ideas, "is this worth building", brainstorming → invoke office-hours
- Bugs, errors, "why is this broken", 500 errors → invoke investigate
- Ship, deploy, push, create PR → invoke ship
- QA, test the site, find bugs → invoke qa
- Code review, check my diff → invoke review
- Update docs after shipping → invoke document-release
- Weekly retro → invoke retro
- Design system, brand → invoke design-consultation
- Visual audit, design polish → invoke design-review
- Architecture review → invoke plan-eng-review
- Save progress, checkpoint, resume → invoke checkpoint
- Code quality, health check → invoke health
