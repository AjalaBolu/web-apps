# ============================================
# app.py - Main Flask Application Entry Point
# ============================================
# This file initializes the Flask app, configures
# the MySQL database, and registers all routes.

from flask import Flask
from flask_mysqldb import MySQL

# Create the Flask application instance
app = Flask(__name__)

# ----------------------------------------
# SECRET KEY - Used for session security
# Change this to a random string in production!
# ----------------------------------------
app.secret_key = 'car_rental_secret_key_2024'

# ----------------------------------------
# MySQL Database Configuration
# Update these settings to match your MySQL setup
# ----------------------------------------
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'          # Your MySQL username
app.config['MYSQL_PASSWORD'] = 'ilovemum$'          # Your MySQL password
app.config['MYSQL_DB'] = 'car_rental_db'  # Database name
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'  # Return rows as dictionaries

# Initialize MySQL with our Flask app
mysql = MySQL(app)

# ----------------------------------------
# Import and register all routes
# Routes are defined in routes.py
# ----------------------------------------
from routes import register_routes
register_routes(app, mysql)

# ----------------------------------------
# Run the application
# debug=True shows errors during development
# ----------------------------------------
if __name__ == '__main__':
    app.run(debug=True, port=5000)
