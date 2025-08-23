from flask_mysqldb import MySQL

def create_tables(app, mysql):
    with app.app_context():
        cur = mysql.connection.cursor()
        
        # Users table with role column for RBAC
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(80) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            mobile VARCHAR(20) NOT NULL,
            role ENUM('donor', 'requester', 'volunteer', 'admin') NOT NULL DEFAULT 'donor',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Donations table
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (donor_id) REFERENCES users(id)
        )
        """)
        
        # Requests table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INT AUTO_INCREMENT PRIMARY KEY,
            food_id INT NOT NULL,
            requester_id INT NOT NULL,
            quantity INT NOT NULL,
            delivery_address TEXT NOT NULL,
            transport_arranged BOOLEAN DEFAULT FALSE,
            status ENUM('pending', 'assigned', 'completed') DEFAULT 'pending',
            volunteer_id INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            assigned_at DATETIME,
            completed_at DATETIME,
            FOREIGN KEY (food_id) REFERENCES donations(id),
            FOREIGN KEY (requester_id) REFERENCES users(id),
            FOREIGN KEY (volunteer_id) REFERENCES users(id)
        )
        """)
        
        # Notifications table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """)

        mysql.connection.commit()
        cur.close()
