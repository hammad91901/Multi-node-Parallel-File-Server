#!/bin/bash
echo "Building Parallel File Server..."
cd server
g++ -std=c++17 -fopenmp -o server main.cpp -lpthread
if [ $? -eq 0 ]; then
    echo "Build successful!"
    echo "Server executable: server/server"
else
    echo "Build failed!"
    exit 1
fi

