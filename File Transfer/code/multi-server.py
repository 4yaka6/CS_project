import os
import socket
import threading

FILES_DIR = "files"  # 文件存储的文件夹
clients = set()  # 用于追踪连接的客户端

class Client:
    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr
        self.last_active_time = None


def handle_client(client_socket, client_addr):
    client = Client(client_socket, client_addr)
    clients.add(client)
    print(f"{client_addr} has connected.")
    print(f"Current clients: {len(clients)}")

    try:
        while True:
            # 接收客户端发送的数据
            data = client_socket.recv(100)
            if not data:  # 如果没有数据，说明客户端断开
                break

            message = data.decode()

            # 更新客户端最后活动时间
            client.last_active_time = threading.get_ident()

            # 处理不同的消息
            if message == "LIST_FILES":
                files = os.listdir(FILES_DIR)
                file_list = "\n".join(files)
                client_socket.sendall(file_list.encode())
            elif message.startswith("DOWNLOAD"):
                filename = message.split(" ")[1]
                file_path = os.path.join(FILES_DIR, filename)

                if os.path.exists(file_path):
                    print(f"Starting file download for {filename} to {client_addr}")
                    with open(file_path, 'rb') as f:
                        while chunk := f.read(4096):
                            packet_size = len(chunk)
                            header = packet_size.to_bytes(4, byteorder='big')
                            client_socket.sendall(header + chunk)
                    print(f"File {filename} sent successfully to {client_addr}")
                else:
                    client_socket.sendall(b"ERROR: File not found")
            else:
                client_socket.sendall(b"ERROR: Unknown command")

    except Exception as e:
        print(f"Error handling client {client_addr}: {e}")
    finally:
        print(f"{client_addr} has disconnected.")
        clients.remove(client)
        print(f"Current clients: {len(clients)}\n")

        try:
            client_socket.close()
        except Exception as e:
            print(f"Error closing connection: {e}")


def check_idle_connections():
    while True:
        # 检查空闲连接并关闭超时连接
        threading.Event().wait(60)  # 每60秒检查一次
        current_time = threading.get_ident()

        for client in list(clients):
            # 300秒空闲则断开连接
            if current_time - client.last_active_time > 300:
                print(f"Disconnecting idle client {client.addr}")
                try:
                    client.conn.close()
                    clients.remove(client)
                    print(f"Current clients: {len(clients)}")
                except Exception as e:
                    print(f"Error closing idle connection: {e}")


def start_server(host='127.0.0.1', port=8888):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(15)
    print(f"Server started on {host}:{port}")

    # 启动检查空闲连接的线程
    threading.Thread(target=check_idle_connections, daemon=True).start()

    while True:
        client_socket, client_addr = server_socket.accept()
        threading.Thread(target=handle_client, args=(client_socket, client_addr), daemon=True).start()


if __name__ == '__main__':
    start_server()
