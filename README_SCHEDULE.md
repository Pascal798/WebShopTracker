# WebShopTracker — Build & Scheduled Task (Windows)

Kurzanleitung, um den Bot als Windows Scheduled Task laufen zu lassen.

1) Build EXE
- Öffne eine administrative Eingabeaufforderung in diesem Projekt-Ordner.
- Führe `build_exe.bat` aus:

```
build_exe.bat
```

Nach dem Build liegt die Anwendung in `dist\bot\bot.exe`. Die Dateien `shops_config.json`, `products.json` und (falls vorhanden) `.env` werden automatisch kopiert.

2) Testlauf
- Starte `run_bot.bat` lokal, um sicherzustellen, dass `bot.exe` wie erwartet läuft:

```
run_bot.bat
```

3) Scheduled Task erstellen (PowerShell als Administrator)
- Beispiel: Task jeden Tag um 09:00 ausführen und in Arbeitsverzeichnis `C:\path\to\project\dist\bot` starten.

PowerShell-/CMD-Beispiel (ersetze Pfade entsprechend):

```
schtasks /Create /SC DAILY /TN "WebShopTrackerBot" /TR "C:\Users\%USERNAME%\Projects\WebShopTracker\run_bot.bat" /ST 09:00 /F
```

Oder mit PowerShell (vollständiger Task mit Arbeitsverzeichnis):

```
$action = New-ScheduledTaskAction -Execute "C:\Windows\System32\cmd.exe" -Argument "/c start /d \"C:\Users\SPA\Projects\WebShopTracker\dist\bot\" bot.exe"
$trigger = New-ScheduledTaskTrigger -Daily -At 9am
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "WebShopTrackerBot" -Description "Starts the WebShopTracker bot" -User "$env:USERNAME" -RunLevel Highest
```

Hinweise:
- Stelle sicher, dass `dist\bot` alle benötigten Dateien enthält (bes. `.env` mit `GMAIL_ADDRESS` und `GMAIL_PASSWORD`, falls Emails gebraucht werden).
- Playwright benötigt, dass die Browser-Installationen vorhanden sind (das `build_exe.bat` führt `python -m playwright install chromium` aus).
- Wenn der Scheduled Task keine GUI-Interaktion benötigt, kann `start` weggelassen werden und `bot.exe` direkt ausgeführt werden.
