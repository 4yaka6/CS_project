import sys
import torch
import numpy as np
import cv2
from PIL import Image
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
from torchvision import transforms
from CNN_train import EmotionClassifier  # 你的CNN训练模型

# 设备配置
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# 加载训练好的模型
def load_model(model_path):
    model = EmotionClassifier()  # 创建模型实例
    model.load_state_dict(torch.load(model_path, map_location=device))  # 加载模型权重
    model.to(device)
    model.eval()  # 切换为评估模式
    return model


# 将Pillow图像转换为QPixmap
def pil_to_qpixmap(pil_image):
    pil_image = pil_image.convert("RGB")  # 转换为RGB格式
    data = pil_image.tobytes("raw", "RGB")  # 转换为字节数据
    qimage = QImage(data, pil_image.width, pil_image.height, QImage.Format_RGB888)
    return QPixmap.fromImage(qimage)

def preprocess_image(image_path, max_size=(48, 48), quality=100):

    # 读取图像
    img = cv2.imread(image_path)
    if img is None:
        print("Error: Image not found!")
        return None


    # 转换为灰度图
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 转换为 PIL 图片以便进行后续处理
    img_pil = Image.fromarray(img_gray)

    # 进行压缩和调整大小
    img_resized = img_pil.resize(max_size, Image.Resampling.LANCZOS)

    # 转换为 Tensor 以便输入模型进行预测
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.5,), (0.5,))  # 使用标准化（均值0.5，标准差0.5）
    ])
    face_tensor = transform(img_resized).unsqueeze(0)  # 添加batch维度

    # 转化为 QPixmap 以便显示
    processed_image = pil_to_qpixmap(img_resized)

    return img, processed_image, face_tensor


# 创建 PyQt5 应用界面
class EmotionClassifierApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

        # 加载训练好的模型
        self.model_path = 'resultsave/cnnloss0.12acc5766.pth'  # 你训练好的模型路径
        self.model = load_model(self.model_path)

    def initUI(self):
        # 设置窗口
        self.setWindowTitle('Emotion Classifier')
        self.setGeometry(100, 100, 800, 600)

        # 创建布局
        layout = QVBoxLayout()

        # 创建显示原始和处理后图片的标签
        self.source_image_label = QLabel(self)
        self.processed_image_label = QLabel(self)
        self.result_label = QLabel("Prediction Result: ", self)

        # 创建上传图片按钮
        self.upload_button = QPushButton('Upload Image', self)
        self.upload_button.clicked.connect(self.upload_image)
        layout.addWidget(self.upload_button)

        # 创建标签显示原始图片和处理后图片的注释
        self.source_image_text = QLabel('Source Image', self)
        self.processed_image_text = QLabel('Processed Image', self)
        layout.addWidget(self.source_image_text)
        layout.addWidget(self.source_image_label)
        layout.addWidget(self.processed_image_text)
        layout.addWidget(self.processed_image_label)
        layout.addWidget(self.result_label)

        # 设置布局
        self.setLayout(layout)

    def upload_image(self):
        # 打开文件对话框，选择图片
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, 'Select Image', '', 'Images (*.png *.jpg *.bmp *.jpeg)',
                                                   options=options)

        if file_path:
            # 预处理图片并获得处理后的图像
            original_image, processed_image, face_tensor = preprocess_image(file_path)

            if original_image is None:
                self.source_image_label.setText("No face detected. Please upload a valid image.")
                self.processed_image_label.clear()
                self.result_label.setText("Prediction Result: No face detected")
                return

            # 显示原始图像
            pixmap = QPixmap(file_path)
            self.source_image_label.setPixmap(pixmap.scaled(400, 400, Qt.KeepAspectRatio))

            # 显示处理后的图像
            self.processed_image_label.setPixmap(processed_image.scaled(400, 400, Qt.KeepAspectRatio))

            # 进行情绪分类预测
            with torch.no_grad():
                face_tensor = face_tensor.to(device)
                output = self.model(face_tensor)  # 进行预测
                probabilities = torch.nn.functional.softmax(output, dim=1)  # 获取每个类别的概率

                # 获取预测结果
                predicted_class = torch.argmax(probabilities, dim=1).item()
                prediction = probabilities[0].cpu().numpy()  # 转为 CPU numpy 数组

                # 输出每个类别的概率
                class_names = ['angry', 'disgusted', 'fearful', 'happy', 'neutral', 'sad', 'surprised']
                result_text = f"Prediction: {class_names[predicted_class]} ({100 * prediction[predicted_class]:.2f}%)\n"
                for i, prob in enumerate(prediction):
                    result_text += f"{class_names[i]}: {100 * prob:.2f}%\n"

                self.result_label.setText(f"Prediction Result:\n{result_text}")


# 启动应用程序
def main():
    app = QApplication(sys.argv)
    ex = EmotionClassifierApp()
    ex.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
