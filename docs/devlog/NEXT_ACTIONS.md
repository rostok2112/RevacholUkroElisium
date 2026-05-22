# Next Actions

After the local metadata probe smoke helper:

1. Prepare the local Steam-installed game without launching it:

   ```powershell
   python scripts/run_bepinex_metadata_probe_local_smoke.py --auto-discover --enable-probe
   ```

2. Manually launch the game, wait for BepInEx startup, then close the game.
3. Check only allowlisted metadata markers from `BepInEx/LogOutput.log` and write the redacted
   workspace report:

   ```powershell
   python scripts/run_bepinex_metadata_probe_local_smoke.py --auto-discover --check-log --write-report
   ```

4. Validate and review the redacted report:

   ```powershell
   python scripts/check_bepinex_metadata_probe_report.py `
     --report workspace/synthetic-slice/bepinex-bridge/metadata-probe/report.json `
     --quiet

   python scripts/review_bepinex_metadata_probe_report.py `
     --report workspace/synthetic-slice/bepinex-bridge/metadata-probe/report.json `
     --quiet
   ```

5. Disable the probe flags again:

   ```powershell
   python scripts/run_bepinex_metadata_probe_local_smoke.py --auto-discover --disable-probe
   ```

6. Keep raw BepInEx logs, game logs, private paths, screenshots, payload dumps, and completed real
   reports out of git. Share only the redacted helper/reviewer summaries when debugging setup.

Exact resume prompt after the real local smoke:

`Continue in revachol-ukro-elisium after the local metadata probe smoke helper was used against the Steam install. First inspect git status, read AGENTS.md, docs/devlog/*.md, docs/manual-smoke/bepinex-metadata-probe-smoke.md, scripts/run_bepinex_metadata_probe_local_smoke.py, scripts/check_bepinex_metadata_probe_report.py, scripts/review_bepinex_metadata_probe_report.py, and if present validate workspace/synthetic-slice/bepinex-bridge/metadata-probe/report.json without printing raw logs. Analyze the redacted local smoke result and fix only setup/build/install/config/log-contract issues needed for the metadata probe startup smoke. Do not commit raw logs, BepInEx logs, screenshots, real reports, private paths, game files, real text, hooks, Unity scanning, OCR, extraction, provider execution, companion HTTP contract changes, downloads, or new dependencies.`
