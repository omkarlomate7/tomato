import psycopg2
import os
import random

# Database connection
conn = psycopg2.connect(
    dbname="tomato_db",  # Update with your DB name
    user="postgres",
    password="4445",
    host="localhost"
)
cur = conn.cursor()

# Function to get all image files (both .png and .jfif) from a folder
def get_images_from_folder(folder_path):
    # List all files in the folder and filter by .png and .jfif extensions
    return [f for f in os.listdir(folder_path) if f.endswith('.png') or f.endswith('.jfif')]

# Paths to static folder images
pizza_image_folder = r"C:\Users\PDB-User\Desktop\Tomato\static\images\burgers"
burger_image_folder = r"C:\Users\PDB-User\Desktop\Tomato\static\images\pizza"
samosa_image_folder = r"C:\Users\PDB-User\Desktop\Tomato\static\images\samosa"

# Get all pizza, burger, and samosa images (handling both .png and .jfif)
pizza_images = get_images_from_folder(pizza_image_folder)
burger_images = get_images_from_folder(burger_image_folder)
samosa_images = get_images_from_folder(samosa_image_folder)

# Function to assign images based on food name
def assign_images_by_name():
    # Fetch all dishes
    cur.execute("SELECT id, name FROM dishes")
    dishes = cur.fetchall()

    for dish in dishes:
        dish_id = dish[0]
        dish_name = dish[1].lower()  # Convert name to lowercase for easier matching

        # Assign pizza image if 'pizza' is in the name
        if "pizza" in dish_name and pizza_images:
            image = random.choice(pizza_images)
            image_path = f"/static/images/pizzas/{image}"
        # Assign burger image if 'burger' is in the name
        elif "burger" in dish_name and burger_images:
            image = random.choice(burger_images)
            image_path = f"/static/images/burgers/{image}"
        # Assign samosa image if 'samosa' is in the name
        elif "samosa" in dish_name and samosa_images:
            image = random.choice(samosa_images)
            image_path = f"/static/images/samosas/{image}"
        else:
            # If no match or no images available, skip updating this dish
            continue

        # Update the dish record with the image URL
        cur.execute("UPDATE dishes SET image_url = %s WHERE id = %s", (image_path, dish_id))

    # Commit the changes to the database
    conn.commit()

# Run the function to assign images
assign_images_by_name()

# Close the cursor and connection
cur.close()
conn.close()

print("Image assignment complete.")
