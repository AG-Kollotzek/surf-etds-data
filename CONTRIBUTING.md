# Contributing a campaign

A campaign is added as a pull request. The steps below go from the measurement laptop to a
green pull request. Documentation is in English; protocol transcriptions stay in the German
of the original protocol.

## Before the measurement

1. On the measurement laptop, clone [`surf-etds-phantom`](https://github.com/AG-Kollotzek/surf-etds-phantom)
   and start the measurement terminal as described in its `CONTRIBUTING.md`.
2. Place the lab's private list of people as `software/people.local.json` in that clone (it is
   git-ignored there). The terminal then offers the names for selection and writes **role codes**
   (`Lead1`, `QMP2`, `Student2`, ...) into the protocol logs. Never type names into the free-text fields.

## After the measurement

3. Clone this repository and create the campaign folder `campaigns/<YYYY-MM-DD>_<Linac>/`, for
   example `campaigns/2026-10-05_L2/` (`LX` for a test run without a linac).
4. Copy the files, unchanged:
   - `phantom/`: the telemetry CSV, the `*_QA.csv` and the `*_log.json` / `*_log.txt` of every run;
   - `etd/`: every `TrackingResult_<date>_<time>.json` export and its `.png`;
   - `xray/`: readouts of the ExacTrac X-ray system, if any were taken, as CSV.
5. Write `runs.csv` (columns in the [README](README.md#file-formats)): one row per run, linking
   telemetry and export, and a `note` for every file that is not a regular run.
6. If a protocol was written, transcribe it into `protocol.md`: word by word, with role codes
   instead of names, without organisational to-dos. The signed original stays with the lab.
7. Prepare the folder. This converts line endings, sets the workstation name of the exports to
   `ETD-L<n>` and writes `SHA256SUMS`:

   ```bash
   python tools/prepare_campaign.py campaigns/2026-10-05_L2
   ```

8. Validate and check for names. Keep the list of people **outside** this repository:

   ```bash
   python tools/validate.py
   python tools/check_names.py /path/outside/this/repository/people.json campaigns/2026-10-05_L2
   ```

   Both must end without findings. `check_names.py` prints findings masked; fix the files, then run
   `prepare_campaign.py` again so that `SHA256SUMS` matches.

## Pull request

9. Commit on a branch with your GitHub no-reply address as commit e-mail, push and open a pull
   request. Describe the campaign in one or two sentences (linac, purpose, anything unusual).
10. The `validate` workflow must be green before a maintainer merges.

## Rules

- No names, e-mail addresses, photos, home paths or workstation names anywhere in `campaigns/`.
- A published campaign ID is never renamed, and published files are not rewritten. If a
  correction is unavoidable, explain it in the pull request and in the `note` column of `runs.csv`.
- No file larger than 50 MB.
- Plans, to-dos and open questions do not belong in this repository or its issues.
