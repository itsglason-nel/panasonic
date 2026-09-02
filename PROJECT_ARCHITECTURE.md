# PMPC Data Logger: Architecture Reference

> Scope: source inventory and dependency map for the working tree on 2026-09-01. This is a technical reference, not a database migration or a replacement for operational validation.

## Purpose and maintenance contract

This document keeps architectural context in the repository so subsequent work can be scoped without repeatedly rediscovering the application. It has **no runtime import, UI asset, database connection, migration, trigger, stored-procedure, or launcher dependency**.

Whenever a source file is added, modified, renamed, or removed, update the affected sections in this document in the same change:

1. Update the component, route, template, schema, or tool entry that changed.
2. Update the dependency and impact notes when a public contract changed (route, payload, database column/table, stored procedure, trigger, template element ID, JavaScript function, or environment variable).
3. Add a dated entry to **Change ledger** with file paths and a concise behavioral summary.
4. Do not state that a migration has been applied unless it has actually been run against the target database.

The baseline is intentionally descriptive. It does not execute code or inspect the live MySQL/Redis/PLC environment, so no production state is changed by reading or updating it.

## System overview

PMPC Data Logger is a factory-floor production-management application.

```text
Browser
  |- Jinja pages: login, dashboard, admin, scoreboards, print documents
  |- Vanilla JavaScript + app.css
  `- JSON requests / Socket.IO
          |
Flask application factory (app/__init__.py)
  |- auth blueprint: session login and dashboard
  |- api blueprint: station submission and live reads
  |- admin blueprint: operational administration, reports, printing
  `- scoreboard blueprint: public line display and scoreboard data
          |
SQLAlchemy models + selected raw SQL
          |                         \
MySQL 8 (production history, schedules, linestat)   Redis (sessions, latest weight)
          |
Stored procedure + AFTER INSERT triggers
          |
linestat: PLC-facing/current-line state

WeightReader: serial/TCP PLC -> Redis, with current_weight.txt fallback
Windows launcher: starts and supervises the local application process
```

## Runtime and configuration

| Area | Source of truth | Notes |
| --- | --- | --- |
| WSGI/server entry | `wsgi.py` | Creates `app`; runs Socket.IO with Eventlet when executed directly. |
| Application factory | `app/__init__.py` | Initializes SQLAlchemy, Redis/filesystem session storage, Flask-Login, Socket.IO, CSRF, blueprints, security headers, error handling, and request-time schedule auto-close. |
| Configuration | `config.py`, `.env` | MySQL, Redis, secret, server, serial/PLC, gas tolerance, backup and BOM paths. `.env` is secret and ignored by Git. |
| Python dependencies | `requirements.txt` | Flask, Socket.IO/Eventlet, SQLAlchemy/PyMySQL, Redis/session/auth/CSRF, serial, Excel, launcher, Gunicorn. |
| Windows operations | `launcher.pyw`, `Launchers/` | GUI launcher plus system-check, database-update, debug, and start scripts. |

`create_app()` defaults to `FLASK_CONFIG=development`. It falls back to filesystem-backed sessions when Redis is unavailable. Its `before_request` handler finalizes prior production days and may reset stale zero-WIP `linestat` rows; changes here have production data consequences.

## Backend components

### Routes and pages

| Module | URL responsibility | Primary consumers / dependencies |
| --- | --- | --- |
| `app/routes/auth.py` | `/`, `/auth/login`, `/dashboard`, logout, password change | `login.html`, `dashboard.html`, Flask-Login `User`. Login has in-memory IP lockout state. |
| `app/routes/api.py` | `/api/unit`, BOM/serial/schedule lookups, station submission, PIT and current-weight reads | Scanner/operator workflow; station records, `linestat`, Redis/file weight fallback, Socket.IO. |
| `app/routes/admin.py` | `/admin`, `/admin/api/*`, `/sys/api/*`, printing, QC, WIP, conveyor, shifts, transfer slips | `admin.html`, included modal/script templates, all operational models, raw SQL and `linestat` workflow. Admin role is required. |
| `app/routes/scoreboard.py` | `/scoreboard`, per-line scoreboard, scoreboard data/log/model APIs | Scoreboard templates, schedule/history tables. Some endpoints sit at `/api/scoreboard/*` outside the API blueprint. |

Route changes are API-contract changes. Check the template JavaScript `fetch()` callers, scanner callers, Socket.IO event names, role checks, serialized field names, and status codes before changing them.

### Services

| Module | Responsibility | Risk boundary |
| --- | --- | --- |
| `barcode_parser.py` | Decodes safety-part QR input into part number, lot barcode, and raw data. | Parser output is used by station validation. |
| `linestat_monitor.py` | Gets/initializes current state; invokes `sp_linestat_shift_sequence`; forces PLC-visible refresh after manual schedule edits. | Direct stored-procedure and mutable production-state dependency. |
| `weight_reader.py` | Background serial/TCP Keyence or indicator reader; writes `current_weight_kg` to Redis, falls back to `current_weight.txt`. | Hardware and live station input. Do not start it in tests without an explicit mock configuration. |
| `pit_generator.py` | Optional PIT JSON persistence for future operator-station models. Imports missing models lazily and returns `None` until they exist. | Present but not connected to the current model set. |

## Data model and database automation

### SQLAlchemy tables

| Domain | Tables / model modules | Purpose |
| --- | --- | --- |
| Identity/configuration | `users` (`user.py`), `lines` (`line.py`), `modules` (`module.py`), `tags` (`tag.py`), `areas` (`area.py`), `shifts` (`shift.py`) | Roles, active configuration, model production areas, and production-shift definitions. |
| Planning/reference | `worksched` (`worksched.py`), `partref` (`partref.py`), `modelref` (`modelref.py`) | Line/date/sequence plan vs. actuals; BOM parts; serial starts, areas, program and tolerance references. |
| Live PLC state | `linestat` (`linestat.py`), `system_state` (raw SQL) | Current station model, variance and configuration data; auto-close completion marker. |
| Station history | `crs`, `att`, `gms`, `spamsi`, `spamso`, `insp2`, `insp3_run`, `insp4`, `packaging` | Production and inspection history across stations. |
| Document workflow | `transfer_slips` (`transfer_slip.py`) | Transfer header and serialized unit serial list. |

Models are registered through imports in `app/models/__init__.py`. A new model is not sufficient by itself: add its import, migration, route/query contract, UI usage if applicable, and this document.

### Stored procedure and triggers

The canonical current SQL definitions are duplicated in `migrations/000_new_initial_schema.sql` and `migrations/002_add_to_server.sql`; the scratch SQL files provide targeted reapplication inputs.

| Object | Defined in | Effect |
| --- | --- | --- |
| `sp_linestat_shift_sequence` | `000_new_initial_schema.sql`, `002_add_to_server.sql`, `scratch_sp.sql` | Advances or initializes station-specific line state from `worksched` and writes `linestat`. Called by `linestat_monitor.py`. |
| `after_crs_insert`, `after_att_insert`, `after_gms_insert` | Initial/new schema and server migration | Synchronize live-state variance after station inserts. |
| `after_spamsi_insert`, `after_spamso_insert` | Initial/new schema and server migration | Synchronize safety-parts station state. |
| `after_insp2_insert`, `after_insp3_run_insert`, `after_insp4_insert`, `after_packaging_insert` | New/server migrations and `scratch_triggers.sql` | Advance late-stage workflow state after history inserts. |

Treat these as one transactionally coupled workflow: a station insert can update `linestat`, which can change downstream PLC behavior and the next station’s accepted model. Never modify an insert model, a trigger, or the stored procedure in isolation. Validate on a backup/test database with a multi-station schedule before deployment.

### Migration and maintenance files

| File(s) | Role | Caution |
| --- | --- | --- |
| `migrations/000_new_initial_schema.sql` | Broad schema plus procedure/triggers. | Contains repeated/revised definitions; review statement order before a fresh deployment. |
| `migrations/001_initial_schema.sql` | Earlier baseline schema. | Contains schema evolution statements and data inserts. |
| `migrations/002_add_modelref.sql`, `002_add_to_server.sql`, `003_add_areas.sql` | Incremental production schema/state updates. | `002_add_to_server.sql` includes procedure/triggers and the Area registry; `003_add_areas.sql` is the focused idempotent Area migration. |
| `run_alter.py`, `run_triggers.py` | Run the scratch ALTER / procedure-trigger SQL. | Directly mutates the configured database. |
| `tools/run_migration.py`, `migrate_*.py`, `rename_modelref.py`, `widen_columns.py`, `alter_db.py` | One-off/manual database utilities. | Some target historical filenames or perform destructive schema changes; inspect before running. |
| `tools/init_database.py`, `backup_db.py`, `check_db.py`, seed scripts | Database creation, backup, inspection, seed data. | Backup retention deletes old backup files; seed tools change data. |

Known migration caution: `tools/migrate_linestat.py` references `migrations/003_linestat.sql`, which is not in the current inventory. Do not run it until its target migration is restored or corrected.

## Frontend architecture

| Layer | Files | Contract |
| --- | --- | --- |
| Shared shell | `templates/base.html`, `static/css/app.css`, `static/js/app.js` | Base layout, global styles and shared client behavior. |
| Authentication/dashboard | `login.html`, `dashboard.html` | Auth forms and production dashboard surface. |
| Administration | `admin.html`, `admin/components/modals.html`, `admin/components/scripts.html` | Large single-page admin interface, including Modules, Tags, and dynamic Areas management. Element IDs, inline handlers and script functions form an internal public contract. |
| Station scanning | `static/js/scanner.js` | Scanner input and station submission integration. |
| Scoreboards | `templates/scoreboard/all_lines.html`, `templates/scoreboard/line.html`, `routes/scoreboard.py` | Line display and polling/data contracts. |
| Printable documents | `print_tag.html`, `print_transfer_slip.html`, `print_qc_report.html`, `qc_report_print.html` | Server-rendered print formats; do not assume screen CSS applies. |

The admin templates include external Flatpickr and Tom Select CDN scripts. This differs from the README’s offline-only description and should be considered before any network-isolation claim or deployment change.

## Repository map

```text
app/
  __init__.py                 Flask factory and extension wiring
  models/                     ORM table mappings
  routes/                     HTTP/API blueprint handlers
  services/                   barcode, line-state, PIT, hardware-weight logic
  static/                     CSS and browser JavaScript
  templates/                  Jinja pages, admin includes, printable layouts
migrations/                  MySQL schema, procedure, trigger definitions
tools/                       Operational database/seed/backup utilities
Launchers/                   Windows user-facing startup/maintenance scripts
scratch/                     Diagnostic and experimental helpers; not runtime
docs/                        Reference assets and source material
launcher.pyw                 Windows CustomTkinter launcher
config.py                    Environment-driven configuration
wsgi.py                      Server entry point
run_alter.py/run_triggers.py Targeted database update runners
```

Binary/reference files under `docs/reference/` (PDF, PowerPoint, spreadsheet, image) were inventoried but not treated as executable architecture. `node_modules/`, `.git/`, generated caches and `.env` are excluded from this reference.

## Change-impact checklist

Before changing a component, identify its paired contracts:

| Change type | Also inspect |
| --- | --- |
| Route, response, parameter, status code | Browser `fetch()`/scanner caller, templates, role/CSRF behavior, tests. |
| Template element ID, form field, inline handler | `admin/components/scripts.html`, `app.js`, `scanner.js`, CSS selectors. |
| Model/table/column | ORM mapping, SQL migrations, raw SQL, procedure/triggers, indexes, admin serialization, print templates. |
| Area configuration | `areas` API and model, both model-area selects, `modelref.area` validation, schema copies, and inactive-area retention behavior. Do not replace the `modelref.area` or `linestat.area` string contract without a PLC workflow migration. |
| Station insertion or status | All trigger definitions, `linestat`, work schedule sequence, scoreboard and WIP views. |
| `linestat` field or procedure | Every trigger, `linestat_monitor.py`, API station submission, PLC/launcher expectations. |
| Environment/configuration | `.env` deployment settings, launcher behavior, Redis/MySQL/serial availability, production versus testing config. |
| Weight reader | Hardware protocol, Redis key `current_weight_kg`, `current_weight.txt` fallback, `/api/weight/current`. |
| Migration/tool | Existing production schema, idempotency, backup/rollback plan, active database target. |

## Verification baseline

No UI, Python, SQL, trigger, stored procedure, launcher, or configuration file was edited to add this reference. Documentation-only changes should at minimum pass `git diff --check`. For functional work, use proportionate checks: import/app startup without production hardware, affected route tests, browser workflow validation, and a disposable MySQL copy for schema/trigger/procedure changes.

## Change ledger

| Date | Files | Summary |
| --- | --- | --- |
| 2026-09-01 | `PROJECT_ARCHITECTURE.md`, `AGENTS.md` | Added repository architecture reference and mandatory documentation-sync instruction. No application or database behavior changed. |
| 2026-09-01 | `app/models/area.py`, admin route/UI files, `migrations/000_new_initial_schema.sql`, `migrations/002_add_to_server.sql`, `migrations/003_add_areas.sql` | Added dynamic Area configuration while retaining the existing `modelref.area` to `linestat.area` stored-procedure contract. Schema changes were added but not executed. |
| 2026-09-01 | `app/models/spamsi_unique_ref.py`, `app/routes/admin.py`, `app/templates/admin/components/modals.html`, `app/templates/admin/components/scripts.html`, `migrations/000_new_initial_schema.sql`, `migrations/002_add_to_server.sql`, `migrations/004_add_spamsi_unique_codes.sql`, `scratch_sp.sql` | Added the optional per-model SPAMSI unique-code reference table and extended the existing model-reference API/UI contract. The `linestat.inuniqe` field remains `VARCHAR(4)` and is populated from the next model’s configured mapping while being cleared when the SPAMSI sequence is exhausted. |
| 2026-09-01 | `app/models/modelref.py` | Fixed `ModelRef.to_dict()` to include `spamsi_unique_code` field by querying the `spamsi_unique_refs` table. This ensures the BOM edit flow and all model configuration endpoints return the complete field set for proper UI pre-population and API contract completeness. No schema, route, or trigger changes required. |
| 2026-09-01 | `app/templates/admin/components/modals.html`, `app/templates/admin/components/scripts.html`, `app/routes/admin.py` | Reorganized "New Model - Add Parts" modal: moved SPAMSI Unique Code to appear after Program H/F (grid layout now displays Area/Serial Start in row 1, Program H/F in row 2, SPAMSI code in row 3). Made SPAMSI Unique Code required for new model creation (enforced via client-side validation in `saveBom()` and `saveModelConfig()`, and server-side validation in `update_modelref()`). Requirement applies to NEW models only; existing models remain backward compatible with optional codes. Both "New Model" and "Edit Model Configuration" modals synchronized for consistent UX. |
| 2026-09-01 | `app/routes/admin.py`, `app/templates/admin/components/scripts.html` | Fixed `get_prod_tag_tracker` logic to consider `PASS` and `OK` as valid station statuses alongside `GOOD` when evaluating overall Tag Status. Added direct click-to-print functionality on Prod Tag Tracker rows. |
| 2026-09-01 | `app/templates/admin/print_tag.html` | Updated javascript template logic to consider `PASS` and `OK` statuses when rendering checkboxes for all inspection sections (ATT, GMS, INSP2, INSP3_RUN, INSP4). Injected `att_brazzer1` through `att_brazzer7` text values into the Brazing / Prep Processes table. |
| 2026-09-01 | `app/templates/admin.html`, `app/templates/admin/components/modals.html`, `app/templates/admin/components/scripts.html` | Resolved critical Javascript ReferenceErrors (`st is not defined`, `rowNum is not defined`) causing table loading crashes for INSP2, INSP3Vib, INSP4, Repair, and Packaging endpoints. Added Line No field to ATT and GMS Details modals, and created dedicated GMS Details modal. Corrected table column mappings for INSP3Run (21 columns) and Packaging (10 columns) and fixed data misalignment across headers. |
| 2026-09-01 | `app/routes/admin.py`, `app/templates/admin/components/modals.html`, `app/templates/admin/components/scripts.html` | Resolved `AttributeError` crashes in `get_insp3run_data`, `get_insp4_data`, and `get_packaging_data` caused by mismatched field names and unsafe timestamp formatting. Injected missing `setupTableLoading` state in `loadINSP3RunData`. Created and wired dedicated details modals for INSP2, INSP3Vib, CBPCB, INSP4, and Repair tables to prevent routing to the default CRS modal. |
| 2026-09-01 | `app/routes/admin.py`, `app/templates/admin/components/scripts.html` | Fixed UI tabs for INSP3Run, INSP4, and Packaging to automatically load data when clicked by adding the missing `targetPanel` hooks. Added missing `finishTableLoading` call in `loadINSP3RunData` preventing perpetual loading states. Added `lineno` to the `get_att_data` payload to populate the Air Tight Test Record Details modal correctly. || 2026-09-02 | migrations/005_add_spamso_outmodel_refs.sql, pp/models/modelref.py, pp/models/linestat.py, pp/models/spamso_outmodel_ref.py, pp/models/__init__.py, pp/routes/admin.py, pp/templates/admin/components/modals.html, pp/templates/admin/components/scripts.html, scratch_sp.sql | Upgraded gmstolpos/gmstolneg from DECIMAL(2,0) to DECIMAL(4,2) in modelref, linestat, and gastolref tables, enabling decimal precision (e.g. 5.25) for GMS gas charge tolerances. Added outmodel VARCHAR(14) column to linestat after outvar to carry the SPAMSO output model reference. Created new spamso_outmodel_refs lookup table (keyed by modelcode) and corresponding SpamsoOutmodelRef ORM model. Extended update_modelref() to upsert/delete rows from spamso_outmodel_refs when the spamso_outmodel field is saved. Rebuilt sp_linestat_shift_sequence to populate linestat.outmodel from spamso_outmodel_refs on SPAMSO sequence shift and clear it on exhaustion; also updated DECIMAL variable declarations to DECIMAL(4,2). Updated Model Configuration modal (Serial & Program tab) with new " SPAMSO Output Model\ text input (mc-spamso-outmodel). Gas tolerance inputs in GMS Target modal now use step=0.01. Migration 005 has been executed against the local development database. |
| 2026-09-02 | migrations/002_add_to_server.sql | Appended Migration 005 block: DECIMAL(4,2) ALTER statements for modelref/linestat, idempotent outmodel ADD COLUMN for linestat, spamso_outmodel_refs CREATE TABLE, and full rebuild of sp_linestat_shift_sequence with DECIMAL(4,2) tolerance variables, auto-populate of linestat.outmodel from spamso_outmodel_refs on SPAMSO shift, and NULL clear of outmodel on exhaustion. This makes 002 the single authoritative server-deploy script. |
