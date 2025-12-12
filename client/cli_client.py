#!/usr/bin/env python3
"""
Simple command-line client for the Parallel File Server
Useful for testing and automation
"""

import socket
import sys
import argparse

def connect_to_server(host, port):
    """Connect to the file server"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        sock.connect((host, port))
        return sock
    except Exception as e:
        print(f"Error connecting to server: {e}")
        return None

def list_files(sock):
    """Request and display list of available files"""
    try:
        sock.sendall(b"LIST\n")
        response = b""
        while b"\n" not in response:
            chunk = sock.recv(1024)
            if not chunk:
                break
            response += chunk
        
        files = response.decode().strip().split('\n')
        if files and files[0] and files[0] != "NO_FILES":
            print("\nAvailable files:")
            print("-" * 40)
            for i, file in enumerate(files, 1):
                if file:
                    print(f"{i}. {file}")
            print("-" * 40)
            return files
        else:
            print("No files available on server")
            return []
    except Exception as e:
        print(f"Error listing files: {e}")
        return []

def download_file(sock, filename, save_path):
    """Download a file from the server"""
    try:
        # Send GET request
        request = f"GET {filename}\n"
        sock.sendall(request.encode())
        
        # Receive file size
        size_data = b""
        while b"\n" not in size_data:
            chunk = sock.recv(1)
            if not chunk:
                print("Connection closed by server")
                return False
            size_data += chunk
        
        try:
            file_size = int(size_data.decode().strip())
        except ValueError:
            error_msg = size_data.decode().strip()
            if error_msg == "FILE_NOT_FOUND":
                print(f"Error: File '{filename}' not found on server")
            else:
                print(f"Server error: {error_msg}")
            return False
        
        # Receive file data
        print(f"Downloading '{filename}' ({file_size} bytes)...")
        received = 0
        with open(save_path, 'wb') as f:
            while received < file_size:
                chunk = sock.recv(min(8192, file_size - received))
                if not chunk:
                    break
                f.write(chunk)
                received += len(chunk)
                progress = (received / file_size) * 100
                print(f"\rProgress: {progress:.1f}%", end='', flush=True)
        
        print()  # New line after progress
        if received == file_size:
            print(f"File saved to: {save_path}")
            return True
        else:
            print("Error: Incomplete file transfer")
            return False
            
    except Exception as e:
        print(f"Error downloading file: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Parallel File Server CLI Client')
    parser.add_argument('--host', default='localhost', help='Server host (default: localhost)')
    parser.add_argument('--port', type=int, default=8080, help='Server port (default: 8080)')
    parser.add_argument('--list', action='store_true', help='List available files')
    parser.add_argument('--download', type=str, help='Download a file (specify filename)')
    parser.add_argument('--output', type=str, help='Output path for downloaded file')
    
    args = parser.parse_args()
    
    sock = connect_to_server(args.host, args.port)
    if not sock:
        sys.exit(1)
    
    try:
        if args.list:
            list_files(sock)
        elif args.download:
            output_path = args.output or args.download
            download_file(sock, args.download, output_path)
        else:
            # Interactive mode
            print(f"Connected to {args.host}:{args.port}")
            print("Commands: list, download <filename>, quit")
            
            while True:
                try:
                    cmd = input("\n> ").strip().split()
                    if not cmd:
                        continue
                    
                    if cmd[0] == "quit" or cmd[0] == "exit":
                        sock.sendall(b"QUIT\n")
                        break
                    elif cmd[0] == "list":
                        list_files(sock)
                    elif cmd[0] == "download" and len(cmd) > 1:
                        filename = cmd[1]
                        output_path = cmd[2] if len(cmd) > 2 else filename
                        download_file(sock, filename, output_path)
                    else:
                        print("Unknown command. Use: list, download <filename>, quit")
                except KeyboardInterrupt:
                    print("\nExiting...")
                    break
                except Exception as e:
                    print(f"Error: {e}")
    finally:
        sock.close()

if __name__ == '__main__':
    main()

