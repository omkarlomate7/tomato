from cryptography.fernet import Fernet
import os


def generate_key():
    key = Fernet.generate_key()
    with open('secret.key', 'wb') as key_file:
        key_file.write(key)
    print("Encryption key has been generated and saved as 'secret.key'.")


def load_key():
    return open('secret.key', 'rb').read()


def encrypt_data(data):
    key = load_key()
    fernet = Fernet(key)
    encrypted = fernet.encrypt(data.encode())
    return encrypted

def decrypt_data(encrypted_data):
    key = load_key()
    fernet = Fernet(key)
    decrypted = fernet.decrypt(encrypted_data.encode())
    return decrypted.decode()
