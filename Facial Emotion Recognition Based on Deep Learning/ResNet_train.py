import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split
from torchvision import datasets, transforms, models
import os
import time
from datetime import timedelta
import matplotlib.pyplot as plt

# 重要性池化
class ImportancePooling(nn.Module):
    def __init__(self):
        super(ImportancePooling, self).__init__()

    def forward(self, x, importance_map):
        # 计算重要性池化的输出
        importance_map_exp = torch.exp(importance_map)  # 通过指数计算提高重要性
        weighted_features = x * importance_map_exp  # 将特征图与重要性进行加权

        # 对加权后的特征进行池化（这里使用全局平均池化）
        pooled_features = torch.sum(weighted_features, dim=[2, 3]) / torch.sum(importance_map_exp, dim=[2, 3])

        return pooled_features


# 通道注意力模块
class ChannelAttention(nn.Module):
    def __init__(self, in_channels):
        super(ChannelAttention, self).__init__()
        # 修改卷积层的输入和输出通道数
        self.conv1 = nn.Conv2d(in_channels * 2, in_channels // 16, kernel_size=1)  # 输入通道是原始的两倍
        self.conv2 = nn.Conv2d(in_channels // 16, in_channels, kernel_size=1)

    def forward(self, x):
        # 使用全局平均池化
        avg_pool = torch.mean(x, dim=[2, 3], keepdim=True)  # 保持空间维度为 1x1

        # 使用最大池化（修正之前的错误）
        max_pool, _ = torch.max(x, dim=2, keepdim=True)  # 沿着高度维度做池化
        max_pool, _ = torch.max(max_pool, dim=3, keepdim=True)  # 再沿着宽度维度做池化

        # 拼接通道注意力
        pooled = torch.cat([avg_pool, max_pool], dim=1)  # 拼接池化结果（通道数为原来的2倍）

        # 通过卷积生成通道注意力
        attention = self.conv2(torch.relu(self.conv1(pooled)))
        attention = torch.sigmoid(attention)

        return x * attention


# 空间注意力模块
class SpatialAttention(nn.Module):
    def __init__(self):
        super(SpatialAttention, self).__init__()
        self.conv1 = nn.Conv2d(2, 1, kernel_size=7, padding=3)

    def forward(self, x):
        avg_pool = torch.mean(x, dim=1, keepdim=True)
        max_pool, _ = torch.max(x, dim=1, keepdim=True)

        pooled = torch.cat([avg_pool, max_pool], dim=1)

        attention = self.conv1(pooled)
        attention = torch.sigmoid(attention)

        return x * attention


# CBAM模块：结合通道注意力和空间注意力
class CBAM(nn.Module):
    def __init__(self, in_channels):
        super(CBAM, self).__init__()
        self.channel_attention = ChannelAttention(in_channels)
        self.spatial_attention = SpatialAttention()

    def forward(self, x):
        x = self.channel_attention(x)
        x = self.spatial_attention(x)
        return x


# 使用预训练的ResNet模型，并冻结卷积层，最后添加CBAM注意力模块
class EmotionClassifier(nn.Module):
    def __init__(self):
        super(EmotionClassifier, self).__init__()
        # 使用预训练的ResNet50模型
        self.resnet = models.resnet50(weights='IMAGENET1K_V1')

        # 获取ResNet50的最后一层卷积层的输出通道数
        last_conv_channels = self.resnet.layer4[2].conv3.out_channels  # 获取最后一个卷积层输出通道数

        # 加入CBAM模块，应用到最后一个卷积层
        self.cbam = CBAM(last_conv_channels)

        # 修改全连接层，7个输出对应7种情绪
        self.resnet.fc = nn.Linear(self.resnet.fc.in_features, 7)

    def forward(self, x):
        # 通过ResNet模型
        x = self.resnet.conv1(x)
        x = self.resnet.bn1(x)
        x = self.resnet.relu(x)
        x = self.resnet.maxpool(x)

        x = self.resnet.layer1(x)
        x = self.resnet.layer2(x)
        x = self.resnet.layer3(x)

        # 在最后一个卷积层应用CBAM注意力机制
        x = self.resnet.layer4(x)
        x = self.cbam(x)  # 应用CBAM注意力

        # 将特征图展平并通过全连接层进行分类
        x = self.resnet.avgpool(x)
        x = torch.flatten(x, 1)
        x = self.resnet.fc(x)

        return x


def repeat_channels(x):
    # 将图像转换为 3 通道
    return x.repeat(3, 1, 1)


# 训练过程
def train_model():
    # 确保 result 和 model 文件夹存在
    if not os.path.exists('result'):
        os.makedirs('result')
    if not os.path.exists('model'):
        os.makedirs('model')

    # 数据预处理和增强
    transform = transforms.Compose([
        transforms.Resize((48, 48)),  # 调整图片大小
        transforms.Grayscale(num_output_channels=1),  # 转换为灰度图像
        transforms.ToTensor(),  # 转换为 Tensor
        transforms.Lambda(repeat_channels),  # 将灰度图像转换为 3 通道
        transforms.RandomRotation(40),  # 随机旋转 - 最大旋转角度为 40 度
        transforms.RandomAffine(degrees=0, translate=(0.2, 0.2)),  # 随机水平和竖直偏移
        transforms.RandomHorizontalFlip(),  # 随机水平翻转
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))  # 正则化，归一化到 [-1, 1] 区间
    ])

    # 加载数据集
    full_dataset = datasets.ImageFolder(root='./datasets/train', transform=transform)

    # 分割数据集为训练集和验证集
    train_size = int(0.8 * len(full_dataset))
    validation_size = len(full_dataset) - train_size
    train_dataset, validation_dataset = random_split(full_dataset, [train_size, validation_size])

    # 初始化 DataLoader
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True, num_workers=0)
    validation_loader = DataLoader(validation_dataset, batch_size=32, shuffle=False, num_workers=0)

    # 初始化模型
    model = EmotionClassifier()
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(model.parameters(), lr=0.001, momentum=0.7)  # 使用SGD优化器并传入momentum

    # 检查是否有可用的 CUDA 设备
    if torch.cuda.is_available():
        # 获取当前可用的 CUDA 设备，并输出设备名称
        device = torch.device("cuda")
        device_name = torch.cuda.get_device_name(device)
        print(f"Training will be done on CUDA device: {device_name}")
    else:
        # 如果没有 CUDA 设备，则打印警告并停止训练
        print("CUDA is not available. Please ensure a CUDA-enabled GPU is present. Training will not proceed.")
        exit()  # 停止程序

    # 将模型转移到 CUDA 设备
    model.to(device)

    epochs = 100  # 总共训练100个epoch

    # 用于存储每个 epoch 的验证准确率、loss 和学习率
    validation_accuracies = []
    epoch_losses = []
    learning_rates = []

    # 记录训练开始时间
    start_time = time.time()

    best_model = None  # 用于保存当前准确率最高的模型
    best_accuracy = 0  # 用于记录当前的最佳准确率

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

        # 判断是否是当前最佳模型，如果是，保存模型
        if validation_accuracy > best_accuracy:
            best_accuracy = validation_accuracy
            best_model = model.state_dict()  # 记录当前最佳模型的权重

        # 每10轮保存一次最好的模型
        if (epoch + 1) % 10 == 0:
            if best_model is not None:
                torch.save(best_model, f'model/best_emotion_classifier_epoch_{epoch + 1}.pth')

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
