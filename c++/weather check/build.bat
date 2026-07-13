@echo off
REM Weather App - Build Script
echo building... please wait seconds

REM Step 1: Generate icon file
echo [1/4] Generating icon...
g++ -o make_icon.exe make_icon.cpp -std=c++17
if %ERRORLEVEL% NEQ 0 (
    echo make_icon build failed.
    pause
    exit /b 1
)
make_icon.exe

REM Step 2: Compile resource (COFF format for MinGW linker)
echo [2/4] Compiling resource...
windres weather.rc -O coff -o weather.o

REM Step 3: Build CLI version
echo [3/4] Building weather.exe...
g++ -static -Os -s -o weather.exe weather.cpp weather.o -std=c++17

REM Step 4: Build GUI version
echo [4/4] Building weather_gui.exe...
g++ -static -Os -s -o weather_gui.exe weather_gui.cpp weather.o -std=c++17 -mwindows

REM Clean up build artifacts
echo [*] Cleaning up...
if exist make_icon.exe del make_icon.exe

if %ERRORLEVEL% EQU 0 (
    echo Build successful! Custom icon applied.
) else (
    echo Build failed.
)
pause
