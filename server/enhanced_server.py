#!/usr/bin/env python3
"""
Enhanced Parallel File Server with Advanced Features
- File upload/download
- Directory browsing
- File search
- File metadata
- Compression support
- Multi-node coordination
- Server statistics
"""

import socket
import threading
import os
import sys
import json
import hashlib
import gzip
import zlib
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import multiprocessing
from collections import defaultdict

class EnhancedFileServer:
    def __init__(self, port=8080, directory="server_files", node_id=None):
        self.port = port
        self.directory = Path(directory)
        self.directory.mkdir(exist_ok=True, parents=True)
        self.node_id = node_id or f"node_{port}"
        self.running = False
        self.log_lock = threading.Lock()
        self.stats_lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=20)
        
        # Statistics
        self.stats = {
            'connections': 0,
            'files_downloaded': 0,
            'files_uploaded': 0,
            'bytes_sent': 0,
            'bytes_received': 0,
            'active_connections': 0,
            'start_time': datetime.now()
        }
        
        # Multi-node coordination
        self.peer_nodes = {}  # {node_id: (host, port)}
        self.file_replicas = defaultdict(list)  # {filename: [node_ids]}
        
    def log(self, message):
        with self.log_lock:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] [{self.node_id}] {message}")
    
    def update_stats(self, **kwargs):
        with self.stats_lock:
            for key, value in kwargs.items():
                if key in self.stats:
                    if isinstance(self.stats[key], (int, float)):
                        self.stats[key] += value
                    else:
                        self.stats[key] = value
    
    def get_file_metadata(self, filepath):
        """Get comprehensive file metadata"""
        try:
            stat = filepath.stat()
            md5_hash = self.calculate_checksum(filepath)
            return {
                'name': filepath.name,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'md5': md5_hash,
                'type': 'file' if filepath.is_file() else 'directory'
            }
        except Exception as e:
            return None
    
    def calculate_checksum(self, filepath, algorithm='md5'):
        """Calculate file checksum in parallel chunks"""
        hash_obj = hashlib.md5() if algorithm == 'md5' else hashlib.sha256()
        chunk_size = 8192
        
        with open(filepath, 'rb') as f:
            # Use multiprocessing for parallel hash calculation
            with multiprocessing.Pool(processes=4) as pool:
                chunks = []
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    chunks.append(chunk)
                
                # Process chunks in parallel
                hashes = pool.map(lambda c: hashlib.md5(c).digest(), chunks)
                for h in hashes:
                    hash_obj.update(h)
        
        return hash_obj.hexdigest()
    
    def list_directory(self, subpath=""):
        """List files and directories with metadata"""
        try:
            target_dir = self.directory / subpath if subpath else self.directory
            if not target_dir.exists() or not target_dir.is_dir():
                return []
            
            items = []
            for item in target_dir.iterdir():
                metadata = self.get_file_metadata(item)
                if metadata:
                    metadata['path'] = str(item.relative_to(self.directory))
                    items.append(metadata)
            
            return sorted(items, key=lambda x: (x['type'] == 'file', x['name'].lower()))
        except Exception as e:
            self.log(f"Error listing directory: {e}")
            return []
    
    def search_files(self, query, search_type='name'):
        """Search for files by name or content"""
        results = []
        query_lower = query.lower()
        
        try:
            # Parallel file search
            with multiprocessing.Pool(processes=4) as pool:
                all_files = list(self.directory.rglob('*'))
                search_tasks = [(f, query_lower, search_type) for f in all_files if f.is_file()]
                
                # Parallel search
                matches = pool.starmap(self._search_file, search_tasks)
                results = [m for m in matches if m]
        
        except Exception as e:
            self.log(f"Error searching files: {e}")
        
        return results
    
    def _search_file(self, filepath, query, search_type):
        """Search a single file (used in parallel)"""
        try:
            if search_type == 'name':
                if query in filepath.name.lower():
                    return self.get_file_metadata(filepath)
            elif search_type == 'content':
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read().lower()
                        if query in content:
                            return self.get_file_metadata(filepath)
                except:
                    pass
        except:
            pass
        return None
    
    def send_file(self, client_socket, filepath, compress=False):
        """Send a file with optional compression"""
        if not filepath.exists():
            client_socket.sendall(b"FILE_NOT_FOUND\n")
            return False
        
        try:
            file_size = filepath.stat().st_size
            
            # Send metadata
            metadata = self.get_file_metadata(filepath)
            metadata_json = json.dumps(metadata) + "\n"
            client_socket.sendall(metadata_json.encode())
            
            # Read and process file in parallel
            chunk_size = 8192
            with open(filepath, 'rb') as f:
                with multiprocessing.Pool(processes=4) as pool:
                    chunks = []
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        chunks.append(chunk)
                    
                    # Process chunks in parallel
                    if compress:
                        processed_chunks = pool.map(self._compress_chunk, chunks)
                    else:
                        processed_chunks = chunks
                    
                    # Send chunks
                    total_sent = 0
                    for chunk in processed_chunks:
                        client_socket.sendall(chunk)
                        total_sent += len(chunk)
            
            self.update_stats(files_downloaded=1, bytes_sent=total_sent)
            self.log(f"File '{filepath.name}' ({total_sent} bytes) sent successfully")
            return True
            
        except Exception as e:
            self.log(f"Error sending file: {e}")
            client_socket.sendall(b"FILE_READ_ERROR\n")
            return False
    
    def _compress_chunk(self, chunk):
        """Compress a chunk (parallel operation)"""
        return gzip.compress(chunk)
    
    def receive_file(self, client_socket, filepath):
        """Receive and save a file from client"""
        try:
            # Receive metadata
            metadata_data = b""
            while b"\n" not in metadata_data:
                chunk = client_socket.recv(1)
                if not chunk:
                    return False
                metadata_data += chunk
            
            try:
                metadata = json.loads(metadata_data.decode().strip())
                file_size = metadata.get('size', 0)
            except:
                # Fallback: receive size as plain text
                file_size = int(metadata_data.decode().strip())
            
            # Ensure directory exists
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Receive file data
            received = 0
            with open(filepath, 'wb') as f:
                while received < file_size:
                    chunk = client_socket.recv(min(8192, file_size - received))
                    if not chunk:
                        break
                    f.write(chunk)
                    received += len(chunk)
            
            if received == file_size:
                self.update_stats(files_uploaded=1, bytes_received=received)
                self.log(f"File '{filepath.name}' ({received} bytes) received successfully")
                return True
            else:
                self.log(f"Incomplete file transfer: {received}/{file_size}")
                return False
                
        except Exception as e:
            self.log(f"Error receiving file: {e}")
            return False
    
    def get_statistics(self):
        """Get server statistics"""
        with self.stats_lock:
            uptime = (datetime.now() - self.stats['start_time']).total_seconds()
            stats = self.stats.copy()
            stats['uptime_seconds'] = uptime
            stats['node_id'] = self.node_id
            stats['port'] = self.port
            return stats
    
    def handle_client(self, client_socket, client_addr):
        """Handle a client connection"""
        client_ip = client_addr[0]
        self.update_stats(connections=1, active_connections=1)
        self.log(f"Client connected from {client_ip}")
        
        try:
            while True:
                data = client_socket.recv(4096)
                if not data:
                    break
                
                request = data.decode().strip()
                parts = request.split(' ', 2)
                command = parts[0]
                
                self.log(f"Request from {client_ip}: {command}")
                
                if command == "LIST":
                    subpath = parts[1] if len(parts) > 1 else ""
                    items = self.list_directory(subpath)
                    response = json.dumps(items) + "\n"
                    client_socket.sendall(response.encode())
                
                elif command == "GET":
                    filepath_str = parts[1] if len(parts) > 1 else ""
                    compress = len(parts) > 2 and parts[2] == "COMPRESS"
                    filepath = self.directory / filepath_str
                    self.send_file(client_socket, filepath, compress)
                
                elif command == "PUT":
                    filepath_str = parts[1] if len(parts) > 1 else ""
                    filepath = self.directory / filepath_str
                    self.receive_file(client_socket, filepath)
                
                elif command == "SEARCH":
                    query = parts[1] if len(parts) > 1 else ""
                    search_type = parts[2] if len(parts) > 2 else "name"
                    results = self.search_files(query, search_type)
                    response = json.dumps(results) + "\n"
                    client_socket.sendall(response.encode())
                
                elif command == "STATS":
                    stats = self.get_statistics()
                    response = json.dumps(stats) + "\n"
                    client_socket.sendall(response.encode())
                
                elif command == "METADATA":
                    filepath_str = parts[1] if len(parts) > 1 else ""
                    filepath = self.directory / filepath_str
                    metadata = self.get_file_metadata(filepath)
                    if metadata:
                        response = json.dumps(metadata) + "\n"
                    else:
                        response = json.dumps({"error": "File not found"}) + "\n"
                    client_socket.sendall(response.encode())
                
                elif command == "QUIT":
                    break
                
                else:
                    client_socket.sendall(b'{"error": "UNKNOWN_COMMAND"}\n')
        
        except Exception as e:
            self.log(f"Error handling client: {e}")
        finally:
            client_socket.close()
            self.update_stats(active_connections=-1)
            self.log(f"Client {client_ip} disconnected")
    
    def start(self):
        """Start the server"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server_socket.bind(('0.0.0.0', self.port))
            server_socket.listen(20)
            self.running = True
            
            self.log(f"Enhanced Parallel File Server started on port {self.port}")
            self.log(f"Serving files from: {self.directory.absolute()}")
            self.log(f"Node ID: {self.node_id}")
            self.log("Waiting for connections...")
            
            while self.running:
                client_socket, client_addr = server_socket.accept()
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
    import argparse
    parser = argparse.ArgumentParser(description='Enhanced Parallel File Server')
    parser.add_argument('--port', type=int, default=8080, help='Server port')
    parser.add_argument('--directory', default='server_files', help='File directory')
    parser.add_argument('--node-id', help='Node identifier for multi-node setup')
    args = parser.parse_args()
    
    server = EnhancedFileServer(args.port, args.directory, args.node_id)
    server.start()

if __name__ == "__main__":
    main()

