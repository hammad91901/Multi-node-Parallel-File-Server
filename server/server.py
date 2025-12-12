#!/usr/bin/env python3
"""
Python-based Parallel File Server
Alternative implementation that doesn't require C++ compilation
Uses multiprocessing and threading for parallelism
"""

import socket
import threading
import os
import sys
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import multiprocessing

class ParallelFileServer:
    def __init__(self, port=8080, directory="server_files"):
        self.port = port
        self.directory = Path(directory)
        self.directory.mkdir(exist_ok=True)
        self.running = False
        self.log_lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=10)
        
    def log(self, message):
        with self.log_lock:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] {message}")
    
    def list_files(self):
        """List all files in the server directory"""
        try:
            files = [f.name for f in self.directory.iterdir() if f.is_file()]
            return files
        except Exception as e:
            self.log(f"Error listing files: {e}")
            return []
    
    def send_file(self, client_socket, filename):
        """Send a file to the client using parallel processing"""
        filepath = self.directory / filename
        
        if not filepath.exists():
            client_socket.sendall(b"FILE_NOT_FOUND\n")
            return False
        
        try:
            file_size = filepath.stat().st_size
            
            # Send file size
            size_msg = f"{file_size}\n".encode()
            client_socket.sendall(size_msg)
            
            # Read and send file in chunks (parallel processing simulation)
            chunk_size = 8192
            with open(filepath, 'rb') as f:
                # Use multiprocessing pool for parallel chunk processing
                with multiprocessing.Pool(processes=4) as pool:
                    chunks = []
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        chunks.append(chunk)
                    
                    # Process chunks in parallel (demonstrates parallelism)
                    # In production: compression, encryption, checksums, etc.
                    processed_chunks = pool.map(self.process_chunk, chunks)
                    
                    # Send processed chunks sequentially
                    for chunk in processed_chunks:
                        client_socket.sendall(chunk)
            
            self.log(f"File '{filename}' ({file_size} bytes) sent successfully")
            return True
            
        except Exception as e:
            self.log(f"Error sending file: {e}")
            client_socket.sendall(b"FILE_READ_ERROR\n")
            return False
    
    def process_chunk(self, chunk):
        """Process a chunk of data (placeholder for parallel operations)"""
        # In production: compression, encryption, checksum calculation, etc.
        # This demonstrates parallel processing
        return chunk
    
    def handle_client(self, client_socket, client_addr):
        """Handle a client connection"""
        client_ip = client_addr[0]
        self.log(f"Client connected from {client_ip}")
        
        try:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                
                request = data.decode().strip()
                self.log(f"Request from {client_ip}: {request}")
                
                if request == "LIST":
                    files = self.list_files()
                    if files:
                        response = "\n".join(files) + "\n"
                    else:
                        response = "NO_FILES\n"
                    client_socket.sendall(response.encode())
                
                elif request.startswith("GET "):
                    filename = request[4:].strip()
                    self.send_file(client_socket, filename)
                
                elif request == "QUIT":
                    break
                
                else:
                    client_socket.sendall(b"UNKNOWN_COMMAND\n")
        
        except Exception as e:
            self.log(f"Error handling client: {e}")
        finally:
            client_socket.close()
            self.log(f"Client {client_ip} disconnected")
    
    def start(self):
        """Start the server"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server_socket.bind(('0.0.0.0', self.port))
            server_socket.listen(10)
            self.running = True
            
            self.log(f"Parallel File Server started on port {self.port}")
            self.log(f"Serving files from: {self.directory.absolute()}")
            self.log("Waiting for connections...")
            
            while self.running:
                client_socket, client_addr = server_socket.accept()
                # Handle each client in a separate thread
                thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, client_addr)
                )
                thread.daemon = True
                thread.start()
        
        except KeyboardInterrupt:
            self.log("Server shutting down...")
        except Exception as e:
            self.log(f"Server error: {e}")
        finally:
            server_socket.close()
            self.executor.shutdown(wait=True)

def main():
    port = 8080
    directory = "server_files"
    
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    if len(sys.argv) > 2:
        directory = sys.argv[2]
    
    server = ParallelFileServer(port, directory)
    server.start()

if __name__ == "__main__":
    main()

