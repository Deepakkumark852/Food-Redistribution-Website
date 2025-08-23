import os
import uuid

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-123'
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = 'Dk#9003212258'  # Your MySQL password
    MYSQL_DB = 'food_donation_db'
    MYSQL_CURSORCLASS = 'DictCursor'
    # Special key for admin registration
    ADMIN_SPECIAL_KEY = os.environ.get('ADMIN_SPECIAL_KEY') or str(uuid.uuid4())
