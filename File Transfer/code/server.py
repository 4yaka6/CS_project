import asyncio
import os
import struct

FILES_DIR = os.path.join(os.path.abspath('.'), 'files')  # 文件存储的文件夹
clients = set()  # 用于追踪连接的客户端
chunk_size = 4096  # 分块大小


class Client:
    def __init__(self, writer, last_active_time):
        self.writer = writer
        self.last_active_time = last_active_time


async def send_file(writer, file_path):
    """分块发送文件"""
    with open(file_path, 'rb') as f:
        data = f.read()  # 读取整个文件内容
        length = len(data)  # 获取文件大小
        length_prefix = struct.pack('!I', length)  # 包头：使用网络字节序（big-endian）来存储长度

        # 先发送文件大小
        writer.write(length_prefix)
        await writer.drain()

        # 数据分块发送
        for i in range(0, length, chunk_size):
            writer.write(data[i:i + chunk_size])  # 按块发送数据
            await writer.drain()  # 确保每次写入的数据被发送

    print(f"File {file_path} sent successfully")


async def receive_message(reader, writer, client):
    """接收消息并处理"""
    data = await reader.read(100)
    if not data:  # 如果没有数据，说明客户端断开
        return None

    message = data.decode()
    # 更新客户端最后活动时间
    client.last_active_time = asyncio.get_event_loop().time()

    return message


async def handle_client(reader, writer):
    client_ip = writer.get_extra_info('peername')[0]
    client_port = writer.get_extra_info('peername')[1]

    # 创建客户端对象并添加到集合中
    client = Client(writer, asyncio.get_event_loop().time())
    clients.add(client)

    print(f"{client_ip}:{client_port} has connected.")
    print(f"Current clients: {len(clients)}")

    try:
        while True:
            message = await receive_message(reader, writer, client)

            # 处理不同的消息
            if message == "LIST_FILES":
                files = os.listdir(FILES_DIR)
                file_list = "\n".join(files)
                writer.write(file_list.encode())
                await writer.drain()
            elif message.startswith("DOWNLOAD"):
                filename = message.split(" ")[1]
                file_path = os.path.join(FILES_DIR, filename)

                if os.path.exists(file_path):
                    print(f"Starting file download for {filename} to {client_ip}:{client_port}")
                    await send_file(writer, file_path)
                else:
                    writer.write(b"ERROR: File not found")
                    await writer.drain()
            else:
                writer.write(b"ERROR: Unknown command")
                await writer.drain()

    except asyncio.CancelledError:
        pass
    finally:
        print(f"{client_ip}:{client_port} has disconnected.")
        clients.remove(client)
        print(f"Current clients: {len(clients)}\n")

        try:
            writer.close()
            await writer.wait_closed()
        except Exception as e:
            print(f"Error closing connection: {e}")


async def main():
    server = await asyncio.start_server(
        handle_client, '127.0.0.1', 8888)

    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr}')

    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    asyncio.run(main())
