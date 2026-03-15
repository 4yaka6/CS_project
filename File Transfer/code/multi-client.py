import sys
import os
import subprocess
import socket
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton, QListWidget, QLabel, \
    QHBoxLayout, QMessageBox, QFileDialog

# 下载路径
DOWNLOAD_PATH = os.path.join(os.path.abspath('.'), 'download')  # 当前目录作为下载路径

class ClientWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('File Transfer Client')
        self.setGeometry(500, 500, 800, 600)

        # Layouts
        self.layout = QVBoxLayout()
        self.input_layout = QHBoxLayout()
        self.file_list_layout = QVBoxLayout()

        # IP address input
        self.server_ip_input = QLineEdit(self)
        self.server_ip_input.setPlaceholderText('Enter Server IP')
        self.connect_button = QPushButton('Connect', self)
        self.connect_button.clicked.connect(self.connect_to_server)

        self.input_layout.addWidget(self.server_ip_input)
        self.input_layout.addWidget(self.connect_button)

        # File list display
        self.file_list_widget = QListWidget(self)
        self.file_info_label = QLabel('File Info:', self)
        self.file_info_text = QLabel('', self)
        self.download_button = QPushButton('Download', self)

        self.download_button.clicked.connect(self.download_file)

        # New buttons
        self.disconnect_button = QPushButton('Disconnect', self)
        self.disconnect_button.clicked.connect(self.disconnect_from_server)

        self.open_folder_button = QPushButton('Open Download Folder', self)
        self.open_folder_button.clicked.connect(self.open_download_folder)

        self.file_list_layout.addWidget(self.file_list_widget)
        self.file_list_layout.addWidget(self.file_info_label)
        self.file_list_layout.addWidget(self.file_info_text)
        self.file_list_layout.addWidget(self.download_button)
        self.file_list_layout.addWidget(self.disconnect_button)
        self.file_list_layout.addWidget(self.open_folder_button)

        # Adding layouts to the main layout
        self.layout.addLayout(self.input_layout)
        self.layout.addLayout(self.file_list_layout)

        self.setLayout(self.layout)

        self.server_socket = None
        self.server_ip = None

    def connect_to_server(self):
        self.server_ip = self.server_ip_input.text()
        if self.server_ip:
            # 启动线程去获取文件列表
            threading.Thread(target=self.fetch_file_list_thread, args=(self.server_ip,)).start()

    def fetch_file_list_thread(self, server_ip):
        """在独立线程中运行获取文件列表"""
        self.fetch_file_list(server_ip)

    def fetch_file_list(self, server_ip):
        try:
            # 创建 TCP 连接
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.connect((self.server_ip, 8888))

            self.show_message("Connection Successful", f"Connected to {server_ip}")

            # 请求文件列表
            self.server_socket.sendall(b"LIST_FILES")

            # 接收文件列表
            data = self.server_socket.recv(1024)
            files = data.decode().splitlines()

            self.file_list_widget.clear()
            self.file_list_widget.addItems(files)
        except Exception as e:
            self.show_message("Connection Failed", f"Could not connect to {server_ip}: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()

    def download_file(self):
        selected_file = self.file_list_widget.currentItem().text()
        if selected_file:
            self.file_info_text.setText(f"Downloading {selected_file}")
            # 启动线程进行文件下载
            threading.Thread(target=self.download_file_from_server_thread, args=(selected_file,)).start()

    def download_file_from_server_thread(self, filename):
        """在独立线程中进行文件下载"""
        self.download_file_from_server(filename)

    def download_file_from_server(self, filename):
        try:
            # 创建 TCP 连接
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.connect((self.server_ip, 8888))

            # 请求文件下载
            self.server_socket.sendall(f"DOWNLOAD {filename}".encode())

            # 接收文件数据
            file_path = os.path.join(DOWNLOAD_PATH, filename)
            with open(file_path, 'wb') as f:
                while True:
                    try:
                        # 首先接收4字节标头（数据包大小）
                        header = self.server_socket.recv(4)
                        if len(header) < 4:
                            # 标头不完整，表示传输结束
                            print("File transfer completed.")
                            break

                        # 获取数据包大小
                        packet_size = int.from_bytes(header, byteorder='big')

                        # 如果包大小为0，则表示文件接收完成
                        if packet_size == 0:
                            print("Received file successfully.")
                            break

                        # 接收文件数据块
                        data = self.server_socket.recv(packet_size)
                        if len(data) < packet_size:
                            raise Exception("Incomplete data received")

                        # 写入文件
                        f.write(data)

                    except Exception as e:
                        print(f"Error receiving file: {e}")
                        break  # 如果有错误，跳出循环

            # 显示成功信息
            self.show_message("Download Complete", f"{filename} has been downloaded successfully.")

        except Exception as e:
            self.show_message("Download Failed", f"Failed to download {filename}: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()

    def disconnect_from_server(self):
        if self.server_socket:
            self.server_socket.close()
            self.show_message("Disconnected", "You have disconnected from the server.")

    def open_download_folder(self):
        # Open the directory where files are downloaded
        subprocess.Popen(f'explorer {DOWNLOAD_PATH}')  # Open folder in Explorer (Windows)

    def show_message(self, title, message):
        """Display a message box with the given title and message."""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec_()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ClientWindow()
    window.show()
    sys.exit(app.exec_())
