# Output Templates

Read this when you reach Step 4. Fill each template against the detected stack,
using the repo's real directory names rather than the placeholders shown. Omit any
file that has no content. For multi-project scopes, carry per-project sections
inside each doc. Keep each output file under ~150 lines.

## `agent_docs/architecture.md`

```markdown
# Architecture

## Overview
[2-3 sentence summary of what this codebase does and how it's structured]

## Layer Diagram
[ASCII or description of major layers and how they connect]

## Key Design Decisions
- **[Decision]**: [Why it was made, what it means for contributors]

## Data Flow
[How a typical request/job moves through the system]
```

## `agent_docs/patterns.md`

```markdown
# Coding Patterns

## [Pattern Name]
**Where used**: [files/directories]
**Pattern**:
[Code sketch or description; avoid copying full files, use file:line refs]

**Example**: `[real/path/from/this/repo]:45`
```

## `agent_docs/conventions.md`

```markdown
# Conventions

## Naming
- Files: [kebab-case / PascalCase / snake_case]
- Functions: [camelCase / snake_case]
- DB tables/columns: [convention]

## File Organization
- `[real-dir-from-profile]/` - [what goes here]
- `[real-dir-from-profile]/` - [what goes here]

## Error Handling
[How errors are created, wrapped, propagated]

## Testing
[Where tests live, how to run them, naming convention, what to test]

## Code Style
[Formatting, linters in use, import ordering]
```

## `agent_docs/data-access.md` (if applicable)

```markdown
# Data Access

## ORM / Query Layer
[What's used, how queries are written]

## Repository Pattern
[If present: how repos are structured, what they expose]

## Migrations
[Where they live, how to run them]
```

## `agent_docs/api.md` (if applicable)

```markdown
# API Design

## Protocol
[REST / gRPC / GraphQL / tRPC]

## Conventions
- Route naming: [pattern]
- Request validation: [library/approach]
- Response shape: [standard envelope or not]
- Error responses: [format]
- Versioning: [strategy]
```

## CLAUDE.md pointer block (Step 5)

Append (or create) this block in `CLAUDE.md` so Claude Code auto-loads the docs.
List only the files you actually created.

```markdown
## Reference Docs

The following files contain project-specific context. Read the relevant ones before making changes:

- `agent_docs/architecture.md` - Overall structure and key design decisions
- `agent_docs/patterns.md` - Recurring code patterns with file references
- `agent_docs/conventions.md` - Naming, file organization, error handling, testing
- `agent_docs/data-access.md` - ORM, repositories, migrations (if present)
- `agent_docs/api.md` - API protocol and conventions (if present)
```
