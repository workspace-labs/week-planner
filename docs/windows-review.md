# Windows review, 9 October 2026

Reviewed base commit `309679d` (0.4.1). Fixes are in 0.4.2. The owner authorized committing and pushing
the fixes and updated test-coverage documentation after the local review.

## Reproduced failures and fixes

| Finding | Reproduction | Correction |
| --- | --- | --- |
| Stale browser ticks | Tick a task, edit its title while keeping the plan title, dates and card count, regenerate the HTML. The new task starts done. Updated source review marks also lose to stale browser marks. | Scope stored marks to a digest of the source plan, including source review marks. Reopening an unchanged plan still preserves progress. |
| Missing HTML focus | Render a review with an unplanned carried-over item. Its JSON and PDF retain it, but the rendered HTML never shows it. Waiting and moving summaries are also absent. | Show waiting/carry summaries below the HTML board and update them as tasks are ticked. |
| Missing weekend details | Render a weekend goal with why, done-when and project. Only its short goal band is visible in HTML. | Show its answers, verdict and counted progress under the weekend board. |
| Destructive output alias | Export with `-o` pointing to the input JSON, or a hard link to it. The input is replaced. | Refuse with exit 2 before writing; the source bytes remain intact. |
| Windows UTF-8 BOM | Save valid JSON with Windows PowerShell's UTF-8 encoding. Both exports refuse its BOM. | Accept UTF-8 with or without BOM in plan and brand reads, including the HTML reread. |
| Output exceptions | Use an existing directory as the output filename. A Python traceback escapes. | Return a plain writable-output error, exit 2. |
| Inconsistent date rules | Python 3.11+ accepts compact and ISO-week dates that Python 3.9 refuses, despite the documented format. | Require the canonical `YYYY-MM-DD` spelling. |
| Zero-length buffer | Supply `1e-12` item hours. Quarter-hour tolerance rounds it to zero while counting it as a buffer. | Require at least 0.25 hours for every item before rounding. |
| Mobile title overflow | Use long unbroken title/goal words that pass PDF preflight. The phone page is 495 pixels wider than its viewport. | Wrap title, goal-band, goal-card and footer words within their containers; the same probe reports no horizontal overflow. |
| Windows test gaps | Chrome is installed but tests only look in macOS/Linux locations; their file URI is invalid on Windows. PDF previews require Bash. | Find Windows Chrome or `CHROME_BIN`, use `Path.as_uri()`, and run a portable Python preview command. |

Each functional finding has a regression that failed on the original source before correction. The
brand BOM change shares the plan-reader correction. No PDF drawing style or task-board state was changed.

## Verification

- Python 3.12.10, ReportLab 5.0.1, installed Chrome 143 and isolated portable Poppler 26.09.0.
- Command: `python -B -m unittest discover -s tests`, with current Poppler's `Library/bin` on `PATH`.
- 113 tests passed, zero failures and zero skips. Checks include real browser clicks, saved JSON,
  phone layout, PDF text/bounding boxes, source-file protection and the documented preview.
- Scripted week/review uses four supplied fixture tasks, a linked long carried-over title, an unplanned
  dentist item, confirmed goal answers, optional advice and a Wednesday buffer. It plans 4 hours of 10
  free, then scores 3 of 4 done, goal Close. The unfinished report and dentist move once; completed
  onboarding work stays gone.
- A weekend fixture contains exactly two supplied tasks, no forced personal item, 1.5 hours of 4 free,
  and a one-page PDF. The week plan and review each have three pages.
- JSON/PDF/HTML files were saved together in the user's `Desktop/plan` folder, labeled `TEST`; the
  existing real plan was unchanged. PDF previews were rendered in separate evaluation folders.

## Limits of this review

Scripted skill conversations and browser checks do not prove automatic skill discovery, native
Codex/Claude clickable questions, Claude ZIP upload, the chat-only flow where code cannot run, a live
Backloop board, an unscripted goal interview through the installed skill, Safari/Firefox behavior or
opening and saving a local file on a physical iPhone. The corrected release was tested on Windows;
macOS and Linux reruns remain outstanding.

Existing HTML files keep their own browser progress. For a newly generated file, save browser-only
progress to JSON first: changed source content intentionally starts with its own source marks.
