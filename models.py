from flask_mysqldb import MySQL

def create_tables(app, mysql):
    with app.app_context():
        cur = mysql.connection.cursor()
        
        # Users table with roles column for RBAC (comma-separated roles)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(80) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            mobile VARCHAR(20) NOT NULL,
            roles VARCHAR(255) NOT NULL DEFAULT 'donor',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Donations table with geolocation and image support
        cur.execute("""
        CREATE TABLE IF NOT EXISTS donations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            food_name VARCHAR(100) NOT NULL,
            quantity INT NOT NULL,
            expiry_date DATE NOT NULL,
            pickup_address TEXT NOT NULL,
            pickup_time TIME NOT NULL,
            special_instructions TEXT,
            donor_id INT NOT NULL,
            latitude DOUBLE,
            longitude DOUBLE,
            food_image_base64 LONGTEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (donor_id) REFERENCES users(id)
        )
        """)
        
        # Requests table with verification system and location tracking
        cur.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INT AUTO_INCREMENT PRIMARY KEY,
            food_id INT NOT NULL,
            requester_id INT NOT NULL,
            quantity INT NOT NULL,
            delivery_address TEXT NOT NULL,
            delivery_latitude DOUBLE,
            delivery_longitude DOUBLE,
            transport_arranged BOOLEAN DEFAULT FALSE,
            status ENUM('pending', 'assigned', 'completed') DEFAULT 'pending',
            volunteer_id INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            assigned_at DATETIME,
            completed_at DATETIME,
            
            -- Verification system fields
            pickup_confirmed_at DATETIME,
            pickup_verified_by_donor BOOLEAN DEFAULT FALSE,
            donor_verified_at DATETIME,
            delivery_confirmed_at DATETIME,
            delivery_verified_by_requester BOOLEAN DEFAULT FALSE,
            requester_verified_at DATETIME,
            
            FOREIGN KEY (food_id) REFERENCES donations(id),
            FOREIGN KEY (requester_id) REFERENCES users(id),
            FOREIGN KEY (volunteer_id) REFERENCES users(id)
        )
        """)
        
        # Notifications table for system messages
        cur.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            message TEXT NOT NULL,
            is_read BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """)

        mysql.connection.commit()
        cur.close()
