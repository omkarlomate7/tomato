import psycopg2
from flask import Flask, render_template, request, flash, redirect, session, jsonify, url_for
import os
import random
import matplotlib.pyplot as plt
import io
import base64
import matplotlib
import json
from config import decrypt_data  
matplotlib.use('Agg')  
import numpy as np
from sklearn.linear_model import LinearRegression
from fuzzywuzzy import process 


app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['SECRET_KEY'] = '3505b29ab1897a46de35f444850271ac'



def get_db_config():
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
        config['database']['password'] = decrypt_data(config['database']['password'].encode())
    return config



def get_db_connection():
    
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)

   
    decrypted_password = decrypt_data(config['database']['password'])

   
    conn = psycopg2.connect(
        dbname=config['database']['dbname'],
        user=config['database']['user'],
        password=decrypted_password,  
        host=config['database']['host'],
        port=config['database']['port']
    )
    return conn

@app.route('/')
def index():
    user_name = None
    personalized_recommendations = []

    if 'user_id' in session:
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # Fetch the logged-in user's details
            cur.execute("SELECT username, role FROM users WHERE id = %s", (session['user_id'],))
            user = cur.fetchone()
            if user:
                user_name = user[0]
                session['user_role'] = user[1]
            
            # Fetch the user's last purchases and recommend items from the same category
            cur.execute("""
                SELECT d.id, d.name, d.price, d.image_url
                FROM dishes d
                JOIN sales s ON d.id = s.dish_id
                WHERE s.user_id = %s
                ORDER BY s.sale_date DESC
                LIMIT 1
            """, (session['user_id'],))
            
            last_purchase = cur.fetchone()
            print(f"Last purchase: {last_purchase}")  # Debugging output

            if last_purchase:
                # Fetch recommended items from the same category
                cur.execute("""
                    SELECT d.id, d.name, d.price, d.image_url
                    FROM dishes d
                    WHERE d.id != %s
                    LIMIT 10
                """, (last_purchase[0],))
                personalized_recommendations = cur.fetchall()
                print(f"Recommendations: {personalized_recommendations}")  # Debugging output

            cur.close()
            conn.close()

        except Exception as e:
            print(f"Error: {str(e)}")  # Print error for debugging
            flash(f"Error retrieving user data or recommendations: {str(e)}", 'danger')

    return render_template('index.html', user_name=user_name, recommendations=personalized_recommendations)

@app.route('/recommendations')
def recommendations():
    if 'user_id' not in session:
        flash('Please log in to see your recommendations.', 'danger')
        return redirect('/login')

    user_id = session['user_id']
    recommendations = []
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Fetch user's last purchased dish categories
        cur.execute("""
            SELECT DISTINCT d.category
            FROM sales s
            JOIN dishes d ON s.dish_id = d.id
            WHERE s.user_id = %s
        """, (user_id,))
        purchased_categories = cur.fetchall()

        if purchased_categories:
            # Flatten the list of categories
            purchased_categories = [row[0] for row in purchased_categories]

            # Get recommendations by excluding already purchased dishes from the same categories
            cur.execute("""
                SELECT d.id, d.name, d.price
                FROM dishes d
                WHERE d.category = ANY(%s) AND d.id NOT IN (
                    SELECT s.dish_id FROM sales s WHERE s.user_id = %s
                )
                LIMIT 10
            """, (tuple(purchased_categories), user_id))

            recommendations = cur.fetchall()

        cur.close()
        conn.close()

    except Exception as e:
        flash(f"Error fetching recommendations: {str(e)}", 'danger')

    return render_template('recommendations.html', recommendations=recommendations)

def generate_sales_graph(sales_data, period='Daily'):
    if not sales_data:
        plt.figure(figsize=(12, 7))
        plt.title(f'No Sales Data Available for {period} Period', fontsize=18)
        plt.xticks([], [])
        plt.yticks([], [])
        img = io.BytesIO()
        plt.tight_layout()
        plt.savefig(img, format='png')
        img.seek(0)
        graph_url = base64.b64encode(img.getvalue()).decode('utf8')
        plt.close()
        return graph_url

    dates = [row[0].strftime('%Y-%m-%d') for row in sales_data]
    sales = [row[1] for row in sales_data]
    X = np.arange(len(dates)).reshape(-1, 1)
    y = np.array(sales)
    model = LinearRegression()
    model.fit(X, y)
    next_day_sales = model.predict([[len(dates)]])
    dates.append('Predicted (Next Day)')
    sales.append(next_day_sales[0])

    fig, ax = plt.subplots(figsize=(12, 7))
    bars = ax.bar(dates, sales, color=['#66c2a5'] * (len(sales) - 1) + ['#fc8d62'], edgecolor='black')
    for bar in bars:
        bar.set_edgecolor('blue')

    ax.set_title(f'Sales Over Time ({period})', fontsize=18, color='#333333', fontweight='bold')
    ax.set_xlabel('Date', fontsize=14, color='#666666')
    ax.set_ylabel('Total Sales (₹)', fontsize=14, color='#666666')
    plt.xticks(rotation=45, ha='right', fontsize=12, color='#444444')
    plt.yticks(fontsize=12, color='#444444')
    for bar, sales_value in zip(bars, sales):
        height = bar.get_height()
        ax.annotate(f'{sales_value:.2f}', xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points", ha='center', fontsize=10, color='#000000')
    plt.grid(True, axis='y', linestyle='--', alpha=0.6)

    img = io.BytesIO()
    plt.tight_layout()
    plt.savefig(img, format='png')
    img.seek(0)
    graph_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()

    return graph_url

def generate_today_sales_graph(yesterday_sales, today_sales, weekly_sales_data):
    dates = ['Yesterday', 'Today', 'Predicted (Tomorrow)']
    sales = [yesterday_sales[1] if yesterday_sales else 0, today_sales[1] if today_sales else 0]
    X = np.arange(len(weekly_sales_data)).reshape(-1, 1)
    y = np.array([row[1] for row in weekly_sales_data])
    model = LinearRegression()
    model.fit(X, y)
    tomorrow_sales = model.predict([[len(weekly_sales_data)]])
    sales.append(tomorrow_sales[0])

    plt.figure(figsize=(10, 6))
    bars = plt.bar(dates, sales, color=['#ff9999', '#66b3ff', '#99ff99'], edgecolor='black')
    for bar, sales_value in zip(bars, sales):
        plt.annotate(f'{sales_value:.2f}', xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                     xytext=(0, 3), textcoords="offset points", ha='center')
    plt.title("Today's Sales and Prediction")
    plt.xlabel('Date')
    plt.ylabel('Sales (₹)')
    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    graph_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()

    return graph_url

def generate_weekly_sales_graph(weekly_sales_data):
    dates = [row[0].strftime('%Y-%m-%d') for row in weekly_sales_data]
    sales = [row[1] for row in weekly_sales_data]
    X = np.arange(len(dates)).reshape(-1, 1)
    y = np.array(sales)
    model = LinearRegression()
    model.fit(X, y)
    next_day_sales = model.predict([[len(dates)]])
    dates.append('Predicted (Next Day)')
    sales.append(next_day_sales[0])

    plt.figure(figsize=(10, 6))
    bars = plt.bar(dates, sales, color=['#66b3ff'] * (len(dates) - 1) + ['#ff9999'], edgecolor='black')
    for bar, sales_value in zip(bars, sales):
        plt.annotate(f'{sales_value:.2f}', xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                     xytext=(0, 3), textcoords="offset points", ha='center')
    plt.title("Weekly Sales and Next Day Prediction")
    plt.xlabel('Date')
    plt.ylabel('Sales (₹)')
    plt.xticks(rotation=45)
    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    graph_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()

    return graph_url

def generate_monthly_sales_graph(monthly_sales_data):
    dates = [row[0].strftime('%Y-%m-%d') for row in monthly_sales_data]
    sales = [row[1] for row in monthly_sales_data]
    X = np.arange(len(dates)).reshape(-1, 1)
    y = np.array(sales)
    model = LinearRegression()
    model.fit(X, y)
    next_week_sales = model.predict([[len(dates)]])
    dates.append('Predicted (Next Week)')
    sales.append(next_week_sales[0])

    plt.figure(figsize=(10, 6))
    bars = plt.bar(dates, sales, color=['#66b3ff'] * (len(dates) - 1) + ['#ff9999'], edgecolor='black')
    for bar, sales_value in zip(bars, sales):
        plt.annotate(f'{sales_value:.2f}', xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                     xytext=(0, 3), textcoords="offset points", ha='center')
    plt.title("Monthly Sales and Next Week Prediction")
    plt.xlabel('Date')
    plt.ylabel('Sales (₹)')
    plt.xticks(rotation=45)
    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    graph_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()

    return graph_url

@app.route('/admin/sales')
def admin_sales():
    period = request.args.get('period', 'today')
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        if period == 'today':
            cur.execute("""
                SELECT sale_date::date, SUM(total_price)
                FROM sales
                WHERE sale_date::date = CURRENT_DATE - INTERVAL '1 DAY'
                GROUP BY sale_date::date;
            """)
            yesterday_sales = cur.fetchone()

            cur.execute("""
                SELECT sale_date::date, SUM(total_price)
                FROM sales
                WHERE sale_date::date = CURRENT_DATE
                GROUP BY sale_date::date;
            """)
            today_sales = cur.fetchone()

            cur.execute("""
                SELECT sale_date::date, SUM(total_price)
                FROM sales
                WHERE sale_date::date >= CURRENT_DATE - INTERVAL '7 DAYS'
                GROUP BY sale_date::date
                ORDER BY sale_date::date;
            """)
            weekly_sales_data = cur.fetchall()

            graph_url = generate_today_sales_graph(yesterday_sales, today_sales, weekly_sales_data)

        elif period == 'weekly':
            cur.execute("""
                SELECT sale_date::date, SUM(total_price)
                FROM sales
                WHERE sale_date::date >= CURRENT_DATE - INTERVAL '7 DAYS'
                GROUP BY sale_date::date
                ORDER BY sale_date::date;
            """)
            weekly_sales_data = cur.fetchall()
            graph_url = generate_weekly_sales_graph(weekly_sales_data)

        elif period == 'monthly':
            cur.execute("""
                SELECT sale_date::date, SUM(total_price)
                FROM sales
                WHERE sale_date::date >= CURRENT_DATE - INTERVAL '30 DAYS'
                GROUP BY sale_date::date
                ORDER BY sale_date::date;
            """)
            monthly_sales_data = cur.fetchall()
            graph_url = generate_monthly_sales_graph(monthly_sales_data)

        cur.close()
        conn.close()

        return render_template('admin_sales.html', graph_url=graph_url, period=period)

    except Exception as e:
        flash(f"Error loading sales data: {str(e)}", 'danger')
        return redirect('/')

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()  # Used JSON data for asynchronous request
    
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'status': 'error', 'message': 'Email and password are required.'}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, username, role FROM users WHERE email = %s AND password = %s", (email, password))
        user = cur.fetchone()

        cur.close()
        conn.close()

        if user:
            session['user_id'] = user[0]
            session['user_name'] = user[1]
            session['user_role'] = user[2]
            return jsonify({'status': 'success', 'message': 'Login successful!'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Invalid email or password. Please try again.'}), 401
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'An error occurred: {str(e)}'}), 500


@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('user_role', None)
    return jsonify({'status': 'success', 'message': 'You have been logged out successfully.'}), 200

def assign_image_url(dish_name):
    dish_name_lower = dish_name.lower()
    if 'burger' in dish_name_lower:
        return f"/static/images/burgers/{random.choice(os.listdir('static/images/burgers'))}"
    elif 'pizza' in dish_name_lower:
        return f"/static/images/pizza/{random.choice(os.listdir('static/images/pizza'))}"
    elif 'samosa' in dish_name_lower:
        return f"/static/images/samosa/{random.choice(os.listdir('static/images/samosa'))}"
    else:
        return "/static/images/default_food_image.jpg"
    

@app.route('/search')
def search():
    search_term = request.args.get('q', '').strip()  # Get the search term from the query parameter
    conn = get_db_connection()
    cur = conn.cursor()

    # Search for a restaurant with the given search term
    cur.execute("""
        SELECT r.id, r.name, r.location, d.id, d.name, d.price, d.image_url
        FROM restaurants r
        LEFT JOIN dishes d ON r.id = d.restaurant_id
        WHERE r.name ILIKE %s
    """, (f"%{search_term}%",))
    restaurant_results = cur.fetchall()

    if restaurant_results:
        # If the restaurant exists, return the whole dish catalog
        catalog = []
        for row in restaurant_results:
            catalog.append({
                'restaurant_id': row[0],
                'restaurant_name': row[1],
                'restaurant_location': row[2],
                'dish_id': row[3],
                'dish_name': row[4],
                'dish_price': row[5],
                'dish_image': row[6]
            })
        cur.close()
        conn.close()

        # Return the restaurant catalog
        return render_template('restaurant_catalog.html', catalog=catalog)

    # If no restaurant matches, search for dishes directly
    cur.execute("""
        SELECT d.id, d.name, d.price, d.image_url, r.name as restaurant_name
        FROM dishes d
        LEFT JOIN restaurants r ON d.restaurant_id = r.id
        WHERE d.name ILIKE %s
    """, (f"%{search_term}%",))
    dish_results = cur.fetchall()

    cur.close()
    conn.close()

    # Prepare dish search results to send to the template
    dish_list = []
    for row in dish_results:
        dish_list.append({
            'dish_id': row[0],
            'dish_name': row[1],
            'dish_price': row[2],
            'dish_image': row[3],
            'restaurant_name': row[4]
        })

    # Render the search results page (dishes)
    return render_template('search.html', dishes=dish_list, search_term=search_term)

@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'User is not logged in'}), 400

    user_id = session['user_id']
    dish_id = request.json.get('dish_id')
    quantity = request.json.get('quantity', 1)

    if not dish_id:
        return jsonify({'status': 'error', 'message': 'Invalid dish ID'}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO cart (user_id, dish_id, quantity) VALUES (%s, %s, %s)", 
                    (user_id, dish_id, quantity))
        conn.commit()

        cur.close()
        conn.close()

        return jsonify({'status': 'success', 'message': 'Item added to cart'}), 200

    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error adding to cart: {str(e)}'}), 500
    

@app.route('/remove-from-cart', methods=['POST'])
def remove_from_cart():
    try:
        # Parse the incoming data
        data = request.get_json()
        item_id = data.get('item_id')

        if not item_id:
            return jsonify({'status': 'error', 'message': 'Invalid item ID'}), 400

        # Get the user's ID from the session
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'status': 'error', 'message': 'User not logged in'}), 403

        # Remove the item from the user's cart
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            DELETE FROM cart WHERE user_id = %s AND dish_id = %s
        """, (user_id, item_id))
        conn.commit()

        # Recalculate the total cart cost after removal
        cur.execute("""
            SELECT SUM(dishes.price * cart.quantity) 
            FROM cart 
            JOIN dishes ON cart.dish_id = dishes.id 
            WHERE cart.user_id = %s
        """, (user_id,))
        new_total = cur.fetchone()[0] or 0

        cur.close()
        conn.close()

        return jsonify({'status': 'success', 'new_total': new_total})

    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error removing item: {str(e)}'}), 500

@app.route('/checkout')
def checkout():
    if 'user_id' not in session:
        flash('Please log in to view your cart.', 'danger')
        return redirect('/')

    user_id = session['user_id']

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT dishes.name, dishes.price, cart.quantity, (dishes.price * cart.quantity) AS total_price
            FROM cart
            JOIN dishes ON cart.dish_id = dishes.id
            WHERE cart.user_id = %s
        """, (user_id,))
        cart_items = cur.fetchall()

        total_cost = sum(item[3] for item in cart_items)

        if not cart_items:
            flash("Your cart is empty.", "warning")
            return redirect('/')

        session['total_cost'] = total_cost

        cur.close()
        conn.close()

        return render_template('checkout.html', cart_items=cart_items, total_cost=total_cost)

    except Exception as e:
        flash(f"Error loading cart: {str(e)}", 'danger')
        return redirect('/')
    

    cart_item = Cart.query.filter_by(user_id=user_id, item_id=item_id).first()
    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()

    return redirect(url_for('checkout'))


@app.route('/payment', methods=['GET'])
def payment():
    if 'total_cost' not in session or 'user_id' not in session:
        flash("Something went wrong. Redirecting back to checkout.", "warning")
        return redirect('/checkout')

    total_cost = session['total_cost']
    return render_template('payment.html', total_cost=total_cost)

@app.route('/fake-payment', methods=['POST'])
def fake_payment():
    payment_method = request.form['payment_method']
    upi_id = request.form.get('upi_id', '')
    card_number = request.form.get('card_number', '')
    bank_name = request.form.get('bank_name', '')

    # Retrieve user and total cost from session
    user_id = session.get('user_id')
    total_cost = session.get('total_cost')

    # Ensure user and total cost are present
    if not user_id or not total_cost:
        flash("No items in cart or total cost is None.", 'danger')
        return redirect('/checkout')

    try:
        # Establish database connection
        conn = get_db_connection()
        cur = conn.cursor()

        # Insert payment record into the sales table
        cur.execute("""
            INSERT INTO sales (user_id, total_price, sale_date, payment_method)
            VALUES (%s, %s, NOW(), %s)
        """, (user_id, total_cost, payment_method))
        conn.commit()

        # Clear cart items after successful payment
        cur.execute("DELETE FROM cart WHERE user_id = %s", (user_id,))
        conn.commit()

        cur.close()
        conn.close()

        # Clear session after payment
        session.pop('total_cost', None)

        # Redirect to the home page with success message
        flash(f"Payment of ₹{total_cost} was successful!", 'success')
        return redirect('/')

    except Exception as e:
        # Handle and log any errors
        print(f"Error processing payment: {str(e)}")
        flash(f"Error processing payment: {str(e)}", 'danger')
        return redirect('/checkout')

if __name__ == '__main__':
    app.run(debug=True)
