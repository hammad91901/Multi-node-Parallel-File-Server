# Multi-Node Parallel File Server

A high-performance parallel file server implementation demonstrating socket programming, multithreading, and OpenMP parallelism. Features a modern, classy GUI client for file management.

## 🚀 Features

### Core Features
- **Parallel Processing**: Uses multiprocessing for parallel file operations
- **Multi-threading**: Handles multiple clients simultaneously using thread pools
- **Socket Programming**: TCP/IP socket-based communication
- **Modern GUI**: Beautiful PyQt5-based client interface
- **Cross-platform**: Works on Windows, Linux, and macOS

### Enhanced Features (NEW!)
- **File Upload**: Upload files from client to server
- **Directory Browsing**: Navigate server directories with tree view
- **File Search**: Search files by name or content (parallel search)
- **File Metadata**: View file size, dates, and MD5 checksums
- **Compression**: Optional gzip compression for transfers
- **Server Statistics**: Real-time server performance metrics
- **Multi-Node Support**: Run multiple servers with load balancing
- **Monitoring Dashboard**: Real-time monitoring of all nodes
- **Enhanced GUI**: Tabbed interface with advanced features

## 📋 Prerequisites

### Server (C++)
- C++17 compatible compiler (GCC, Clang, or MSVC)
- OpenMP support
- CMake 3.10+ (optional, for CMake build)

### Client (Python)
- Python 3.7+
- PyQt5

## 🛠️ Installation

### Server Setup

#### Using CMake (Recommended)
```bash
cd server
mkdir build
cd build
cmake ..
cmake --build .
```

#### Using Makefile
```bash
cd server
make
```

#### Windows (MinGW/MSVC)
```bash
cd server
g++ -std=c++17 -fopenmp -o server.exe main.cpp -lws2_32
```

### Client Setup
```bash
pip install -r requirements.txt
```

## 🎯 Usage

### Starting the Server

#### Basic Server
```bash
# Python server (recommended)
python server/server.py 8080 server_files

# Enhanced server with all features
python server/enhanced_server.py --port 8080 --node-id node1
```

#### Multi-Node Setup
```bash
# Start multiple nodes
python server/enhanced_server.py --port 8080 --node-id node1
python server/enhanced_server.py --port 8081 --node-id node2
python server/enhanced_server.py --port 8082 --node-id node3

# Start load balancer
python server/load_balancer.py --port 8000
```

Or use the helper script:
```bash
start_multi_node.bat  # Windows
```

The server will:
- Create the specified directory if it doesn't exist
- Listen for client connections
- Process file requests in parallel using multiprocessing
- Handle multiple clients simultaneously using threads
- Track statistics and provide metadata

### Starting the Client

#### Enhanced GUI Client (Recommended)
```bash
python client/enhanced_gui_client.py
```

Or use the helper script:
```bash
run_enhanced_client.bat  # Windows
```

#### Basic GUI Client
```bash
python client/gui_client.py
```

#### CLI Client (For Testing/Automation)
```bash
python client/cli_client.py --host localhost --port 8080 --list
python client/cli_client.py --host localhost --port 8080 --download sample1.txt
```

### Client Features

**Enhanced GUI Client:**
1. **File Browser Tab**: Navigate directories, view files with metadata
2. **Search Tab**: Search files by name or content
3. **Statistics Tab**: View server performance metrics
4. **Upload Files**: Upload files to server with progress
5. **Download Files**: Download with optional compression
6. **File Metadata**: View file details, checksums, dates
7. **Directory Navigation**: Browse server directory structure
8. **Activity Log**: Real-time operation logging

**Basic GUI Client:**
- Connect to server
- List and download files
- Progress tracking
- Activity logging

**CLI Client:**
- List available files
- Download files with progress
- Interactive or command-line mode
- Suitable for automation

## 📁 Project Structure

```
Multi-node Parallel File Server/
├── server/
│   ├── main.cpp          # Server implementation
│   ├── CMakeLists.txt    # CMake build configuration
│   └── Makefile          # Make build configuration
├── client/
│   ├── gui_client.py     # GUI client application
│   └── cli_client.py     # Command-line client
├── server_files/         # Default server file directory
│   ├── sample1.txt       # Sample test file
│   └── sample2.txt       # Sample test file
├── requirements.txt      # Python dependencies
├── build_server.bat      # Windows build script
├── build_server.sh       # Linux/Mac build script
├── run_server.bat        # Windows run script
├── run_server.sh         # Linux/Mac run script
├── run_client.bat        # Windows client script
├── run_client.sh         # Linux/Mac client script
└── README.md            # This file
```

## 🔧 Technical Details

### Server Architecture

- **Socket Layer**: TCP/IP sockets for network communication
- **Threading Model**: One thread per client connection
- **Parallel Processing**: OpenMP tasks for file chunk processing
- **Thread Safety**: Mutex-protected logging

### Client Architecture

- **GUI Framework**: PyQt5 with modern styling
- **Network Layer**: Socket-based TCP communication
- **Threading**: Separate thread for file transfers to keep UI responsive
- **Progress Tracking**: Real-time download progress updates

## 🎨 GUI Features

- **Modern Design**: Gradient backgrounds, rounded corners, smooth animations
- **Real-time Updates**: Live activity log and progress bars
- **User-friendly**: Intuitive interface with clear visual feedback
- **Responsive**: Non-blocking operations with threaded file transfers

## 📊 Performance

- Supports multiple concurrent client connections
- Parallel file processing using OpenMP
- Efficient chunk-based file transfer (8KB chunks)
- Optimized for high-throughput scenarios

## 🧪 Testing

### Quick Test

1. **Build the server:**
   ```bash
   # Windows
   build_server.bat
   
   # Linux/Mac
   chmod +x build_server.sh
   ./build_server.sh
   ```

2. **Start the server:**
   ```bash
   # Windows
   run_server.bat
   
   # Linux/Mac
   chmod +x run_server.sh
   ./run_server.sh
   ```

3. **Test with CLI client:**
   ```bash
   cd client
   python cli_client.py --list
   python cli_client.py --download sample1.txt
   ```

4. **Test with GUI client:**
   ```bash
   run_client.bat  # or run_client.sh
   ```
   - Connect to `localhost:8080`
   - Click "Refresh" to see files
   - Select a file and click "Download"

### Multiple Clients Test

Open multiple client instances (GUI or CLI) to test concurrent connections and parallel processing.

## 🔍 Concepts Demonstrated

1. **Socket Programming**: TCP/IP client-server communication
2. **Multithreading**: Concurrent client handling
3. **Parallel Computing**: Multiprocessing for parallel operations
4. **GUI Development**: Modern desktop application interface
5. **Network Protocols**: Custom JSON-based protocol
6. **Load Balancing**: Multi-node request distribution
7. **Distributed Systems**: Multi-node coordination
8. **File Processing**: Parallel checksums, search, compression
9. **Statistics & Monitoring**: Real-time system metrics
10. **Directory Management**: Hierarchical file navigation

## 🐛 Troubleshooting

### Server Issues
- **Port already in use**: Change the port number
- **Permission denied**: Check file/directory permissions
- **OpenMP not found**: Install OpenMP library for your compiler

### Client Issues
- **Connection refused**: Ensure server is running
- **PyQt5 not found**: Run `pip install PyQt5`
- **Import errors**: Verify Python version (3.7+)

## 📝 License

This project is for educational purposes, demonstrating parallel and distributed computing concepts.

## 👨‍💻 Author

Created for Parallel and Distributed Computing course project.

---

**Note**: This is a demonstration project. For production use, consider adding authentication, encryption, error recovery, and more robust error handling.

