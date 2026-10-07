$action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "`"D:\Projects\active\antigravity_bot\start_hidden.vbs`"" -WorkingDirectory "D:\Projects\active\antigravity_bot"
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero)
Register-ScheduledTask -TaskName "AntigravityBot" -Action $action -Trigger $trigger -Settings $settings -Force
