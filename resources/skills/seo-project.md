---
name: seo-project
description: >
  Multi-project management. Switch context between projects, each with its own brand,
  URL, and content calendar. Use when user says "project list", "project switch",
  "project new", or "project status".
---

# Project Manager

Manages multiple SEO/content projects. Each project has its own brand context, URL,
and content calendar stored at `~/.seo-projects/<name>/context.md`.

Active project is tracked in `~/.seo-projects/active`.

---

## Storage Layout

```
~/.seo-projects/
  active                        ← name of the active project (1 line)
  diverfi/
    context.md
  project-b/
    context.md
```

Project slug = lowercase, no spaces, no diacritics. `diverFi` → `diverfi`.

**Slugify rule:** Keep only a-z, 0-9, hyphens. Replace spaces with hyphens. Strip diacritics and all other characters. Lowercase. Max 30 chars.
- `diverFi` → `diverfi`
- `My Blog 2026` → `my-blog-2026`
- `Client ABC` → `client-abc`

Recommend ASCII-only names for reliable matching: `diverfi`, `my-blog`, `client-abc`.

---

## Commands

### `project list`

List all projects. Mark active with `→`.

Steps:
1. Read `~/.seo-projects/active` to get active project name (empty = none)
2. List all subdirectories in `~/.seo-projects/` (skip non-directories)
3. For each directory, read the `name:` field from its `context.md` frontmatter
4. Output:

```
Projects:
  → diverFi   (diverfi.xyz)      ← active
    Project B  (projectb.com)
    Project C  (projectc.io)
```

If no projects exist:
```
No projects yet. Create one with: project new <name> <url>
```

---

### `project switch <name>`

Set a project as active.

Steps:
1. Slugify input: lowercase, strip spaces and diacritics. `diverFi` → `diverfi`
2. Check `~/.seo-projects/<slug>/context.md` exists. If not:
   ```
   Project "<name>" not found. Run: project list
   ```
3. Write slug to `~/.seo-projects/active`
4. Read the project's `context.md` and show a 3-line summary:
   ```
   Switched to diverFi (diverfi.xyz)
   Audience: Working adults 22-35, new to DeFi
   Content queue: 2 items pending
   ```

---

### `project new <name> <url>`

Create a new project from template.

Steps:
1. Slugify name
2. Check `~/.seo-projects/<slug>/` does NOT exist. If it does:
   ```
   Project "<slug>" already exists. Use: project switch <name>
   ```
3. Create `~/.seo-projects/<slug>/context.md` by copying
   `resources/context/project.template.md`, then substituting:
   - `My Project` → `<name>`
   - `https://example.com` → `<url>`
   - `YYYY-MM-DD` → today's date

4. Set as active project (write slug to `~/.seo-projects/active`)
5. Output:
   ```
   Created: ~/.seo-projects/<slug>/context.md
   Active project → <name>

   Next: fill in context.md then run: content write <topic>
   ```

---

### `project status`

Show full context of active project.

Steps:
1. Read `~/.seo-projects/active`. If empty:
   ```
   No active project. Run: project list
   ```
2. Read `~/.seo-projects/<slug>/context.md`
3. Output the file content in full, then show content calendar summary:
   ```
   Content Calendar:
     Pending: 3 items
     Done:    1 item
   ```

---

## Integration with other skills

When `project switch` is called, all subsequent skill runs in the session
will use the active project context automatically (handled in each skill's Startup).

To check active project in any skill:
1. Read `~/.seo-projects/active` (1 line, slug)
2. Read `~/.seo-projects/<slug>/context.md`
3. Use brand/audience/URL fields as additional context

---

## URL Resolution

When a skill receives a project name instead of a URL (e.g., `seo audit diverFi`):
1. Slugify the input
2. Check if `~/.seo-projects/<slug>/context.md` exists
3. If yes: extract the `url:` field from frontmatter and use it as the target URL
4. If no: treat input as a raw URL

---

## Trigger phrases

- `project list`
- `project switch <name>`
- `project new <name> <url>`
- `project status`
