import torch
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, classification_report
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
from EfficientNet_train import EmotionClassifier  # 导入训练模型类


# 设备配置
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# 加载模型
def load_model(model, model_path):
    # 加载训练好的模型权重
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()
    return model


# 数据预处理和增强
def get_test_loader():
    transform = transforms.Compose([
        transforms.Resize((224, 224)),  # EfficientNet 预期输入尺寸是 224x224
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])  # 使用ImageNet的均值和标准差
    ])

    # 加载test数据集
    test_dataset = datasets.ImageFolder(root='./datasets/train', transform=transform)

    # 使用DataLoader加载测试数据
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False, num_workers=4)

    return test_loader, test_dataset.classes  # 返回DataLoader和类标签


# 验证模型
def validate_model(model, test_loader, class_names):
    all_labels = []
    all_preds = []

    # 使用no_grad()来进行验证时不计算梯度
    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            _, preds = torch.max(outputs, 1)
            all_labels.extend(labels.cpu().numpy())
            all_preds.extend(preds.cpu().numpy())

    # 计算混淆矩阵和分类报告
    conf_matrix = confusion_matrix(all_labels, all_preds)

    # 打印分类报告
    print('Classification Report:')
    print(classification_report(all_labels, all_preds, target_names=class_names, zero_division=1))

    # 绘制混淆矩阵
    plt.figure(figsize=(8, 8))
    plt.imshow(conf_matrix, interpolation='nearest', cmap=plt.cm.Blues)
    plt.colorbar()

    # 添加标签
    tick_marks = np.arange(len(class_names))
    plt.xticks(tick_marks, class_names, rotation=45)
    plt.yticks(tick_marks, class_names)

    # 格式化显示混淆矩阵中的数值
    thresh = conf_matrix.max() / 2.
    for i in range(conf_matrix.shape[0]):
        for j in range(conf_matrix.shape[1]):
            plt.text(j, i, format(conf_matrix[i, j], 'd'),
                     horizontalalignment="center",
                     color="white" if conf_matrix[i, j] > thresh else "black")

    plt.xlabel('Predicted Label')
    plt.ylabel('True Label')
    plt.title('Confusion Matrix')
    plt.tight_layout()
    plt.show()


# 主函数
if __name__ == '__main__':
    # 加载模型
    model_path = 'model/emotion_classifier_epoch_51.pth'  # 选择适当的模型路径
    model = EmotionClassifier(num_classes=7)  # 创建模型实例
    model = load_model(model, model_path)  # 加载训练好的模型权重

    # 获取test数据加载器
    test_loader, class_names = get_test_loader()

    # 验证模型并输出结果
    validate_model(model, test_loader, class_names)
