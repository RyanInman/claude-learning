# Extraction Guide

Read this when you reach Step 3 (Extract and Analyze). Synthesize the deep-scan
findings into the categories below. Filter to what the Repo Profile actually has
and skip any category that is absent (no API layer means no API section).

| Category | What to capture |
|---|---|
| Architecture | Overall structure (monolith/services/layers), data flow |
| Module conventions | How files are organized, what lives where |
| Naming | Files, functions, variables, DB columns |
| Error handling | How errors propagate and are surfaced |
| Data access | ORM vs raw SQL, repository pattern, query conventions |
| API design | REST/gRPC/GraphQL, request/response shapes, versioning |
| Auth & security | Auth strategy, middleware, permission checks |
| Testing | Unit vs integration split, test helpers, mocking approach |
| Dependency injection | Constructor injection, DI containers, global singletons (or lack of) |
| Async patterns | Promise chains, async/await, goroutines, background jobs |
| Config & env | How config is loaded, env var conventions |
| Logging & observability | Log format, tracing, metrics |

## Reading dependencies for architectural signal

The dominant manifest's dependency list often reveals design choices faster than
reading the source. Capture the choice and its implication, not just the package name:

- Prisma / TypeORM / SQLAlchemy / ActiveRecord -> ORM-based data access
- tRPC / GraphQL / gRPC -> type-safe or schema-first API layer
- FastAPI / asyncio / Tokio -> async-first runtime
- Rails / Django / Laravel -> convention-over-config MVC
- NestJS / Spring -> DI-container architecture
