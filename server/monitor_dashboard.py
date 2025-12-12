#!/usr/bin/env python3
"""
Server Monitoring Dashboard
Real-time monitoring of server nodes and statistics
"""

import socket
import json
import time
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QTextEdit,
                             QTableWidget, QTableWidgetItem, QTabWidget)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont

class MonitorDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.nodes = []  # List of (host, port, node_id)
        self.initUI()
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateAllNodes)
        self.timer.start(2000)  # Update every 2 seconds

    def initUI(self):
        self.setWindowTitle("Server Monitor Dashboard")
        self.setGeometry(100, 100, 1200, 800)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Header
        header = QLabel("📊 Server Monitor Dashboard")
        header.setFont(QFont("Segoe UI", 18, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Node management
        node_frame = QWidget()
        node_layout = QHBoxLayout(node_frame)
        node_layout.addWidget(QLabel("Add Node:"))
        
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("Host")
        node_layout.addWidget(self.host_input)
        
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("Port")
        node_layout.addWidget(self.port_input)
        
        add_btn = QPushButton("Add Node")
        add_btn.clicked.connect(self.addNode)
        node_layout.addWidget(add_btn)
        
        layout.addWidget(node_frame)
        
        # Stats table
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(8)
        self.stats_table.setHorizontalHeaderLabels([
            "Node ID", "Host:Port", "Uptime", "Connections",
            "Active", "Downloads", "Uploads", "Bytes Sent"
        ])
        layout.addWidget(self.stats_table)
        
        # Log
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(QLabel("Activity Log:"))
        layout.addWidget(self.log_text)

    def addNode(self):
        host = self.host_input.text().strip()
        try:
            port = int(self.port_input.text().strip())
            node_id = f"{host}:{port}"
            self.nodes.append((host, port, node_id))
            self.log(f"Added node: {node_id}")
            self.updateAllNodes()
        except:
            self.log("Invalid port number")

    def updateAllNodes(self):
        self.stats_table.setRowCount(len(self.nodes))
        for i, (host, port, node_id) in enumerate(self.nodes):
            stats = self.getNodeStats(host, port)
            if stats:
                self.stats_table.setItem(i, 0, QTableWidgetItem(stats.get('node_id', '')))
                self.stats_table.setItem(i, 1, QTableWidgetItem(f"{host}:{port}"))
                self.stats_table.setItem(i, 2, QTableWidgetItem(self.formatUptime(stats.get('uptime_seconds', 0))))
                self.stats_table.setItem(i, 3, QTableWidgetItem(str(stats.get('connections', 0))))
                self.stats_table.setItem(i, 4, QTableWidgetItem(str(stats.get('active_connections', 0))))
                self.stats_table.setItem(i, 5, QTableWidgetItem(str(stats.get('files_downloaded', 0))))
                self.stats_table.setItem(i, 6, QTableWidgetItem(str(stats.get('files_uploaded', 0))))
                self.stats_table.setItem(i, 7, QTableWidgetItem(self.formatSize(stats.get('bytes_sent', 0))))

    def getNodeStats(self, host, port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((host, port))
            sock.sendall(b"STATS\n")
            
            response = b""
            while b"\n" not in response:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
            
            sock.close()
            return json.loads(response.decode().strip())
        except:
            return None

    def formatUptime(self, seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        return f"{h}h {m}m"

    def formatSize(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QLineEdit
    
    app = QApplication(sys.argv)
    window = MonitorDashboard()
    window.show()
    sys.exit(app.exec_())

