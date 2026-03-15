#  我真诚地保证：
#  我自己独立地完成了整个程序从分析、设计到编码的所有工作。
#  如果在上述过程中，我遇到了什么困难而求教于人，那么，我将在程序实习报告中
#  详细地列举我所遇到的问题，以及别人给我的提示。
#  在此，我感谢 XXX, …, XXX对我的启发和帮助。下面的报告中，我还会具体地提到
#  他们在各个方法对我的帮助。
#  我的程序里中凡是引用到其他程序或文档之处，
#  例如教材、课堂笔记、网上的源代码以及其他参考书上的代码段,
#  我都已经在程序的注释里很清楚地注明了引用的出处。

#  我从未没抄袭过别人的程序，也没有盗用别人的程序，
#  不管是修改式的抄袭还是原封不动的抄袭。
#  我编写这个程序，从来没有想过要去破坏或妨碍其他计算机系统的正常运转。
#  <张刘骁>

import hashlib
import socket
import os
import json
import struct
import threading

BUFFER_SIZE = 1024
SERVER_ADDRESS = ("0.0.0.0", 9000)
UPLOAD_DIR = "uploads"  # 用于存储上传的文件

# 确保上传目录存在
os.makedirs(UPLOAD_DIR, exist_ok=True)
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


def list_directory(path):
    """列出指定目录下的文件和文件夹"""
    if not os.path.exists(path):
        return {"error": "Path does not exist.", "path": path}
    if not os.path.isdir(path):
        return {"error": "Path is not a directory.", "path": path}

    items = []
    for entry in os.listdir(path):
        entry_path = os.path.join(path, entry)
        items.append({
            "name": entry,
            "is_dir": os.path.isdir(entry_path)
        })
    return {"items": items, "current_path": os.path.abspath(path)}

def calculate_md5(file_path):
    """计算文件的MD5"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def handle_client(conn, addr):
    """处理单个客户端的请求"""
    print(f"Connected to {addr}")
    try:
        while True:
            data = conn.recv(BUFFER_SIZE).decode()
            if not data:
                break
            command, *args = data.split(" ", 1)

            if command == "LIST":
                path = args[0] if args else "."
                result = list_directory(path)
                conn.sendall(json.dumps(result).encode())

            elif command == "UPLOAD":
                file_name, file_size, file_md5 = args[0].split(" ", 2)
                file_size = int(file_size)
                file_path = os.path.join(UPLOAD_DIR, file_name)

                with open(file_path, "wb") as f:
                    received_size = 0
                    while received_size < file_size:
                        chunk = conn.recv(min(file_size - received_size, BUFFER_SIZE))
                        if not chunk:
                            break
                        f.write(chunk)
                        received_size += len(chunk)

                received_md5 = calculate_md5(file_path)
                if received_md5 == file_md5:
                    conn.sendall("UPLOAD SUCCESS".encode())
                    print(f"File {file_name} uploaded successfully.")
                else:
                    conn.sendall("UPLOAD FAILED".encode())

            elif command == "DOWNLOAD":
                file_name = args[0]
                file_path = os.path.join(UPLOAD_DIR, file_name)

                if not os.path.exists(file_path):
                    conn.sendall(f"File {file_name} not found.".encode())
                    continue

                file_size = os.path.getsize(file_path)
                file_md5 = calculate_md5(file_path)
                conn.sendall(f"{file_name} {file_size} {file_md5}".encode())

                with open(file_path, "rb") as f:
                    while (chunk := f.read(BUFFER_SIZE)):
                        conn.sendall(chunk)

                print(f"File {file_name} sent to {addr}.")

    except Exception as e:
        print(f"Error handling client {addr}: {e}")
    finally:
        conn.close()
        print(f"Disconnected from {addr}")

def start_server():
    """启动多线程TCP服务器"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
        server_sock.bind(SERVER_ADDRESS)
        server_sock.listen(5)
        print(f"Server listening on {SERVER_ADDRESS}")

        while True:
            conn, addr = server_sock.accept()
            print(f"Accepted connection from {addr}")
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.start()

if __name__ == "__main__":
    start_server()