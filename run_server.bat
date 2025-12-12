@echo off
echo Starting Parallel File Server...
cd server
if exist server.exe (
    server.exe 8080 ..\server_files
) else (
    echo Server executable not found. Please build the server first.
    echo Run: cd server && make
    pause
)

