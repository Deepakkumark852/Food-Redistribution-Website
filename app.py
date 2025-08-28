from flask import Flask
from config import Config
from flask_mysqldb import MySQL
from models import create_tables
from routes import init_routes
from flask_cors import CORS
from flask.json import JSONEncoder
from decimal import Decimal
from datetime import datetime, date

class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super(CustomJSONEncoder, self).default(obj)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.json_encoder = CustomJSONEncoder
    # Configure CORS with more specific settings
    CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000", "http://localhost:5173", "http://localhost:5174"], 
                                     "supports_credentials": True,
                                     "allow_headers": ["Content-Type", "Authorization"]}})
    # Initialize MySQL
    mysql = MySQL(app)
    
    # Initialize routes
    init_routes(app, mysql)
    
    return app, mysql

if __name__ == '__main__':
    app, mysql = create_app()
    create_tables(app, mysql)
    
    app.run(debug=True, port=5000)
