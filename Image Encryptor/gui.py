import sys
import os
import random
import math
import numpy as np
from PIL import Image
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog,
    QLineEdit, QSpinBox, QHBoxLayout, QMessageBox
)
from PyQt5.QtCore import Qt


def key_to_seed(key: str):
    return sum(ord(c) for c in key)


def pad_image(arr, block_size):
    """填充图像至 block_size 的倍数"""
    h, w, c = arr.shape
    new_h = math.ceil(h / block_size) * block_size
    new_w = math.ceil(w / block_size) * block_size
    padded = np.zeros((new_h, new_w, c), dtype=np.uint8)
    padded[:h, :w] = arr
    return padded


def decrypt_image(image_path, key, block_size, swap_range):
    """基于局部块交换的可逆解密算法"""
    img = Image.open(image_path).convert('RGB')
    arr = np.array(img)
    arr = pad_image(arr, block_size)

    h, w, _ = arr.shape
    num_y = h // block_size
    num_x = w // block_size

    decrypted = np.array(arr)
    random.seed(key_to_seed(key))

    # 构建与加密时相同的交换顺序
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
    return output_path


class DecryptApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔓 图像解密工具")
        self.setGeometry(400, 200, 400, 250)

        self.image_path = None

        layout = QVBoxLayout()

        # 图片选择
        self.file_label = QLabel("未选择图片")
        self.file_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.file_label)

        self.btn_select = QPushButton("选择加密图片")
        self.btn_select.clicked.connect(self.select_image)
        layout.addWidget(self.btn_select)

        # 参数输入
        param_layout = QHBoxLayout()
        layout.addLayout(param_layout)

        # Block Size
        self.block_label = QLabel("Block Size:")
        self.block_input = QSpinBox()
        self.block_input.setRange(4, 128)
        self.block_input.setValue(16)
        param_layout.addWidget(self.block_label)
        param_layout.addWidget(self.block_input)

        # Range
        self.range_label = QLabel("Range:")
        self.range_input = QSpinBox()
        self.range_input.setRange(1, 8)
        self.range_input.setValue(4)
        param_layout.addWidget(self.range_label)
        param_layout.addWidget(self.range_input)

        # Key
        key_layout = QHBoxLayout()
        layout.addLayout(key_layout)
        self.key_label = QLabel("Key:")
        self.key_input = QLineEdit()
        key_layout.addWidget(self.key_label)
        key_layout.addWidget(self.key_input)

        # 解密按钮
        self.btn_decrypt = QPushButton("开始解密")
        self.btn_decrypt.clicked.connect(self.run_decrypt)
        layout.addWidget(self.btn_decrypt)

        self.setLayout(layout)

    def select_image(self):
        file, _ = QFileDialog.getOpenFileName(self, "选择加密图片", "", "Images (*.png *.jpg *.jpeg)")
        if file:
            self.image_path = file
            filename = os.path.basename(file)
            self.file_label.setText(f"已选择：{filename}")

    def run_decrypt(self):
        if not self.image_path:
            QMessageBox.warning(self, "错误", "请先选择图片！")
            return
        key = self.key_input.text().strip()
        if not key:
            QMessageBox.warning(self, "错误", "请输入密钥！")
            return

        block_size = self.block_input.value()
        swap_range = self.range_input.value()

        try:
            output_path = decrypt_image(self.image_path, key, block_size, swap_range)
            QMessageBox.information(self, "完成", f"✅ 解密成功！\n文件已保存：\n{output_path}")
            os.startfile(os.path.dirname(output_path))  # 自动打开保存目录
        except Exception as e:
            QMessageBox.critical(self, "错误", f"解密失败：\n{e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = DecryptApp()
    win.show()
    sys.exit(app.exec_())
