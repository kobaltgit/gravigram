@echo off
echo Stopping Antigravity Bot...
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*antigravity_bot*run.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force; Write-Host ('Killed PID ' + $_.ProcessId) }"
echo Done.
