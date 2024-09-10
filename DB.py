import json
import random
import psycopg2

# Connect to PostgreSQL database
conn = psycopg2.connect(
    host="localhost",
    database="tomato_db",
    user="postgres",
    password="4445"
)

cur = conn.cursor()

# Load the restaurant data from the JSON file
with open('pune_restaurants_with_id.json', 'r') as file:
    restaurant_data = json.load(file)

# List of Indian dishes
indian_dishes = [
    "Butter Chicken", "Paneer Tikka", "Masala Dosa", "Chicken Biryani", 
    "Pav Bhaji", "Chole Bhature", "Rajma Rice", "Aloo Paratha", "Tandoori Chicken", 
    "Dal Makhani", "Samosa", "Vada Pav", "Kadhai Paneer", "Fish Curry", "Prawn Masala", 
    "Mutton Rogan Josh", "Chicken Kebab", "Vegetable Korma", "Hyderabadi Biryani", 
    "Bhindi Masala", "Palak Paneer", "Malai Kofta", "Roti", "Naan", "Jeera Rice"
]

# List of pizzas, burgers, and sandwiches
western_dishes = [
    "Cheese Pizza", "Pepperoni Pizza", "Veggie Pizza", "Margherita Pizza", 
    "BBQ Chicken Pizza", "Chicken Burger", "Veggie Burger", "Grilled Sandwich", 
    "Club Sandwich", "Cheeseburger", "Tuna Sandwich", "Ham and Cheese Sandwich", 
    "Chicken Wrap", "Falafel Wrap", "Grilled Panini", "Veggie Sub", "BLT Sandwich"
]

# Price range for dishes
price_range = [100, 150, 200, 250, 300, 350, 400, 450, 500]

# Categories based on restaurant name
pizza_burger_keywords = ["Pizza", "Burger", "Grill", "Bistro", "BBQ", "Cafe"]
indian_keywords = ["Spice", "Tandoor", "Biryani", "Curry", "Masala"]

# Generate 500 dishes by analyzing restaurant names
dish_id = 1
total_dishes = 500
generated_dishes = []

for restaurant in restaurant_data['restaurants']:
    restaurant_id = restaurant['id']
    restaurant_name = restaurant['name']
    
    # Determine the type of dishes the restaurant would serve
    if any(keyword in restaurant_name for keyword in pizza_burger_keywords):
        # Assign pizzas, burgers, and sandwiches to these restaurants
        dish_list = western_dishes
    elif any(keyword in restaurant_name for keyword in indian_keywords):
        # Assign Indian dishes to these restaurants
        dish_list = indian_dishes
    else:
        # Generic restaurants get a mix of both
        dish_list = indian_dishes + western_dishes

    # Randomly assign a number of dishes (between 5 and 10) to each restaurant
    num_dishes = random.randint(5, 10)
    selected_dishes = random.sample(dish_list, num_dishes)
    
    for dish_name in selected_dishes:
        dish_price = random.choice(price_range)  # Assign random price
        generated_dishes.append({
            "id": dish_id,
            "name": dish_name,
            "price": dish_price,
            "restaurant_id": restaurant_id
        })
        dish_id += 1
        
    # Stop once we reach 500 dishes
    if len(generated_dishes) >= total_dishes:
        break

# Insert the generated dishes into the PostgreSQL 'dishes' table
for dish in generated_dishes:
    cur.execute("""
        INSERT INTO dishes (id, name, price, restaurant_id)
        VALUES (%s, %s, %s, %s)
    """, (dish['id'], dish['name'], dish['price'], dish['restaurant_id']))

# Commit the transaction
conn.commit()

# Close the connection
cur.close()
conn.close()

print(f"Successfully inserted {len(generated_dishes)} dishes into the 'dishes' table!")
