@echo off
setlocal
cd /d "C:\Users\CRIS\Desktop\ayush\rms-bearing"
if not exist logs mkdir logs

echo [%date% %time%] Starting Batch 1 >> logs\nightly_batch_pipeline.log
"C:\Users\CRIS\Desktop\ayush\rms-bearing\rms\Scripts\python.exe" scripts\batch_mine_faults_2025_2026.py --from 2025-01-01 --to 2026-09-09 >> logs\nightly_batch_pipeline.log 2>&1
if errorlevel 1 (
  echo [%date% %time%] Batch 1 failed; Batch 2 not started >> logs\nightly_batch_pipeline.log
  exit /b 1
)

echo [%date% %time%] Batch 1 completed; starting Batch 2 >> logs\nightly_batch_pipeline.log
"C:\Users\CRIS\Desktop\ayush\rms-bearing\rms\Scripts\python.exe" scripts\batch_extract_7day_telemetry.py --input data\manifests\fault_candidates_2025_2026.csv >> logs\nightly_batch_pipeline.log 2>&1
if errorlevel 1 (
  echo [%date% %time%] Batch 2 failed >> logs\nightly_batch_pipeline.log
  exit /b 1
)

echo [%date% %time%] Batch 1 and Batch 2 completed >> logs\nightly_batch_pipeline.log
exit /b 0
