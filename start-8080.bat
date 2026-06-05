@echo off
cd /d "%~dp0"
title Sluzhebnyk - local server (port 8080)
echo.
echo   GOLOSOVYI SLUZHEBNYK
echo   ====================
echo.
echo   Starting local server on http://localhost:8080
echo   (port 8080 - to avoid conflict with other projects on 8000)
echo   Browser will open in a moment.
echo.
echo   Keep THIS window open while you use the app.
echo   Close it to stop the server.
echo.
start "" http://localhost:8080
py -m http.server 8080
