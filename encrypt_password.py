import json
from config import encrypt_data, generate_key, load_key


def encrypt_and_update_password(plain_password):
    
    try:
        load_key() 
    except FileNotFoundError:
        print("Key not found. Generating new key...")
        generate_key()  

   
    encrypted_password = encrypt_data(plain_password)

    
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)

   
    config['database']['password'] = encrypted_password.decode()

    
    with open('config.json', 'w') as config_file:
        json.dump(config, config_file, indent=4)

    print("Password has been encrypted and updated in config.json.")

if __name__ == "__main__":
   
    plain_password = "4445"  
    encrypt_and_update_password(plain_password)
