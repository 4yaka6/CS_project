

import hashlib
import os
import struct
import sys
import socket
import json
import warnings

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QListWidget, QLabel, QMessageBox, QListWidgetItem, QFileDialog,
    QLineEdit
)
from PyQt5.QtGui import QIcon

SERVER_ADDRESS = ("127.0.0.1", 9000)
BUFFER_SIZE = 1024
UPLOAD_DIR = "../server/multiprocess/uploads"  # 本地上传目录


def calculate_md5(file_path):
    """计算文件的MD5"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def send_with_frame(sock, data):
    """发送带有封帧的数据"""
    data_length = len(data)
    frame_header = struct.pack("!I", data_length)  # 使用 4 字节表示长度
    sock.sendall(frame_header + data)

def recv_with_frame(sock):
    """接收带有封帧的数据"""
    frame_header = sock.recv(4)  # 先接收 4 字节长度
    if not frame_header:
        return None
    data_length = struct.unpack("!I", frame_header)[0]  # 解码数据长度
    data = b""
    while len(data) < data_length:
        chunk = sock.recv(data_length - len(data))
        if not chunk:
            break
        data += chunk
    return data

class RemoteFileBrowser(QWidget):
    def __init__(self):
        super().__init__()
        self.sock = None
        self.current_path = "../"
        self.server_address = ("127.0.0.1", 9000)  # 默认地址
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Remote File Browser")
        self.setGeometry(300, 300, 600, 400)

        layout = QVBoxLayout()

        # 输入IP和端口的区域
        self.ip_label = QLabel("Server IP:")
        self.ip_input = QLineEdit(self)
        self.ip_input.setText(self.server_address[0])  # 设置默认IP
        layout.addWidget(self.ip_label)
        layout.addWidget(self.ip_input)

        self.port_label = QLabel("Server Port:")
        self.port_input = QLineEdit(self)
        self.port_input.setText(str(self.server_address[1]))  # 设置默认端口
        layout.addWidget(self.port_label)
        layout.addWidget(self.port_input)

        # 连接按钮
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect_to_server)
        layout.addWidget(self.connect_button)

        # 当前路径标签
        self.path_label = QLabel(f"Current Path: {self.current_path}")
        layout.addWidget(self.path_label)

        # 文件列表
        self.file_list = QListWidget()
        self.file_list.itemDoubleClicked.connect(self.navigate_directory)
        layout.addWidget(self.file_list)

        # 返回上级目录按钮
        self.up_button = QPushButton("Up One Level")
        self.up_button.clicked.connect(self.go_up_one_level)
        layout.addWidget(self.up_button)

        # 刷新按钮
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_file_list)
        layout.addWidget(self.refresh_button)

        # 上传文件按钮
        self.upload_button = QPushButton("Upload File")
        self.upload_button.clicked.connect(self.upload_file)
        layout.addWidget(self.upload_button)

        # 下载文件按钮
        self.download_button = QPushButton("Download File")
        self.download_button.clicked.connect(self.download_file)
        layout.addWidget(self.download_button)

        self.setLayout(layout)

        # 设置整体样式
        self.setStyleSheet("""
                    QWidget {
                        background-color: #eaeaea;
                        font-family: 'Arial', sans-serif;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                    QLabel {
                        font-family: 'Arial', sans-serif;
                    }
                """)

        # 初始加载文件列表
        self.refresh_file_list()

    def connect_to_server(self):
        """连接到服务器"""
        ip = self.ip_input.text()
        port = self.port_input.text()

        if not ip or not port:
            QMessageBox.critical(self, "Error", "IP or Port is empty.")
            return

        try:
            port = int(port)
            self.server_address = (ip, port)
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # self.sock.settimeout(3)  # 设置超时时间，避免卡死
            self.sock.connect(SERVER_ADDRESS)
            QMessageBox.information(self, "Info", f"Connected to {ip}:{port}")
            self.refresh_file_list()  # 连接成功后刷新文件列表
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to connect: {str(e)}")

    def send_command(self, command):
        if not self.sock:  # 如果socket还没初始化
            return None

        self.sock.sendall(command.encode())
        data = self.sock.recv(BUFFER_SIZE)
        return json.loads(data.decode())

    def refresh_file_list(self):
        if self.sock is None: return
        """刷新当前路径下的文件列表"""
        try:
            result = self.send_command(f"LIST {self.current_path}")
            if "error" in result:
                QMessageBox.critical(self, "Error", result["error"])
                return

            self.current_path = result["current_path"]
            self.path_label.setText(f"Current Path: {self.current_path}")

            self.file_list.clear()
            for item in result["items"]:
                list_item = QListWidgetItem()
                list_item.setText(item["name"])
                list_item.setData(Qt.UserRole, item["is_dir"])
                # 设置图标
                if item["is_dir"]:
                    list_item.setIcon(QIcon("icons/folder.png"))  # 目录图标
                else:
                    list_item.setIcon(QIcon("icons/file.png"))  # 文件图标

                self.file_list.addItem(list_item)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def navigate_directory(self, item):
        """双击进入目录"""
        if item.data(Qt.UserRole):
            dir_name = item.text()
            self.current_path = f"{self.current_path}/{dir_name}"
            self.refresh_file_list()
        else:
            QMessageBox.information(self, "Info", f"Selected file: {item.text()}")

    def go_up_one_level(self):
        """返回上一级目录"""
        self.current_path = "/".join(self.current_path.split("/")[:-1]) or "."
        self.refresh_file_list()

    def upload_file(self):
        """上传文件到服务器"""
        file_name, _ = QFileDialog.getOpenFileName(self, "Select a file to upload")
        if not file_name:
            return

        file_size = os.path.getsize(file_name)
        file_md5 = calculate_md5(file_name)
        self.sock.sendto(f"UPLOAD {os.path.basename(file_name)} {file_size} {file_md5}".encode(), self.server_address)

        with open(file_name, "rb") as f:
            while (data := f.read(BUFFER_SIZE)):
                self.sock.sendto(data, self.server_address)

        data, _ = self.sock.recvfrom(BUFFER_SIZE)
        if data.decode() == "UPLOAD SUCCESS":
            QMessageBox.information(self, "Success", "File uploaded successfully.")
            self.refresh_file_list()

    def download_file(self):
        """从服务器下载文件"""
        item = self.file_list.currentItem()
        if not item or item.data(Qt.UserRole):
            QMessageBox.critical(self, "Error", "Please select a file to download.")
            return
        file_name = self.current_path + '/' + item.text()

        # send_with_frame(self.sock,f"DOWNLOAD {file_name}".encode())
        self.sock.sendall(f"DOWNLOAD {file_name}".encode())  # 使用 sendall 发送数据
        data = self.sock.recv(BUFFER_SIZE) # 使用 recv 接收数据
        # data = recv_with_frame(self.socket)
        if data.decode().startswith("File not found"):
            QMessageBox.critical(self, "Error", data.decode())
            return
        file_info = data.decode().split(" ")
        file_size = int(file_info[1])
        file_md5 = file_info[2]
        save_path, _ = QFileDialog.getSaveFileName(self, "Save file", file_name)
        if not save_path:
            return

        with open(save_path, "wb") as f:
            received_size = 0
            while received_size < file_size:
                # file_data = recv_with_frame(self.socket)
                file_data, _ = self.sock.recvfrom(min(file_size - received_size, BUFFER_SIZE))
                f.write(file_data)
                received_size += len(file_data)

        received_md5 = calculate_md5(save_path)
        print(f"Received MD5: {received_md5}")
        if received_md5 == file_md5:
            QMessageBox.information(self, "Success", "File downloaded successfully.")
            print("File transfer successful.")
        else:
            QMessageBox.information(self, "Failed", "File downloaded failed.")
            print("File transfer failed. MD5 mismatch.")




if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=UserWarning, message=".*NSSavePanel.*")
    app = QApplication(sys.argv)

    # 设置图标资源路径
    app.setStyle("Fusion")

    browser = RemoteFileBrowser()
    browser.show()
    sys.exit(app.exec_())