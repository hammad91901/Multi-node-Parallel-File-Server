#!/bin/bash
echo "Starting Parallel File Server..."
cd server
if [ -f "./server" ]; then
    ./server 8080 ../server_files
else
    echo "Server executable not found. Please build the server first."
    echo "Run: cd server && make"
fi

