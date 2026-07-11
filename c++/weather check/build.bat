@echo off
REM Space Shooter - Build Script
echo building... please wait seconds
g++ -static -Os -s -o weather.exe weather.cpp -std=c++17
g++ -static -Os -s -o weather_gui.exe weather_gui.cpp -std=c++17 -mwindows
if %ERRORLEVEL% EQU 0 (
    echo Build successful! Run bin file to play.
) else (
    echo Build failed.
)
pause



