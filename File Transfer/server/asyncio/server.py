


import asyncio
import hashlib
import json
import os
import struct

import aiofiles

BUFFER_SIZE = 1024
SERVER_ADDRESS = ("0.0.0.0", 9000)
UPLOAD_DIR = "uploads"  # 用于存储上传的文件

# 确保上传目录存在
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def send_with_frame(writer, data):
    """发送带有封帧的数据"""
    data_length = len(data)
    frame_header = struct.pack("!I", data_length)  # 使用 4 字节表示长度
    writer.write(frame_header + data)
    await writer.drain()

async def recv_with_frame(reader):
    """接收带有封帧的数据"""
    frame_header = await reader.readexactly(4)  # 先接收 4 字节长度
    if not frame_header:
        return None
    data_length = struct.unpack("!I", frame_header)[0]  # 解码数据长度
    data = await reader.readexactly(data_length)  # 按长度读取完整数据
    return data

async def list_directory(path):
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


async def calculate_md5(file_path):
    """计算文件的 MD5"""
    hash_md5 = hashlib.md5()
    async with aiofiles.open(file_path, "rb") as f:
        while chunk := await f.read(4096):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


async def handle_client(reader, writer):
    """处理单个客户端请求"""
    peername = writer.get_extra_info("peername")
    print(f"Connected to {peername}")
    try:
        while True:
            data = await reader.read(BUFFER_SIZE)
            if not data:
                break

            message = data.decode()
            command, *args = message.split(" ", 1)

            if command == "LIST":
                path = args[0] if args else "."
                result = await list_directory(path)
                response = json.dumps(result)
                writer.write(response.encode())
                await writer.drain()

            elif command == "UPLOAD":
                file_name, file_size, file_md5 = args[0].split(" ", 2)
                file_size = int(file_size)
                file_path = os.path.join(UPLOAD_DIR, file_name)

                async with aiofiles.open(file_path, "wb") as f:
                    received_size = 0
                    while received_size < file_size:
                        chunk = await reader.read(min(BUFFER_SIZE, file_size - received_size))
                        if not chunk:
                            break
                        await f.write(chunk)
                        received_size += len(chunk)

                received_md5 = await calculate_md5(file_path)
                if received_md5 == file_md5:
                    writer.write(b"UPLOAD SUCCESS")
                    print(f"File {file_name} uploaded successfully.")
                else:
                    writer.write(b"UPLOAD FAILED")
                await writer.drain()

            elif command == "DOWNLOAD":
                # file_name = args[0]
                # file_path = os.path.join(UPLOAD_DIR, file_name)
                #
                # if not os.path.exists(file_path):
                #     await send_with_frame(writer, f"File {file_name} not found.".encode())
                #     continue
                #
                # file_size = os.path.getsize(file_path)
                # file_md5 = await calculate_md5(file_path)
                # header = f"{file_name} {file_size} {file_md5}".encode()
                # await send_with_frame(writer, header)
                #
                # async with aiofiles.open(file_path, "rb") as f:
                #     while chunk := await f.read(BUFFER_SIZE):
                #         await send_with_frame(writer, chunk)
                #
                # print(f"File {file_name} sent to {peername}.")
                file_name = args[0]
                file_path = os.path.join(UPLOAD_DIR, file_name)

                if not os.path.exists(file_path):
                    writer.write(f"File {file_name} not found.".encode())
                    await writer.drain()
                    continue

                file_size = os.path.getsize(file_path)
                file_md5 = await calculate_md5(file_path)
                writer.write(f"{file_name} {file_size} {file_md5}".encode())
                await writer.drain()

                async with aiofiles.open(file_path, "rb") as f:
                    while chunk := await f.read(BUFFER_SIZE):
                        writer.write(chunk)
                        await writer.drain()

                print(f"File {file_name} sent to {peername}.")


    except Exception as e:
        print(f"Error handling client {peername}: {e}")
    finally:
        print(f"Disconnected from {peername}")
        writer.close()
        await writer.wait_closed()


async def main():
    """启动基于 asyncio 的并发服务器"""
    server = await asyncio.start_server(handle_client, *SERVER_ADDRESS)

    addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets)
    print(f"Serving on {addrs}")

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())