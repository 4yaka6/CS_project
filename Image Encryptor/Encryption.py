import os
import random
import string
import math
from PIL import Image
import numpy as np

BLOCK_SIZE = 12  # 每个图像块的大小
RANGE = 8        # 可调交换范围（1~8）
KEY_LENGTH = 16  # 密钥长度


def key_to_seed(key: str):
    """将密钥转换为随机种子"""
    return sum(ord(c) for c in key)


def generate_key(length=KEY_LENGTH):
    """生成指定长度的密钥"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def pad_image(arr, block_size):
    """将图像填充到 block_size 的倍数"""
    h, w, c = arr.shape
    new_h = math.ceil(h / block_size) * block_size
    new_w = math.ceil(w / block_size) * block_size
    padded = np.zeros((new_h, new_w, c), dtype=np.uint8)
    padded[:h, :w] = arr
    return padded


def encrypt_image(image_path, key, block_size=BLOCK_SIZE, swap_range=RANGE):
    """图像加密函数"""
    img = Image.open(image_path).convert('RGB')
    arr = np.array(img)
    arr = pad_image(arr, block_size)

    h, w, _ = arr.shape
    num_y = h // block_size
    num_x = w // block_size

    encrypted = np.array(arr)
    random.seed(key_to_seed(key))

    for i in range(num_y):
        for j in range(num_x):
            # 随机在指定范围内选择另一个块
            dy = random.randint(-swap_range, swap_range)
            dx = random.randint(-swap_range, swap_range)
            y2 = min(max(i + dy, 0), num_y - 1)
            x2 = min(max(j + dx, 0), num_x - 1)

            # 块交换
            y1s, y2s = i * block_size, y2 * block_size
            x1s, x2s = j * block_size, x2 * block_size
            temp = np.copy(encrypted[y1s:y1s+block_size, x1s:x1s+block_size])
            encrypted[y1s:y1s+block_size, x1s:x1s+block_size] = encrypted[y2s:y2s+block_size, x2s:x2s+block_size]
            encrypted[y2s:y2s+block_size, x2s:x2s+block_size] = temp

    encrypted_img = Image.fromarray(encrypted)
    output_path = os.path.splitext(image_path)[0] + "_encrypted.png"
    encrypted_img.save(output_path)
    print(f"✅ 加密完成：{output_path}")
    print(f"🔑 密钥（请妥善保存）：{key}")


def main():
    files = [f for f in os.listdir('.') if f.lower().endswith(('.png', '.jpg', '.jpeg')) and not f.endswith('_encrypted.png')]
    if not files:
        print("❌ 当前目录下没有可加密的图片。")
        return

    print("📂 可选图片列表：")
    for i, f in enumerate(files):
        print(f"{i + 1}. {f}")

    idx = int(input("请输入要加密的图片编号：")) - 1
    if idx < 0 or idx >= len(files):
        print("❌ 无效选择。")
        return

    key = generate_key()
    encrypt_image(files[idx], key)


if __name__ == "__main__":
    main()
