@echo off
rem BATCH 1 - mine 2025/2026 bearing-like faults, day by day (resumable).
rem Full range takes many hours - leave running overnight on CRIS intranet.
cd /d "C:\Users\CRIS\Desktop\ayush\rms-bearing"
"C:\Users\CRIS\Desktop\ayush\rms-bearing\rms\Scripts\python.exe" scripts\batch_mine_faults_2025_2026.py --from 2025-01-01 --to 2026-09-09
pause
