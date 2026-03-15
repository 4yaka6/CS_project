# import tensorflow as tf
#
# def test_cuda():
#     if tf.config.list_physical_devices('GPU'):
#         print("CUDA is available. Your system can use GPU acceleration.")
#         physical_devices = tf.config.list_physical_devices('GPU')
#         for device in physical_devices:
#             print(f"Device name: {device.name}")
#     else:
#         print("CUDA is not available. Your system cannot use GPU acceleration.")
#
# if __name__ == "__main__":
#     test_cuda()
import torch

def test_cuda():
    if torch.cuda.is_available():
        print("CUDA is available. Your system can use GPU acceleration.")
        print(f"Device name: {torch.cuda.get_device_name(0)}")
        print(f"Total memory: {torch.cuda.get_device_properties(0).total_memory / 1024 ** 3:.2f} GB")
    else:
        print("CUDA is not available. Your system cannot use GPU acceleration.")

if __name__ == "__main__":
    test_cuda()