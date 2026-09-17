# SURF-ETDS measurement data

Raw measurement data of the **SURF Test Unit**, a three-degree-of-freedom motion phantom with
two heated pads, recorded together with the tracking exports of **ExacTrac Dynamic Surface**
(ETDS) at the linear accelerators of Tirol Kliniken, Innsbruck.

This repository is the single home of the raw data. The code that uses it lives elsewhere:

| Repository | Content |
|---|---|
| [`surf-etds-phantom`](https://github.com/AG-Kollotzek/surf-etds-phantom) | Firmware, measurement terminal and hardware of the phantom; the [data dictionary](https://github.com/AG-Kollotzek/surf-etds-phantom/blob/main/docs/data-dictionary.md) describes the telemetry and protocol formats |
| [`surf-etds-analysis`](https://github.com/AG-Kollotzek/surf-etds-analysis) | Characterisation and validation of the tracking accuracy (campaign `2026-03-10_L4`) |
| [`surf-etds-qa`](https://github.com/AG-Kollotzek/surf-etds-qa) | Yearly quality assurance across linacs and report generation |

Both code repositories include this repository as a git submodule at a fixed tag.

## Layout

```
campaigns/<YYYY-MM-DD>_<Linac>/
  phantom/      telemetry CSV, sphere-detection *_QA.csv, measurement protocol logs *_log.json / *_log.txt
  etd/          ExacTrac exports TrackingResult_<date>_<time>.json and the matching .png
  xray/         stereotactic kV (ExacTrac X-ray) readouts, where they were taken
  protocol.md   transcription of the measurement protocol, where one was written
  runs.csv      one row per run: which files belong together and how they were used
  SHA256SUMS    checksums of every file in the campaign folder
tools/          validation and preparation scripts (MIT)
```

A campaign is one measurement day on one linac. `<Linac>` is `L<n>` where the linac is
documented, `LX` for test runs without a linac and `unknown` where nothing documents it. The
`linac` field of a terminal protocol is kept as entered: in `2026-08-06_LX`, a run without motion
controller before the linac 3 and 4 measurements, it reads `5`, which is not a linac.
The ID of a published campaign never changes.

## Campaigns

| Campaign | Telemetry CSV | Sphere detection | Protocol logs | ExacTrac exports | Evaluated runs | Also |
|---|--:|--:|--:|--:|--:|---|
| `2025-12-04_unknown` | 5 | 0 | 0 | 0 | 0 | |
| `2026-01-26_unknown` | 7 | 0 | 0 | 0 | 0 | |
| `2026-02-10_unknown` | 3 | 0 | 0 | 0 | 0 | |
| `2026-02-16_unknown` | 1 | 0 | 0 | 0 | 0 | |
| `2026-02-17_unknown` | 7 | 0 | 0 | 0 | 0 | |
| `2026-02-19_L3` | 4 | 0 | 0 | 0 | 0 | |
| `2026-02-24_unknown` | 11 | 0 | 0 | 0 | 0 | |
| `2026-03-10_L4` | 40 | 0 | 0 | 38 | 32 | `protocol.md`, `xray/` |
| `2026-03-25_unknown` | 10 | 0 | 0 | 0 | 0 | |
| `2026-04-08_unknown` | 22 | 0 | 0 | 0 | 0 | |
| `2026-05-12_unknown` | 0 | 1 | 0 | 0 | 0 | |
| `2026-05-13_unknown` | 4 | 4 | 0 | 0 | 0 | |
| `2026-07-15_L1` | 8 | 8 | 0 | 8 | 8 | |
| `2026-07-29_L0` | 2 | 2 | 0 | 5 | 4 | `protocol.md` |
| `2026-08-06_L3` | 2 | 2 | 3 | 4 | 4 | `protocol.md` |
| `2026-08-06_L4` | 2 | 2 | 3 | 5 | 4 | `protocol.md` |
| `2026-08-06_LX` | 1 | 1 | 1 | 0 | 0 | |
| `2026-08-21_LX` | 1 | 1 | 1 | 0 | 0 | |

Campaigns up to `2026-05-13` are pilot and development measurements without tracking exports.
`2026-03-10_L4` is the campaign evaluated for the paper. `2026-07-15_L1`, `2026-07-29_L0`,
`2026-08-06_L3` and `2026-08-06_L4` are the initial measurements of the yearly QA.

## File formats

**Telemetry, sphere detection and protocol logs** (`phantom/`) are written by the measurement
terminal of `surf-etds-phantom` and described in its
[data dictionary](https://github.com/AG-Kollotzek/surf-etds-phantom/blob/main/docs/data-dictionary.md).
They are stored unchanged.

**ExacTrac exports** (`etd/`) are the JSON exports of the tracking system and the image it
writes with each export, unchanged except for the first field (see Pseudonymisation).

**`runs.csv`** links the files of a campaign. Columns:

| Column | Meaning |
|---|---|
| `run_id` | For `2026-03-10_L4` the run number of the evaluation in `surf-etds-analysis`; for the QA campaigns the configuration entry of `surf-etds-qa`; empty for runs that are not evaluated |
| `csv_file` | Telemetry CSV in `phantom/` (a `*_QA.csv` only when it has no telemetry CSV) |
| `etd_file` | ExacTrac export in `etd/` |
| `group` | Motion group of the paper evaluation, or `single angle` / `multi angle` for the QA |
| `roi_area` | Region of interest drawn in the tracking system (paper campaign; spelling as recorded) |
| `heatingpads` | `OFF` or the pad temperature in °C |
| `title` | Plot title (paper campaign) or deflection and couch angle (QA) |
| `used_in_analysis` | `true` if `surf-etds-analysis` or `surf-etds-qa` evaluates the run |
| `note` | Why a file is not evaluated, detected signatures (for example the values the terminal writes without a controller), links to protocol logs |
| `blueprint` | Motion blueprint of `surf-etds-phantom`, where documented |
| `protocol_remark` | What the measurement protocol says about the run, in English; remarks in brackets are additions |

In `2026-03-10_L4`, lines 1–41 of `runs.csv` are the run index published with
`surf-etds-phantom` and are kept unchanged; the rows after line 41 list the ExacTrac exports
that the evaluation does not use.

**`protocol.md`** transcribes the measurement protocol word by word in its original German,
with role codes instead of names. Page numbers and organisational to-dos are not transcribed.

**`xray/exactrac_kv_readouts.csv`** (`2026-03-10_L4`) holds the ExacTrac X-ray readouts of the
static extreme positions (protocol run 13), in protocol order. Columns: `point`, `block`,
`axis` (`h`, `v`, `r`), `setpoint`, `unit`, `lateral_mm`, `longitudinal_mm`, `vertical_mm`,
and `xray_verification_point_id`, the point number used by `xray_verification_v2.py` in
`surf-etds-analysis`, which lists the final zero reading of the rotation block first.

**`SHA256SUMS`** follows the GNU `sha256sum` format, sorted by path. Check a campaign with
`sha256sum -c SHA256SUMS` (`shasum -a 256 -c SHA256SUMS` on macOS) inside its folder.

## Pseudonymisation

- **Operators** appear only as role codes: `QMP<n>` for a Qualified Medical Physicist,
  `Student<n>` for students (including PhD students, student assistants and interns);
  `RTT<n>` is reserved. The mapping to people is kept privately by the lab and is not published.
- **Workstation names:** the first field of every ExacTrac export, `computerName`, named the
  tracking workstation. It is replaced by `ETD-L<n>`, where `<n>` is the linac of the campaign;
  no other byte of the export changes.
- **Protocols** are published as transcriptions with role codes; the signed originals are not
  published. No photos are included.
- `tools/validate.py` rejects operator names, e-mail addresses, home and cloud paths, host
  names and the earlier operator codes; `tools/check_names.py` checks against the lab's private
  list of people before anything is pushed.

## Provenance

The dataset was assembled from the raw data of the phantom repository (`surf-etds-phantom` at
commit `eaff20a`, `data/raw/`), of the analysis repository and of the QA repository. Files that
occurred in more than one repository were merged when byte-identical; where the QA repository
held protocol logs with first names, the phantom copies with role codes were kept. Every file
was checked to be re-derivable from its source.

## Checking the data

```bash
python tools/validate.py
python -m unittest discover -s tools/tests -t tools
```

Both run in CI on every push and pull request. The tools use only the Python standard library
(Python 3.9 or later).

## Contributing

New campaigns come as pull requests; the steps from the measurement laptop to the pull request
are in [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Citing

See [`CITATION.cff`](CITATION.cff), or use GitHub's "Cite this repository".

## Licence

- **CC-BY-4.0** — the measurement data in `campaigns/` and the documentation ([`LICENSE`](LICENSE)).
- **MIT** — the scripts in `tools/` ([`LICENSES/MIT.txt`](LICENSES/MIT.txt)).

"ExacTrac" and "Brainlab" are trademarks of Brainlab AG and are used nominatively. Brainlab does
not endorse and is not affiliated with this work. The data come from quality-assurance and
research measurements with a phantom; they contain no patient data and are not intended for
clinical decisions.
