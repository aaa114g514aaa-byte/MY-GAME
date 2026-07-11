@echo off
REM Space Shooter - Build Script
g++ main.cpp -o SpaceShooter.exe -lgdi32 -lwinmm -static -O2 -mwindows
if %ERRORLEVEL% EQU 0 (
    echo Build successful! Run SpaceShooter.exe to play.
) else (
    echo Build failed.
)
pause



