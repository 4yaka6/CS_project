import asyncio
import os
import struct
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton, QListWidget, QLabel, \
    QHBoxLayout, QMessageBox, QFileDialog
import subprocess

# 下载路径
DOWNLOAD_PATH = os.path.join(os.path.abspath('.'), 'download')  # 当前目录作为下载路径
chunk_size = 4096  # 每次读取的数据块大小

async def recv_packet(reader, chunk_size=4096):
    """
    接收数据，解析长度前缀。数据分块接收。
    """
    length_prefix = await reader.read(4)
    if not length_prefix or len(length_prefix) < 4:
        return None

    length = struct.unpack('!I', length_prefix)[0]
    if length == 0:
        return b''  # 表示传输结束

    data = b''
    while len(data) < length:
        chunk = await reader.read(min(chunk_size, length - len(data)))
        if not chunk:
            return None
        data += chunk

    return data


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

        self.reader = None
        self.writer = None
        self.server_ip = None

    def connect_to_server(self):
        self.server_ip = self.server_ip_input.text()
        if self.server_ip:
            asyncio.run(self.fetch_file_list(self.server_ip))

    async def fetch_file_list(self, server_ip):
        try:
            # 使用 asyncio 创建连接
            self.reader, self.writer = await asyncio.open_connection(self.server_ip, 8888)

            self.show_message("Connection Successful", f"Connected to {server_ip}")

            # 请求文件列表
            self.writer.write(b"LIST_FILES")
            await self.writer.drain()  # 确保数据已经发送

            # 接收文件列表
            data = await self.reader.read(1024)
            files = data.decode().splitlines()

            self.file_list_widget.clear()
            self.file_list_widget.addItems(files)
        except Exception as e:
            self.show_message("Connection Failed", f"Could not connect to {server_ip}: {e}")
        finally:
            if self.writer:
                self.writer.close()
                await self.writer.wait_closed()

    def download_file(self):
        selected_file = self.file_list_widget.currentItem().text()
        if selected_file:
            self.file_info_text.setText(f"Downloading {selected_file}")
            asyncio.run(self.download_file_from_server(selected_file))

    async def download_file_from_server(self, filename):
        try:
            # 使用 asyncio 创建连接
            self.reader, self.writer = await asyncio.open_connection(self.server_ip, 8888)

            # 请求文件下载
            self.writer.write(f"DOWNLOAD {filename}".encode())
            await self.writer.drain()

            # 接收文件数据
            file_path = os.path.join(DOWNLOAD_PATH, filename)
            await self.receive_file(file_path)

            # 显示成功信息
            self.show_message("Download Complete", f"{filename} has been downloaded successfully.")

        except Exception as e:
            self.show_message("Download Failed", f"Failed to download {filename}: {e}")
        finally:
            if self.writer:
                self.writer.close()
                await self.writer.wait_closed()

    async def receive_file(self, file_path):
        """接收文件并保存到指定路径"""
        try:
            with open(file_path, 'wb') as f:
                while True:
                    try:
                        # 使用 recv_packet 函数接收数据块
                        data = await recv_packet(self.reader, chunk_size)
                        if data is None:
                            raise Exception("Error receiving data or connection lost.")

                        # 如果接收到的是空字节串，表示传输结束
                        if data == b'':
                            break

                        # 写入文件
                        f.write(data)

                    except Exception as e:
                        print(f"Error receiving file: {e}")
                        break  # 如果有错误，跳出循环

        except Exception as e:
            print(f"Error writing file: {e}")

    def disconnect_from_server(self):
        if self.writer:
            self.writer.close()
            asyncio.run(self.writer.wait_closed())
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
