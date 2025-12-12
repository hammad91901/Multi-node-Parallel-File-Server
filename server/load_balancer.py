#!/usr/bin/env python3
"""
Load Balancer for Multi-Node File Server
Distributes requests across multiple server nodes
"""

import socket
import threading
import json
import time
from collections import defaultdict

class LoadBalancer:
    def __init__(self, port=8000):
        self.port = port
        self.nodes = []  # List of (host, port, node_id, load)
        self.node_lock = threading.Lock()
        self.request_stats = defaultdict(int)
        
    def register_node(self, host, port, node_id):
        """Register a new server node"""
        with self.node_lock:
            # Check if node already exists
            for i, (h, p, nid, _) in enumerate(self.nodes):
                if nid == node_id:
                    self.nodes[i] = (host, port, node_id, 0)
                    return
            self.nodes.append((host, port, node_id, 0))
            print(f"Registered node: {node_id} at {host}:{port}")
    
    def get_best_node(self, strategy='round_robin'):
        """Select the best node based on load balancing strategy"""
        with self.node_lock:
            if not self.nodes:
                return None
            
            if strategy == 'round_robin':
                # Simple round-robin
                node = self.nodes[0]
                self.nodes.append(self.nodes.pop(0))
                return node
            
            elif strategy == 'least_connections':
                # Select node with least load
                return min(self.nodes, key=lambda x: x[3])
            
            elif strategy == 'random':
                import random
                return random.choice(self.nodes)
            
            return self.nodes[0]
    
    def update_node_load(self, node_id, delta):
        """Update load for a specific node"""
        with self.node_lock:
            for i, (h, p, nid, load) in enumerate(self.nodes):
                if nid == node_id:
                    self.nodes[i] = (h, p, nid, max(0, load + delta))
                    break
    
    def forward_request(self, client_socket, request_data):
        """Forward client request to appropriate node"""
        try:
            # Parse request to determine strategy
            request = request_data.decode().strip()
            command = request.split()[0] if request else "LIST"
            
            # Select node
            node = self.get_best_node('least_connections')
            if not node:
                client_socket.sendall(b'{"error": "No nodes available"}\n')
                return
            
            host, port, node_id, _ = node
            self.update_node_load(node_id, 1)
            self.request_stats[node_id] += 1
            
            # Forward to node
            node_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            node_socket.settimeout(10)
            node_socket.connect((host, port))
            
            # Send request
            node_socket.sendall(request_data)
            
            # Relay response
            while True:
                chunk = node_socket.recv(8192)
                if not chunk:
                    break
                client_socket.sendall(chunk)
            
            node_socket.close()
            self.update_node_load(node_id, -1)
            
        except Exception as e:
            print(f"Error forwarding request: {e}")
            client_socket.sendall(b'{"error": "Request forwarding failed"}\n')
    
    def handle_client(self, client_socket, client_addr):
        """Handle client connection"""
        print(f"Client connected from {client_addr[0]}")
        
        try:
            while True:
                data = client_socket.recv(4096)
                if not data:
                    break
                self.forward_request(client_socket, data)
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            client_socket.close()
            print(f"Client {client_addr[0]} disconnected")
    
    def get_statistics(self):
        """Get load balancer statistics"""
        with self.node_lock:
            return {
                'nodes': len(self.nodes),
                'node_list': [{'id': nid, 'host': h, 'port': p, 'load': l} 
                             for h, p, nid, l in self.nodes],
                'request_stats': dict(self.request_stats)
            }
    
    def start(self):
        """Start the load balancer"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server_socket.bind(('0.0.0.0', self.port))
            server_socket.listen(20)
            
            print(f"Load Balancer started on port {self.port}")
            print("Waiting for connections...")
            
            # Register nodes (can be done via API in future)
            # Example: self.register_node('localhost', 8080, 'node1')
            
            while True:
                client_socket, client_addr = server_socket.accept()
                thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, client_addr)
                )
                thread.daemon = True
                thread.start()
        
        except KeyboardInterrupt:
            print("Load balancer shutting down...")
        finally:
            server_socket.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Load Balancer for Multi-Node File Server')
    parser.add_argument('--port', type=int, default=8000, help='Load balancer port')
    args = parser.parse_args()
    
    lb = LoadBalancer(args.port)
    lb.start()

