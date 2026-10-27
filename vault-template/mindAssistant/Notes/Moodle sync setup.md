# Moodle sync setup

A macOS background job downloads new Moodle files into each module's `Materials/` folder at 07:30 and 18:00, copies new PDFs to iCloud Drive › `To GoodNotes`, and logs each run in [[Moodle downloads]]. Code and setup: `moodle-sync/` in the repository.

- Script and settings: `~/moodle-sync/` · access token: `~/.config/moodle-sync/token` (never in the vault).
- Course mapping: `config.json` maps Moodle course ids to module folders.
- Pause: `launchctl bootout gui/$(id -u)/local.moodle-sync`

Related: [[State]] · [[Modules overview]]
