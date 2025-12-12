# Setup Guide - Multi-Node Parallel File Server

## Quick Start (Python Server - No Compilation Required)

If you don't have a C++ compiler installed, you can use the Python-based server:

### 1. Install Python
Download and install Python 3.7+ from [python.org](https://www.python.org/downloads/)

### 2. Install Dependencies
```bash
pip install PyQt5
```

### 3. Run the Server
```bash
python server/server.py
```

### 4. Run the Client
```bash
python client/gui_client.py
```

## Full Setup (C++ Server with OpenMP)

### Option 1: Install MinGW-w64 (Windows)

1. Download MinGW-w64 from: https://www.mingw-w64.org/downloads/
2. Or use MSYS2: https://www.msys2.org/
   ```bash
   pacman -S mingw-w64-x86_64-gcc
   pacman -S mingw-w64-x86_64-openmp
   ```

3. Add to PATH: `C:\msys64\mingw64\bin`

4. Build the server:
   ```bash
   cd server
   g++ -std=c++17 -fopenmp -o server.exe main.cpp -lws2_32
   ```

### Option 2: Install Visual Studio (Windows)

1. Install Visual Studio Community (free)
2. Install "Desktop development with C++" workload
3. Open Developer Command Prompt
4. Build:
   ```bash
   cd server
   cl /EHsc /openmp main.cpp /link ws2_32.lib
   ```

### Option 3: Use WSL (Windows Subsystem for Linux)

1. Install WSL: `wsl --install`
2. Install build tools:
   ```bash
   sudo apt update
   sudo apt install build-essential libgomp-dev
   ```
3. Build:
   ```bash
   cd server
   make
   ```

## Verify Installation

### Check Python
```bash
python --version
# Should show Python 3.7 or higher
```

### Check C++ Compiler (if using C++ server)
```bash
g++ --version
# Should show GCC version
```

### Check PyQt5
```bash
python -c "import PyQt5; print('PyQt5 installed')"
```

## Running the Project

### Method 1: Python Server (Easiest)
```bash
# Terminal 1 - Start server
python server/server.py

# Terminal 2 - Start client
python client/gui_client.py
```

### Method 2: C++ Server
```bash
# Terminal 1 - Build and start server
cd server
g++ -std=c++17 -fopenmp -o server.exe main.cpp -lws2_32
server.exe 8080 ../server_files

# Terminal 2 - Start client
python client/gui_client.py
```

## Troubleshooting

### "Python not found"
- Install Python from python.org
- Make sure "Add Python to PATH" is checked during installation
- Restart terminal after installation

### "g++ not found"
- Install MinGW-w64 or use Python server instead
- Or use Visual Studio with Developer Command Prompt

### "PyQt5 not found"
```bash
pip install PyQt5
```

### "OpenMP not found" (C++ server)
- Install libgomp (Linux) or use MinGW with OpenMP support
- Or use Python server which doesn't require OpenMP

### Port already in use
- Change port in server: `python server/server.py 9000`
- Update client to connect to port 9000

## Recommended Setup for Windows

1. **Install Python 3.9+** (for client GUI)
2. **Use Python server** (no compilation needed):
   ```bash
   python server/server.py
   ```
3. **Install PyQt5**:
   ```bash
   pip install PyQt5
   ```
4. **Run client**:
   ```bash
   python client/gui_client.py
   ```

This setup requires no C++ compiler and works immediately!

