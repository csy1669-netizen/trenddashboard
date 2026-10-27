@echo off
rem TREND DASHBOARD - 매일 15:00 data 폴더·페이지 변경분을 GitHub에 push
chcp 65001 >nul
cd /d "%~dp0.."
echo [%date% %time%] start >> scripts\push_log.txt
git pull --rebase --autostash >> scripts\push_log.txt 2>&1
git add data index.html README.md scripts\weekly_update.py scripts\push_weekly.bat
git diff --cached --quiet
if %errorlevel%==0 (
  echo [%date% %time%] 변경 없음 >> scripts\push_log.txt
  exit /b 0
)
git commit -m "daily data update %date%" >> scripts\push_log.txt 2>&1
git push >> scripts\push_log.txt 2>&1
echo [%date% %time%] push 완료 >> scripts\push_log.txt
