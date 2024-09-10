import psycopg2
import random
from datetime import datetime, timedelta

# Connect to PostgreSQL
connection = psycopg2.connect(
    dbname="tomato_db",
    user="postgres",
    password="4445",
    host="localhost",
    port="5432"
)
cursor = connection.cursor()

# Function to generate random sales data
def generate_sales_data(num_days, records_per_day):
    # Base sale date is today's date
    base_date = datetime.now()

    sales_data = []
    for day_offset in range(num_days):
        sale_date = base_date - timedelta(days=day_offset)
        
        for _ in range(records_per_day):
            # Random user ID (between 1 and 20 for example)
            user_id = random.randint(1, 20)
            
            # Random total price (between 1000 and 5000 for example)
            total_price = random.randint(1000, 5000)
            
            # Create sales data tuple
            sales_data.append((user_id, total_price, sale_date))
    
    return sales_data

# Function to insert sales data into the database
def insert_sales_data(sales_data):
    query = """
    INSERT INTO sales (user_id, total_price, sale_date) VALUES (%s, %s, %s)
    """
    
    cursor.executemany(query, sales_data)
    connection.commit()

# Generate sales data for the last 30 days with 25 records per day
sales_data = generate_sales_data(num_days=30, records_per_day=25)

# Insert the generated sales data into the database
insert_sales_data(sales_data)

# Close the database connection
cursor.close()
connection.close()

print("Sales data inserted successfully!")
