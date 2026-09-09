@echo off
rem BATCH 2 - 7-day telemetry availability (add --extract to dump row CSVs).
rem Reads data\manifests\fault_candidates_2025_2026.csv from BATCH 1.
rem For the 2024 fallback instead: replace --input ... with --fallback30
cd /d "C:\Users\CRIS\Desktop\ayush\rms-bearing"
"C:\Users\CRIS\Desktop\ayush\rms-bearing\rms\Scripts\python.exe" scripts\batch_extract_7day_telemetry.py --input data\manifests\fault_candidates_2025_2026.csv
pause
