# GUI Encryptor/Decryptor

**Just download `gui.exe` to use all the features of this project.**

---

## Introduction
The encryptor can choose the key length and randomly generate a key. The level of blurring in the encrypted image can be controlled by adjusting parameters. The encrypted image can bypass AI moderation while still allowing the human eye to recognize the original content.  
The decryptor only needs to provide the corresponding image and key in the program to recover the original image.

---

## Encryption Principle
The image is divided into fixed-size blocks, and pixel blocks within each block are swapped according to the key.

---

## Parameter Guide
- **block_size**: the size of each block.  
- **range**: the swap range. For example, if this value is 4, each selected pixel will only swap with blocks within a 4×4 area around its center. Valid range: `[1,8]`.  
- **key length**: default is 16. This cannot be modified in the GUI. To change it, modify the `Encryption.py` file.