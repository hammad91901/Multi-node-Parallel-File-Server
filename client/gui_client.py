import sys
import socket
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QListWidget, QLabel, 
                             QTextEdit, QProgressBar, QFileDialog, QMessageBox,
                             QFrame, QSplitter)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon, QPixmap
import os

class FileTransferThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, host, port, filename, save_path):
        super().__init__()
        self.host = host
        self.port = port
        self.filename = filename
        self.save_path = save_path

    def run(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((self.host, self.port))
            
            # Send GET request
            request = f"GET {self.filename}\n"
            sock.sendall(request.encode())
            
            # Receive file size
            size_data = b""
            while b"\n" not in size_data:
                chunk = sock.recv(1)
                if not chunk:
                    self.error.emit("Connection closed by server")
                    return
                size_data += chunk
            
            try:
                file_size = int(size_data.decode().strip())
            except ValueError:
                error_msg = size_data.decode().strip()
                if error_msg == "FILE_NOT_FOUND":
                    self.error.emit(f"File '{self.filename}' not found on server")
                else:
                    self.error.emit(f"Server error: {error_msg}")
                sock.close()
                return
            
            # Receive file data
            received = 0
            with open(self.save_path, 'wb') as f:
                while received < file_size:
                    chunk = sock.recv(min(8192, file_size - received))
                    if not chunk:
                        break
                    f.write(chunk)
                    received += len(chunk)
                    progress = int((received / file_size) * 100)
                    self.progress.emit(progress)
            
            sock.close()
            
            if received == file_size:
                self.finished.emit(f"File '{self.filename}' downloaded successfully!")
            else:
                self.error.emit("Incomplete file transfer")
                
        except socket.timeout:
            self.error.emit("Connection timeout")
        except socket.error as e:
            self.error.emit(f"Connection error: {str(e)}")
        except Exception as e:
            self.error.emit(f"Error: {str(e)}")

class ModernFileServerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.host = "localhost"
        self.port = 8080
        self.sock = None
        self.transfer_thread = None
        self.initUI()
        self.applyModernStyle()

    def initUI(self):
        self.setWindowTitle("Multi-Node Parallel File Server - Client")
        self.setGeometry(100, 100, 1000, 700)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel("📁 Parallel File Server Client")
        header.setFont(QFont("Segoe UI", 24, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("color: #2c3e50; padding: 10px;")
        main_layout.addWidget(header)
        
        # Connection panel
        conn_frame = QFrame()
        conn_frame.setFrameStyle(QFrame.StyledPanel)
        conn_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db, stop:1 #2980b9);
                border-radius: 10px;
                padding: 15px;
            }
        """)
        conn_layout = QHBoxLayout(conn_frame)
        
        self.host_label = QLabel("Host:")
        self.host_label.setStyleSheet("color: white; font-weight: bold; font-size: 12px;")
        self.host_input = QTextEdit()
        self.host_input.setMaximumHeight(35)
        self.host_input.setPlainText("localhost")
        self.host_input.setStyleSheet("""
            QTextEdit {
                background: white;
                border: 2px solid #ecf0f1;
                border-radius: 5px;
                padding: 5px;
                font-size: 12px;
            }
        """)
        
        self.port_label = QLabel("Port:")
        self.port_label.setStyleSheet("color: white; font-weight: bold; font-size: 12px;")
        self.port_input = QTextEdit()
        self.port_input.setMaximumHeight(35)
        self.port_input.setPlainText("8080")
        self.port_input.setStyleSheet("""
            QTextEdit {
                background: white;
                border: 2px solid #ecf0f1;
                border-radius: 5px;
                padding: 5px;
                font-size: 12px;
            }
        """)
        
        self.connect_btn = QPushButton("🔌 Connect")
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background: #27ae60;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 20px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #229954;
            }
            QPushButton:pressed {
                background: #1e8449;
            }
        """)
        self.connect_btn.clicked.connect(self.connectToServer)
        
        conn_layout.addWidget(self.host_label)
        conn_layout.addWidget(self.host_input)
        conn_layout.addWidget(self.port_label)
        conn_layout.addWidget(self.port_input)
        conn_layout.addWidget(self.connect_btn)
        conn_layout.addStretch()
        
        main_layout.addWidget(conn_frame)
        
        # Splitter for file list and log
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - File list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        file_header = QLabel("📋 Available Files")
        file_header.setFont(QFont("Segoe UI", 14, QFont.Bold))
        file_header.setStyleSheet("color: #34495e; padding: 5px;")
        left_layout.addWidget(file_header)
        
        self.file_list = QListWidget()
        self.file_list.setStyleSheet("""
            QListWidget {
                background: white;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                padding: 5px;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #ecf0f1;
            }
            QListWidget::item:hover {
                background: #e8f4f8;
            }
            QListWidget::item:selected {
                background: #3498db;
                color: white;
            }
        """)
        left_layout.addWidget(self.file_list)
        
        # File operations buttons
        btn_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setStyleSheet(self.getButtonStyle("#3498db"))
        self.refresh_btn.clicked.connect(self.refreshFileList)
        self.refresh_btn.setEnabled(False)
        
        self.download_btn = QPushButton("⬇️ Download")
        self.download_btn.setStyleSheet(self.getButtonStyle("#27ae60"))
        self.download_btn.clicked.connect(self.downloadFile)
        self.download_btn.setEnabled(False)
        
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(self.download_btn)
        left_layout.addLayout(btn_layout)
        
        splitter.addWidget(left_panel)
        
        # Right panel - Log and progress
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        log_header = QLabel("📊 Activity Log")
        log_header.setFont(QFont("Segoe UI", 14, QFont.Bold))
        log_header.setStyleSheet("color: #34495e; padding: 5px;")
        right_layout.addWidget(log_header)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background: #2c3e50;
                color: #ecf0f1;
                border: 2px solid #34495e;
                border-radius: 8px;
                padding: 10px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
            }
        """)
        right_layout.addWidget(self.log_text)
        
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
        right_layout.addWidget(self.progress_bar)
        
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(splitter)
        
        self.log("Application started. Connect to server to begin.")

    def getButtonStyle(self, color):
        darker = self.darkenColor(color)
        return f"""
            QPushButton {{
                background: {color};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: {darker};
            }}
            QPushButton:pressed {{
                background: {self.darkenColor(darker)};
            }}
            QPushButton:disabled {{
                background: #95a5a6;
            }}
        """

    def darkenColor(self, hex_color):
        # Simple color darkening
        color_map = {
            "#3498db": "#2980b9",
            "#27ae60": "#229954",
            "#e74c3c": "#c0392b"
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
        self.log_text.append(f"[{self.getTimestamp()}] {message}")
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    def getTimestamp(self):
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")

    def connectToServer(self):
        try:
            self.host = self.host_input.toPlainText().strip()
            self.port = int(self.port_input.toPlainText().strip())
            
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
            self.download_btn.setEnabled(True)
            self.refreshFileList()
            
        except Exception as e:
            self.log(f"Connection failed: {str(e)}")
            QMessageBox.critical(self, "Connection Error", 
                               f"Failed to connect to server:\n{str(e)}")
            if self.sock:
                self.sock.close()
                self.sock = None

    def refreshFileList(self):
        if not self.sock:
            self.log("Not connected to server")
            return
        
        try:
            self.sock.sendall(b"LIST\n")
            response = b""
            while b"\n" not in response:
                chunk = self.sock.recv(1024)
                if not chunk:
                    break
                response += chunk
            
            files = response.decode().strip().split('\n')
            self.file_list.clear()
            
            if files and files[0] and files[0] != "NO_FILES":
                for file in files:
                    if file:
                        self.file_list.addItem(file)
                self.log(f"Retrieved {len(files)} file(s) from server")
            else:
                self.log("No files available on server")
                
        except Exception as e:
            self.log(f"Error refreshing file list: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to refresh file list:\n{str(e)}")

    def downloadFile(self):
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a file to download")
            return
        
        filename = selected_items[0].text()
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save File", filename, "All Files (*)"
        )
        
        if not save_path:
            return
        
        self.log(f"Downloading '{filename}'...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.download_btn.setEnabled(False)
        
        self.transfer_thread = FileTransferThread(
            self.host, self.port, filename, save_path
        )
        self.transfer_thread.progress.connect(self.progress_bar.setValue)
        self.transfer_thread.finished.connect(self.onDownloadFinished)
        self.transfer_thread.error.connect(self.onDownloadError)
        self.transfer_thread.start()

    def onDownloadFinished(self, message):
        self.log(message)
        self.progress_bar.setVisible(False)
        self.download_btn.setEnabled(True)
        QMessageBox.information(self, "Success", message)

    def onDownloadError(self, error):
        self.log(f"Download error: {error}")
        self.progress_bar.setVisible(False)
        self.download_btn.setEnabled(True)
        QMessageBox.critical(self, "Download Error", error)

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
    
    window = ModernFileServerGUI()
    window.show()
    
    sys.exit(app.exec_())

