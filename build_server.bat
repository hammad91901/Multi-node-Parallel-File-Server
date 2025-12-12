@echo off
echo Building Parallel File Server...
cd server
g++ -std=c++17 -fopenmp -o server.exe main.cpp -lws2_32
if %ERRORLEVEL% EQU 0 (
    echo Build successful!
    echo Server executable: server\server.exe
) else (
    echo Build failed!
    pause
)

