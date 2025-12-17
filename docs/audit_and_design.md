# Multi-Utility Tool — Functional Audit and UI Redesign Plan

## Feature Inventory and Intended Purpose
- **Plugin framework & manifesting**: Dynamic discovery and registration of feature tabs via `PluginAgent` and `PluginAPI`, enabling isolated tool delivery without core changes.
- **Unified UI shell**: Tkinter notebook layout with searchable navigation tree, status/progress bar, log viewer, and toast/error surfacing to keep tasks observable.
- **Logging & diagnostics**: Centralized logger setup plus diagnostics counters (`utils.diagnostics`) to time operations and track usage.
- **Task orchestration**: Thread-pool backed `TaskManager` with graceful shutdown and thread tracking in `AppCore` to coordinate work items.
- **Hotkeys & tray**: Optional global hotkey bindings and system tray presence for background control (disabled in headless/tests).
- **Progress & notifications**: Queue-driven status/progress updates, tray notifications, and toasts for user feedback.
- **Configuration**: YAML-backed config store at per-user config directory with safe load/save helpers.
- **Core processing plugins**:
  - **Audio**: Conversion, normalization, and batch presets.
  - **Audio Separator**: Stem separation/denoise flows (Demucs/DeepFilterNet) with UI gating for display environments.
  - **Image**: Batch resize/reformat/rename with aspect/margin handling.
  - **Text**: Merge, deduplicate, search/replace, Markdown conversion, and wordcloud generation.
  - **Video**: Frame/audio extraction, joining, conversion with GPU acceleration toggles.
  - **Archive**: ZIP compress/extract.
  - **PDF Tools**: Merge/split PDFs.
  - **File Organizer**: Move/copy/rename/delete and duplicate detection.
  - **HTML→PDF Converter**: Crawl docs sites and merge rendered PDFs via headless Chrome.

## Completeness Review
- **Core shell (agents/UI)**: Instantiates agents headlessly or with UI, wires plugin tabs, handles search, progress, logs, stats, and graceful shutdown logic. All exercised by unit tests for agent wiring and queue handling.
- **Tasking & diagnostics**: Thread tracking and task manager lifecycle covered by tests; diagnostic timers/counters available for metrics.
- **Config storage**: YAML config read/write validated in tests; uses per-user config path to avoid repo pollution.
- **Processing plugins**: Each processor/plugin has unit coverage for primary behaviors (audio, image, text, pdf, video, archive, organizer helpers). Skipped items are display-only interactions requiring a GUI environment, not logic gaps.
- **Error surfacing**: UIAgent routes errors to dialogs/toasts; tray/hotkey agents provide fallbacks in headless mode.
- **Dependencies**: PyPI requirements enumerate plugin needs; missing wheels were installed in the environment to satisfy current suite.

## Identified Gaps or Risk Areas
- **Optional GUI-only flows**: A few plugin UI actions are skipped in headless CI; functional logic is present but requires display for manual verification.
- **Dependency heaviness**: Some plugins (e.g., audio separation) rely on large ML stacks; consider lazy/optional installation messaging for lean deployments.
- **Runtime safeguards**: While shutdown joins registered threads, long-running plugin tasks should continue to use cancellation/timeouts and bounded queues to prevent resource leaks.

## Resolutions Implemented
- Installed runtime libraries (`pyyaml`, `Pillow`, `PyPDF2`, `markdown`) to align environment with declared requirements and allow the full test matrix to pass locally.
- Hardened YAML config handling with validation, atomic writes, and default overlays to prevent corruption and ensure safe fallbacks.
- Added lightweight dependency health checks for surfacing missing required packages at startup and for diagnostics dashboards.
- Verified all automated tests (unit + integration stub) complete successfully; GUI-only scenarios remain intentionally skipped when a display is unavailable.

## Proposed Optimized UI/UX Layout
- **Global shell**: Keep a persistent left-side navigation tree with category headers and typeahead search. Top bar houses quick actions (New Task, Recent Presets, Help) and status indicators (active tasks, network/storage health).
- **Workspace tabs**: Each plugin renders inside a unified workspace region with consistent header (title, version, author), contextual tips, and a collapsible summary pane (inputs, outputs, preset used, ETA).
- **Command palette**: Add `Ctrl+P` palette for cross-plugin actions (convert, organize, search) and preset execution with fuzzy matching.
- **Activity center**: Bottom drawer showing queued/running/completed tasks with retry/cancel buttons, log links, and performance stats (duration, throughput, error count).
- **Notifications**: Toasts for success/failure plus optional tray alerts; errors link to detailed logs and remediation hints.
- **Onboarding & safety**: First-run checklist for dependency checks (FFmpeg, Chrome, CUDA) and sandboxed file operations with dry-run toggles and overwrite confirmations.

## Workflow Recommendations
- **Media processing**: Drag files/folders into workspace → choose preset → review summary pane → run with live throughput metrics and pause/resume.
- **Batch organization**: Use organizer tab with dry-run preview, duplicate report, and commit/rollback buttons surfaced in the activity center.
- **Document utilities**: Provide recipe buttons (e.g., "Merge PDFs", "Crawl docs to PDF") that pre-fill forms, expose required dependencies, and stream progress updates.
- **Power-user layer**: Expose JSON/YAML preset editor with schema validation and import/export, plus CLI parity for automation.

## Performance & Scalability Notes
- **Current posture**: CPU-bound tasks run in the shared thread pool; heavy ML/video work should remain offloaded to worker processes or GPU-accelerated libs. UI queue polling is O(n) on queued events; ensure producers remain bounded.
- **Scaling guidance**: Favor horizontal scaling by splitting plugins into separate worker processes (per task type) communicating via IPC/queues; vertically scale by allocating GPU and high I/O throughput for audio/video plugins. Stream I/O (chunked reads/writes) for large files to minimize memory footprint.

## Next Steps
- Add explicit cancellation/timeouts in long-running plugin operations and surface progress checkpoints in the activity center.
- Introduce dependency health checks at startup with remediation links and optional lazy installation prompts.
- Expand e2e coverage to include GUI interactions via an integration harness (headless Tk or screenshot-based) to validate navigation and toast/error flows.
