import os
import random
import math
from PIL import Image
import numpy as np

BLOCK_SIZE = 12
RANGE = 8  # 必须与加密时相同

def key_to_seed(key: str):
    return sum(ord(c) for c in key)

def pad_image(arr, block_size):
    h, w, c = arr.shape
    new_h = math.ceil(h / block_size) * block_size
    new_w = math.ceil(w / block_size) * block_size
    padded = np.zeros((new_h, new_w, c), dtype=np.uint8)
    padded[:h, :w] = arr
    return padded

def decrypt_image(image_path, key, block_size=BLOCK_SIZE, swap_range=RANGE):
    img = Image.open(image_path).convert('RGB')
    arr = np.array(img)
    arr = pad_image(arr, block_size)

    h, w, _ = arr.shape
    num_y = h // block_size
    num_x = w // block_size

    decrypted = np.array(arr)
    random.seed(key_to_seed(key))

    # 构建与加密相同的交换顺序
    swaps = []
    for i in range(num_y):
        for j in range(num_x):
            dy = random.randint(-swap_range, swap_range)
            dx = random.randint(-swap_range, swap_range)
            y2 = min(max(i + dy, 0), num_y - 1)
            x2 = min(max(j + dx, 0), num_x - 1)
            swaps.append(((i, j), (y2, x2)))

    # 解密时反向交换
    for (y1, x1), (y2, x2) in reversed(swaps):
        y1s, y2s = y1 * block_size, y2 * block_size
        x1s, x2s = x1 * block_size, x2 * block_size
        temp = np.copy(decrypted[y1s:y1s+block_size, x1s:x1s+block_size])
        decrypted[y1s:y1s+block_size, x1s:x1s+block_size] = decrypted[y2s:y2s+block_size, x2s:x2s+block_size]
        decrypted[y2s:y2s+block_size, x2s:x2s+block_size] = temp

    decrypted_img = Image.fromarray(decrypted)
    output_path = os.path.splitext(image_path)[0] + "_decrypted.png"
    decrypted_img.save(output_path)

def main():
    files = [f for f in os.listdir('.') if f.endswith('_encrypted.png')]

    print("📂 可选加密图片列表：")
    for i, f in enumerate(files):
        print(f"{i + 1}. {f}")

    idx = int(input("请输入要解密的图片编号：")) - 1
    if idx < 0 or idx >= len(files):
        print("❌ 无效选择。")
        return

    key = input("🔑 请输入密钥：")
    decrypt_image(files[idx], key)

if __name__ == "__main__":
    main()
