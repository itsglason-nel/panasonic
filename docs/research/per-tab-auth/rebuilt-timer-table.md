# rebuilt-timer-table.md
```
app\static\js\app.js:9 -> setTimeout(function() {
app\static\js\app.js:12 -> setTimeout(function() { alert.remove(); }, 300);
app\static\js\app.js:58 -> setTimeout(function() {
app\static\js\app.js:60 -> setTimeout(function() { overlay.remove(); }, 300);
app\templates\admin\components\scripts.html:100 -> setTimeout(() => {
app\templates\admin\components\scripts.html:128 -> confirmInterval = setInterval(() => {
app\templates\admin\components\scripts.html:362 -> workSchedRefreshTimer = setInterval(() => {
app\templates\admin\components\scripts.html:1099 -> setTimeout(() => openModuleScheduleModal(), 300);
app\templates\admin\components\scripts.html:2261 -> toast._hideTimer = setTimeout(() => {
app\templates\admin\components\scripts.html:3582 -> setTimeout(() => window.location.href = d.redirect, 1500);
app\templates\admin\components\scripts.html:5522 -> window.qcFilterTimer = setTimeout(() => {
app\templates\admin\components\scripts.html:5860 -> scoreboardRefreshTimer = setInterval(() => {
app\templates\scoreboard\all_lines.html:184 -> setInterval(updateScoreboard, 10000);
app\templates\scoreboard\line.html:343 -> setInterval(() => {
app\templates\scoreboard\line.html:491 -> setInterval(renderProduction, 1000);
app\templates\scoreboard\line.html:502 -> setInterval(fetchProdData, 30000);
app\templates\scoreboard\line.html:503 -> setInterval(fetchLogsData, 30000);
```
ANALYST NOTES (INFERRED):
- Repeated schedules calls are triggered by `workSchedRefreshTimer` and other UI event handlers overlapping.
