@echo off
cd /d "%~dp0"
title Sluzhebnyk - local server
echo.
echo   GOLOSOVYI SLUZHEBNYK
echo   ====================
echo.
echo   Starting local server on http://localhost:8000
echo   Browser will open in a moment.
echo.
echo   Keep THIS window open while you use the app.
echo   Close it to stop the server.
echo.
start "" http://localhost:8000
py -m http.server 8000
