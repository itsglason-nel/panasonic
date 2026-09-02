# Repository maintenance instructions

Before changing source, read `PROJECT_ARCHITECTURE.md` and use its impact checklist to identify the affected contracts.

For every added, modified, renamed, or deleted source file, update `PROJECT_ARCHITECTURE.md` in the same change. Update the relevant component/schema/contract entry and append a dated Change ledger row. Do not claim database deployment, migration execution, or production verification unless it actually occurred.

Treat UI element IDs, JavaScript function names, API paths/payloads, SQL tables/columns, stored procedures, triggers, `linestat` fields, environment variables, and launcher behavior as cross-component contracts. Preserve unrelated working-tree changes.
