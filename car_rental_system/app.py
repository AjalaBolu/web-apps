import os
from flask import Flask
from flask_mysqldb import MySQL

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'car_rental_secret_key_2024')

app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD', '')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB', 'car_rental_db')
app.config['MYSQL_PORT'] = int(os.environ.get('MYSQL_PORT', 3306))
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['MYSQL_CUSTOM_OPTIONS'] = {
    "ssl": {"ca": os.path.join(BASE_DIR, "certs", "ca.pem")}
}

mysql = MySQL(app)

from tier_data import TIER_FEATURES, TIER_COLORS

USD_TO_NGN_RATE = 1550

@app.template_filter('naira')
def naira_filter(usd_amount):
    naira_amount = float(usd_amount) * USD_TO_NGN_RATE
    return f"₦{naira_amount:,.2f}"

@app.context_processor
def inject_tier_data():
    return dict(TIER_FEATURES=TIER_FEATURES, TIER_COLORS=TIER_COLORS)

from routes import register_routes
register_routes(app, mysql)

if __name__ == '__main__':
    app.run(debug=True, port=5000)