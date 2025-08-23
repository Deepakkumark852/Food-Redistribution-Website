from flask import Flask
from config import Config
from flask_mysqldb import MySQL
from models import create_tables
from routes import init_routes
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)
    # Initialize MySQL
    mysql = MySQL(app)
    
    # Initialize routes
    init_routes(app, mysql)
    
    return app, mysql

if __name__ == '__main__':
    app, mysql = create_app()
    create_tables(app, mysql)
    
    app.run(debug=True, port=5000)
