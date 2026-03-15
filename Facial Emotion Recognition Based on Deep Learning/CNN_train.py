import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split
import torch.nn.functional as F
import os
import time
from torchvision import datasets, transforms
from datetime import timedelta
import matplotlib.pyplot as plt


# 模型定义
class EmotionClassifier(nn.Module):
    def __init__(self):
        super(EmotionClassifier, self).__init__()
        self.conv1 = nn.Conv2d(1, 32, 3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, 3, padding=1)
        self.conv3 = nn.Conv2d(64, 128, 3, padding=1)
        self.pool = nn.MaxPool2d(2, 2)
        self.fc1 = nn.Linear(128 * 6 * 6, 256)
        self.fc2 = nn.Linear(256, 7)
        self.dropout = nn.Dropout(0.5)

    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = self.pool(F.relu(self.conv3(x)))
        x = x.view(-1, 128 * 6 * 6)
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        return x


# 训练过程
def train_model():
    # 确保 result 和 model 文件夹存在
    if not os.path.exists('result'):
        os.makedirs('result')
    if not os.path.exists('model'):
        os.makedirs('model')

    # 数据预处理和增强
    transform = transforms.Compose([
        transforms.Resize((48, 48)),
        transforms.Grayscale(num_output_channels=1),
        transforms.ToTensor(),
        transforms.Normalize((0.5,), (0.5,))
    ])

    # 加载数据集
    full_dataset = datasets.ImageFolder(root='./datasets/train', transform=transform)

    # 分割数据集为训练集和验证集
    train_size = int(0.8 * len(full_dataset))
    validation_size = len(full_dataset) - train_size
    train_dataset, validation_dataset = random_split(full_dataset, [train_size, validation_size])

    # 初始化 DataLoader
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True, num_workers=4)
    validation_loader = DataLoader(validation_dataset, batch_size=32, shuffle=False, num_workers=4)

    # 初始化模型
    model = EmotionClassifier()
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)  # 初始学习率为0.001

    # 使用 CUDA
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    epochs = 60  # 总共训练60个epoch

    # 用于存储每个 epoch 的验证准确率、loss 和学习率
    validation_accuracies = []
    epoch_losses = []
    learning_rates = []

    # 记录训练开始时间
    start_time = time.time()

    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        epoch_start_time = time.time()  # 每个epoch开始时的时间

        # 根据epoch来动态调整学习率
        if epoch < 10:
            lr = 0.001
        else:
            lr = 0.0001

        # 更新优化器的学习率
        for param_group in optimizer.param_groups:
            param_group['lr'] = lr

        # 记录当前学习率
        learning_rates.append(lr)

        # 训练阶段
        for batch_idx, (inputs, labels) in enumerate(train_loader):
            inputs, labels = inputs.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()

        # 记录当前 epoch 的 loss
        epoch_losses.append(running_loss / len(train_loader))

        # 计算当前epoch的进度
        epoch_elapsed_time = time.time() - epoch_start_time
        epoch_elapsed_str = str(timedelta(seconds=int(epoch_elapsed_time)))

        # 每个epoch结束时评估模型的准确性
        model.eval()  # 进入评估模式
        correct = 0
        total = 0
        with torch.no_grad():  # 在验证阶段不计算梯度
            for inputs, labels in validation_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                _, predicted = torch.max(outputs.data, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()

        validation_accuracy = 100 * correct / total
        validation_accuracies.append(validation_accuracy)  # 记录当前 epoch 的准确率

        # 计算已消耗的时间（总训练时间）
        elapsed_time = time.time() - start_time
        elapsed_str = str(timedelta(seconds=int(elapsed_time)))

        # 显示当前 epoch 和进度条
        print(f"Epoch [{epoch + 1}/{epochs}], "
              f"Progress: {100 * (epoch + 1) / epochs:.2f}%, "
              f"Loss: {running_loss / len(train_loader):.4f}, "
              f"Validation Accuracy: {validation_accuracy:.2f}%, "
              f"Epoch Time: {epoch_elapsed_str}, "
              f"Elapsed Time: {elapsed_str}")

        # 保存每个 epoch 的模型
        torch.save(model.state_dict(), f'model/emotion_classifier_epoch_{epoch + 1}.pth')

    # 绘制训练 loss 和 epoch 的折线图
    plt.figure(figsize=(10, 6))
    plt.plot(range(1, epochs + 1), epoch_losses, marker='o', color='r', label='Training Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.title(f'Training Loss per Epoch (lr={learning_rates[0]:.5f})')
    plt.grid(True)
    plt.legend()
    plt.savefig('result/training_loss.png')
    plt.close()

    # 绘制验证准确率和 epoch 的折线图
    plt.figure(figsize=(10, 6))
    plt.plot(range(1, epochs + 1), validation_accuracies, marker='o', color='b', label='Validation Accuracy')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy (%)')
    plt.title(f'Validation Accuracy per Epoch (lr={learning_rates[0]:.5f})')
    plt.grid(True)
    plt.legend()
    plt.savefig('result/validation_accuracy.png')
    plt.close()

    # 输出精确度最高的模型的轮次
    best_epoch = validation_accuracies.index(max(validation_accuracies)) + 1
    print(f"The model with the highest accuracy is from epoch {best_epoch}.")


# 运行主训练函数
if __name__ == '__main__':
    train_model()
