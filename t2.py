import psycopg2

# Connect to PostgreSQL
conn = psycopg2.connect(
    dbname="tomato_db",
    user="postgres",
    password="4445",
    host="localhost",
    port="5432"
)

# Create a cursor object
cur = conn.cursor()

# Query to get all active connections
cur.execute("""
    SELECT pid, usename AS user_name, datname AS database_name, client_addr AS client_address, state, query
    FROM pg_stat_activity
    WHERE state = 'active';
""")
active_connections = cur.fetchall()
print("Active Connections:")
for connection in active_connections:
    print(connection)

# Query to get all table names
cur.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public';
""")
tables = cur.fetchall()
print("\nTables:")
for table in tables:
    print(table[0])

    # Query to get columns for each table
    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = %s;
    """, (table[0],))
    columns = cur.fetchall()
    print("Columns:")
    for column in columns:
        print(f"  {column[0]} ({column[1]})")

# Close the cursor and connection
cur.close()
conn.close()
