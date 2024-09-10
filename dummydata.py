import random
from faker import Faker
import json

# Initialize Faker for Indian locale
fake = Faker('en_IN')

# Define roles (only regular users, except for the admin)
roles = ['User', 'Guest', 'Manager']

# Create a dictionary to hold user data
user_data = {
    "users": []
}

# Admin user data (as specified)
admin_user = {
    "id": 1,
    "username": "omkarlomate",
    "email": "omkarlomate123@gmail.com",
    "password": "4445@Ok",
    "role": "Admin"
}
user_data["users"].append(admin_user)

# Generate 24 Indian users
for i in range(2, 26):
    user = {
        "id": i,
        "username": fake.user_name(),
        "email": fake.email(),
        "password": fake.password(length=12),
        "role": random.choice(roles)
    }
    user_data["users"].append(user)

# Export the user data to a JSON file
json_filename = "indian_users_data.json"
with open(json_filename, "w") as json_file:
    json.dump(user_data, json_file, indent=4)

# Print out the user data for review (optional)
print(json.dumps(user_data, indent=4))
