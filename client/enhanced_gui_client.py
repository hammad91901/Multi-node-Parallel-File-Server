#!/usr/bin/env python3
"""
Enhanced GUI Client for Parallel File Server
Features:
- File upload/download
- Directory browsing
- File search
- File metadata viewing
- Server statistics
- Multi-node support
- Compression options
"""

import sys
import socket
import json
import os
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QLabel, QTextEdit, QProgressBar,
    QFileDialog, QMessageBox, QFrame, QSplitter, QTreeWidget,
    QTreeWidgetItem, QLineEdit, QTabWidget, QTableWidget,
    QTableWidgetItem, QGroupBox, QCheckBox, QComboBox, QInputDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon

class FileTransferThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, host, port, operation, source_path, dest_path=None, compress=False):
        super().__init__()
        self.host = host
        self.port = port
        self.operation = operation  # 'download' or 'upload'
        self.source_path = source_path
        self.dest_path = dest_path
        self.compress = compress

    def run(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(30)
            sock.connect((self.host, self.port))
            
            if self.operation == 'download':
                self._download_file(sock)
            elif self.operation == 'upload':
                self._upload_file(sock)
            
            sock.close()
        except Exception as e:
            self.error.emit(f"Error: {str(e)}")

    def _download_file(self, sock):
        request = f"GET {self.source_path}"
        if self.compress:
            request += " COMPRESS"
        request += "\n"
        sock.sendall(request.encode())
        
        # Receive metadata
        metadata_data = b""
        while b"\n" not in metadata_data:
            chunk = sock.recv(1)
            if not chunk:
                self.error.emit("Connection closed")
                return
            metadata_data += chunk
        
        try:
            metadata = json.loads(metadata_data.decode().strip())
            file_size = metadata.get('size', 0)
        except:
            try:
                file_size = int(metadata_data.decode().strip())
            except:
                error_msg = metadata_data.decode().strip()
                if "FILE_NOT_FOUND" in error_msg or "error" in error_msg.lower():
                    self.error.emit(f"File not found: {self.source_path}")
                else:
                    self.error.emit(f"Server error: {error_msg}")
                return
        
        # Receive file data
        received = 0
        with open(self.dest_path, 'wb') as f:
            while received < file_size:
                chunk = sock.recv(min(8192, file_size - received))
                if not chunk:
                    break
                f.write(chunk)
                received += len(chunk)
                progress = int((received / file_size) * 100)
                self.progress.emit(progress)
        
        if received == file_size:
            self.finished.emit(f"Downloaded '{Path(self.source_path).name}' successfully!")
        else:
            self.error.emit("Incomplete transfer")

    def _upload_file(self, sock):
        file_path = Path(self.source_path)
        if not file_path.exists():
            self.error.emit("File not found")
            return
        
        file_size = file_path.stat().st_size
        
        # Prepare metadata
        metadata = {
            'name': file_path.name,
            'size': file_size,
            'type': 'file'
        }
        
        request = f"PUT {self.dest_path}\n"
        sock.sendall(request.encode())
        
        # Send metadata
        metadata_json = json.dumps(metadata) + "\n"
        sock.sendall(metadata_json.encode())
        
        # Send file data
        sent = 0
        with open(file_path, 'rb') as f:
            while sent < file_size:
                chunk = f.read(8192)
                if not chunk:
                    break
                sock.sendall(chunk)
                sent += len(chunk)
                progress = int((sent / file_size) * 100)
                self.progress.emit(progress)
        
        if sent == file_size:
            self.finished.emit(f"Uploaded '{file_path.name}' successfully!")
        else:
            self.error.emit("Incomplete upload")

class EnhancedFileServerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.host = "localhost"
        self.port = 8080
        self.sock = None
        self.current_path = ""
        self.transfer_thread = None
        self.initUI()
        self.applyModernStyle()

    def initUI(self):
        self.setWindowTitle("Enhanced Parallel File Server - Client")
        self.setGeometry(50, 50, 1400, 900)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        header = QLabel("🚀 Enhanced Parallel File Server Client")
        header.setFont(QFont("Segoe UI", 20, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("color: #2c3e50; padding: 10px;")
        main_layout.addWidget(header)
        
        # Connection panel
        conn_frame = self.createConnectionPanel()
        main_layout.addWidget(conn_frame)
        
        # Main content area with tabs
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                background: white;
            }
            QTabBar::tab {
                background: #ecf0f1;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background: #3498db;
                color: white;
            }
        """)
        
        # File Browser Tab
        browser_tab = self.createBrowserTab()
        tabs.addTab(browser_tab, "📁 File Browser")
        
        # Search Tab
        search_tab = self.createSearchTab()
        tabs.addTab(search_tab, "🔍 Search")
        
        # Statistics Tab
        stats_tab = self.createStatsTab()
        tabs.addTab(stats_tab, "📊 Statistics")
        
        main_layout.addWidget(tabs)
        
        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("padding: 5px; background: #ecf0f1; border-radius: 3px;")
        main_layout.addWidget(self.status_label)

    def createConnectionPanel(self):
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel)
        frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db, stop:1 #2980b9);
                border-radius: 10px;
                padding: 15px;
            }
        """)
        layout = QHBoxLayout(frame)
        
        layout.addWidget(self.createLabel("Host:", "white"))
        self.host_input = QLineEdit()
        self.host_input.setText("localhost")
        self.host_input.setStyleSheet(self.getInputStyle())
        layout.addWidget(self.host_input)
        
        layout.addWidget(self.createLabel("Port:", "white"))
        self.port_input = QLineEdit()
        self.port_input.setText("8080")
        self.port_input.setStyleSheet(self.getInputStyle())
        layout.addWidget(self.port_input)
        
        self.connect_btn = QPushButton("🔌 Connect")
        self.connect_btn.setStyleSheet(self.getButtonStyle("#27ae60"))
        self.connect_btn.clicked.connect(self.connectToServer)
        layout.addWidget(self.connect_btn)
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setStyleSheet(self.getButtonStyle("#3498db"))
        self.refresh_btn.clicked.connect(self.refreshFileList)
        self.refresh_btn.setEnabled(False)
        layout.addWidget(self.refresh_btn)
        
        layout.addStretch()
        return frame

    def createBrowserTab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        self.upload_btn = QPushButton("⬆️ Upload File")
        self.upload_btn.setStyleSheet(self.getButtonStyle("#e74c3c"))
        self.upload_btn.clicked.connect(self.uploadFile)
        self.upload_btn.setEnabled(False)
        toolbar.addWidget(self.upload_btn)
        
        self.download_btn = QPushButton("⬇️ Download")
        self.download_btn.setStyleSheet(self.getButtonStyle("#27ae60"))
        self.download_btn.clicked.connect(self.downloadFile)
        self.download_btn.setEnabled(False)
        toolbar.addWidget(self.download_btn)
        
        self.metadata_btn = QPushButton("ℹ️ Metadata")
        self.metadata_btn.setStyleSheet(self.getButtonStyle("#9b59b6"))
        self.metadata_btn.clicked.connect(self.showMetadata)
        self.metadata_btn.setEnabled(False)
        toolbar.addWidget(self.metadata_btn)
        
        compress_check = QCheckBox("Compress")
        compress_check.setStyleSheet("color: #34495e; font-weight: bold;")
        self.compress_checkbox = compress_check
        toolbar.addWidget(compress_check)
        
        toolbar.addStretch()
        
        # Navigation
        nav_layout = QHBoxLayout()
        nav_layout.addWidget(QLabel("Path:"))
        self.path_label = QLabel("/")
        self.path_label.setStyleSheet("padding: 5px; background: white; border: 1px solid #bdc3c7; border-radius: 3px;")
        nav_layout.addWidget(self.path_label)
        
        self.up_btn = QPushButton("⬆️ Up")
        self.up_btn.setStyleSheet(self.getButtonStyle("#95a5a6"))
        self.up_btn.clicked.connect(self.navigateUp)
        self.up_btn.setEnabled(False)
        nav_layout.addWidget(self.up_btn)
        toolbar.addLayout(nav_layout)
        
        layout.addLayout(toolbar)
        
        # File tree
        splitter = QSplitter(Qt.Horizontal)
        
        # File list
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabels(["Name", "Size", "Type", "Modified"])
        self.file_tree.setStyleSheet("""
            QTreeWidget {
                background: white;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                font-size: 12px;
            }
            QTreeWidget::item {
                padding: 5px;
                border-bottom: 1px solid #ecf0f1;
            }
            QTreeWidget::item:hover {
                background: #e8f4f8;
            }
            QTreeWidget::item:selected {
                background: #3498db;
                color: white;
            }
        """)
        self.file_tree.itemDoubleClicked.connect(self.onItemDoubleClick)
        splitter.addWidget(self.file_tree)
        
        # Log panel
        log_frame = QFrame()
        log_layout = QVBoxLayout(log_frame)
        log_layout.addWidget(QLabel("📋 Activity Log"))
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background: #2c3e50;
                color: #ecf0f1;
                border: 2px solid #34495e;
                border-radius: 8px;
                padding: 10px;
                font-family: 'Consolas', monospace;
                font-size: 11px;
            }
        """)
        log_layout.addWidget(self.log_text)
        splitter.addWidget(log_frame)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #34495e;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
                background: #34495e;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db, stop:1 #2980b9);
                border-radius: 3px;
            }
        """)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        return widget

    def createSearchTab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Search controls
        search_frame = QFrame()
        search_layout = QHBoxLayout(search_frame)
        
        search_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter search query...")
        self.search_input.setStyleSheet(self.getInputStyle())
        self.search_input.returnPressed.connect(self.performSearch)
        search_layout.addWidget(self.search_input)
        
        search_type = QComboBox()
        search_type.addItems(["Name", "Content"])
        search_type.setStyleSheet(self.getInputStyle())
        search_layout.addWidget(search_type)
        self.search_type_combo = search_type
        
        search_btn = QPushButton("🔍 Search")
        search_btn.setStyleSheet(self.getButtonStyle("#3498db"))
        search_btn.clicked.connect(self.performSearch)
        search_btn.setEnabled(False)
        self.search_btn = search_btn
        search_layout.addWidget(search_btn)
        
        layout.addWidget(search_frame)
        
        # Results table
        self.search_results = QTableWidget()
        self.search_results.setColumnCount(4)
        self.search_results.setHorizontalHeaderLabels(["Name", "Size", "Path", "Modified"])
        self.search_results.setStyleSheet("""
            QTableWidget {
                background: white;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background: #3498db;
                color: white;
            }
        """)
        self.search_results.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.search_results)
        
        return widget

    def createStatsTab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        stats_frame = QGroupBox("Server Statistics")
        stats_frame.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        stats_layout = QVBoxLayout(stats_frame)
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setStyleSheet("""
            QTextEdit {
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Consolas', monospace;
            }
        """)
        stats_layout.addWidget(self.stats_text)
        
        refresh_stats_btn = QPushButton("🔄 Refresh Statistics")
        refresh_stats_btn.setStyleSheet(self.getButtonStyle("#3498db"))
        refresh_stats_btn.clicked.connect(self.refreshStatistics)
        refresh_stats_btn.setEnabled(False)
        self.refresh_stats_btn = refresh_stats_btn
        stats_layout.addWidget(refresh_stats_btn)
        
        layout.addWidget(stats_frame)
        layout.addStretch()
        
        return widget

    def createLabel(self, text, color="black"):
        label = QLabel(text)
        label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 12px;")
        return label

    def getInputStyle(self):
        return """
            QLineEdit {
                background: white;
                border: 2px solid #ecf0f1;
                border-radius: 5px;
                padding: 5px;
                font-size: 12px;
            }
        """

    def getButtonStyle(self, color):
        return f"""
            QPushButton {{
                background: {color};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: {self.darkenColor(color)};
            }}
            QPushButton:disabled {{
                background: #95a5a6;
            }}
        """

    def darkenColor(self, hex_color):
        color_map = {
            "#3498db": "#2980b9",
            "#27ae60": "#229954",
            "#e74c3c": "#c0392b",
            "#9b59b6": "#8e44ad",
            "#95a5a6": "#7f8c8d"
        }
        return color_map.get(hex_color, hex_color)

    def applyModernStyle(self):
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ecf0f1, stop:1 #bdc3c7);
            }
        """)

    def log(self, message):
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
        self.status_label.setText(message)

    def connectToServer(self):
        try:
            self.host = self.host_input.text().strip()
            self.port = int(self.port_input.text().strip())
            
            if self.sock:
                self.sock.close()
            
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5)
            self.sock.connect((self.host, self.port))
            self.sock.settimeout(None)
            
            self.log(f"Connected to {self.host}:{self.port}")
            self.connect_btn.setText("✅ Connected")
            self.connect_btn.setEnabled(False)
            self.refresh_btn.setEnabled(True)
            self.upload_btn.setEnabled(True)
            self.download_btn.setEnabled(True)
            self.metadata_btn.setEnabled(True)
            self.search_btn.setEnabled(True)
            self.refresh_stats_btn.setEnabled(True)
            self.up_btn.setEnabled(True)
            self.refreshFileList()
            
        except Exception as e:
            self.log(f"Connection failed: {str(e)}")
            QMessageBox.critical(self, "Connection Error", f"Failed to connect:\n{str(e)}")
            if self.sock:
                self.sock.close()
                self.sock = None

    def refreshFileList(self):
        if not self.sock:
            return
        
        try:
            request = f"LIST {self.current_path}\n"
            self.sock.sendall(request.encode())
            
            response = b""
            while b"\n" not in response:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                response += chunk
            
            items = json.loads(response.decode().strip())
            self.file_tree.clear()
            
            for item in items:
                tree_item = QTreeWidgetItem([
                    item.get('name', ''),
                    self.formatSize(item.get('size', 0)),
                    item.get('type', ''),
                    item.get('modified', '')[:19] if item.get('modified') else ''
                ])
                tree_item.setData(0, Qt.UserRole, item.get('path', ''))
                self.file_tree.addTopLevelItem(tree_item)
            
            self.path_label.setText(self.current_path or "/")
            self.log(f"Refreshed: {len(items)} items")
            
        except Exception as e:
            self.log(f"Error refreshing: {str(e)}")

    def formatSize(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def onItemDoubleClick(self, item, column):
        path = item.data(0, Qt.UserRole)
        item_type = item.text(2)
        
        if item_type == 'directory':
            self.current_path = path
            self.refreshFileList()
        else:
            self.downloadFile()

    def navigateUp(self):
        if self.current_path:
            parts = self.current_path.rstrip('/').split('/')
            if len(parts) > 1:
                self.current_path = '/'.join(parts[:-1])
            else:
                self.current_path = ""
            self.refreshFileList()

    def downloadFile(self):
        selected = self.file_tree.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a file to download")
            return
        
        item = selected[0]
        if item.text(2) == 'directory':
            QMessageBox.warning(self, "Invalid Selection", "Please select a file, not a directory")
            return
        
        filepath = item.data(0, Qt.UserRole)
        save_path, _ = QFileDialog.getSaveFileName(self, "Save File", item.text(0))
        
        if not save_path:
            return
        
        self.log(f"Downloading '{item.text(0)}'...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.download_btn.setEnabled(False)
        
        compress = self.compress_checkbox.isChecked()
        self.transfer_thread = FileTransferThread(
            self.host, self.port, 'download', filepath, save_path, compress
        )
        self.transfer_thread.progress.connect(self.progress_bar.setValue)
        self.transfer_thread.finished.connect(self.onTransferFinished)
        self.transfer_thread.error.connect(self.onTransferError)
        self.transfer_thread.start()

    def uploadFile(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File to Upload")
        if not file_path:
            return
        
        # Ask for destination path
        dest_path, ok = QInputDialog.getText(self, "Upload File", "Destination path (leave empty for root):")
        if not ok:
            return
        
        if not dest_path:
            dest_path = Path(file_path).name
        elif not dest_path.endswith(Path(file_path).name):
            dest_path = f"{dest_path}/{Path(file_path).name}"
        
        self.log(f"Uploading '{Path(file_path).name}'...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.upload_btn.setEnabled(False)
        
        self.transfer_thread = FileTransferThread(
            self.host, self.port, 'upload', file_path, dest_path, False
        )
        self.transfer_thread.progress.connect(self.progress_bar.setValue)
        self.transfer_thread.finished.connect(self.onTransferFinished)
        self.transfer_thread.error.connect(self.onTransferError)
        self.transfer_thread.start()

    def showMetadata(self):
        selected = self.file_tree.selectedItems()
        if not selected:
            return
        
        item = selected[0]
        filepath = item.data(0, Qt.UserRole)
        
        try:
            request = f"METADATA {filepath}\n"
            self.sock.sendall(request.encode())
            
            response = b""
            while b"\n" not in response:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                response += chunk
            
            metadata = json.loads(response.decode().strip())
            
            info = f"""
File: {metadata.get('name', 'N/A')}
Size: {self.formatSize(metadata.get('size', 0))}
Type: {metadata.get('type', 'N/A')}
Modified: {metadata.get('modified', 'N/A')}
Created: {metadata.get('created', 'N/A')}
MD5: {metadata.get('md5', 'N/A')}
            """
            QMessageBox.information(self, "File Metadata", info.strip())
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to get metadata: {str(e)}")

    def performSearch(self):
        query = self.search_input.text().strip()
        if not query:
            return
        
        search_type = self.search_type_combo.currentText().lower()
        
        try:
            request = f"SEARCH {query} {search_type}\n"
            self.sock.sendall(request.encode())
            
            response = b""
            while b"\n" not in response:
                chunk = self.sock.recv(65536)
                if not chunk:
                    break
                response += chunk
            
            results = json.loads(response.decode().strip())
            
            self.search_results.setRowCount(len(results))
            for i, result in enumerate(results):
                self.search_results.setItem(i, 0, QTableWidgetItem(result.get('name', '')))
                self.search_results.setItem(i, 1, QTableWidgetItem(self.formatSize(result.get('size', 0))))
                self.search_results.setItem(i, 2, QTableWidgetItem(result.get('path', '')))
                self.search_results.setItem(i, 3, QTableWidgetItem(result.get('modified', '')[:19] if result.get('modified') else ''))
            
            self.log(f"Search found {len(results)} results")
            
        except Exception as e:
            self.log(f"Search error: {str(e)}")

    def refreshStatistics(self):
        try:
            request = "STATS\n"
            self.sock.sendall(request.encode())
            
            response = b""
            while b"\n" not in response:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                response += chunk
            
            stats = json.loads(response.decode().strip())
            
            info = f"""
Node ID: {stats.get('node_id', 'N/A')}
Port: {stats.get('port', 'N/A')}
Uptime: {self.formatUptime(stats.get('uptime_seconds', 0))}
Total Connections: {stats.get('connections', 0)}
Active Connections: {stats.get('active_connections', 0)}
Files Downloaded: {stats.get('files_downloaded', 0)}
Files Uploaded: {stats.get('files_uploaded', 0)}
Bytes Sent: {self.formatSize(stats.get('bytes_sent', 0))}
Bytes Received: {self.formatSize(stats.get('bytes_received', 0))}
            """
            self.stats_text.setText(info.strip())
            self.log("Statistics refreshed")
            
        except Exception as e:
            self.log(f"Error getting statistics: {str(e)}")

    def formatUptime(self, seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours}h {minutes}m {secs}s"

    def onTransferFinished(self, message):
        self.log(message)
        self.progress_bar.setVisible(False)
        self.download_btn.setEnabled(True)
        self.upload_btn.setEnabled(True)
        self.refreshFileList()
        QMessageBox.information(self, "Success", message)

    def onTransferError(self, error):
        self.log(f"Error: {error}")
        self.progress_bar.setVisible(False)
        self.download_btn.setEnabled(True)
        self.upload_btn.setEnabled(True)
        QMessageBox.critical(self, "Error", error)

    def closeEvent(self, event):
        if self.sock:
            try:
                self.sock.sendall(b"QUIT\n")
                self.sock.close()
            except:
                pass
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = EnhancedFileServerGUI()
    window.show()
    
    sys.exit(app.exec_())

