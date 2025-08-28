from flask_mysqldb import MySQL

def create_tables(app, mysql):
    with app.app_context():
        cur = mysql.connection.cursor()
        
        # Users table: Added last_login, profile_picture_url, and is_active for better user management.
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(80) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            mobile VARCHAR(20) NOT NULL,
            roles VARCHAR(255) NOT NULL DEFAULT 'requester',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME,
            profile_picture_url VARCHAR(255),
            is_active BOOLEAN NOT NULL DEFAULT TRUE
        )
        """)
        
        # Donations table: Added status, original_quantity, remaining_quantity, and pickup window for better tracking.
        cur.execute("""
        CREATE TABLE IF NOT EXISTS donations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            food_name VARCHAR(100) NOT NULL,
            original_quantity INT NOT NULL,
            remaining_quantity INT NOT NULL,
            expiry_date DATE NOT NULL,
            pickup_address TEXT NOT NULL,
            pickup_window_start DATETIME NOT NULL,
            pickup_window_end DATETIME NOT NULL,
            special_instructions TEXT,
            donor_id INT NOT NULL,
            latitude DECIMAL(10, 8),
            longitude DECIMAL(11, 8),
            food_image_base64 LONGTEXT,
            status VARCHAR(50) NOT NULL DEFAULT 'available', -- e.g., available, fully_claimed, expired, cancelled
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (donor_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """)
        
        # Requests table: Enhanced with more specific status values and timestamps.
        cur.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INT AUTO_INCREMENT PRIMARY KEY,
            food_id INT NOT NULL,
            requester_id INT NOT NULL,
            quantity INT NOT NULL,
            status VARCHAR(50) NOT NULL DEFAULT 'pending', -- pending, assigned, pickup_pending_verification, in_transit, delivery_pending_verification, completed, cancelled
            delivery_address TEXT,
            delivery_latitude DECIMAL(10, 8),
            delivery_longitude DECIMAL(11, 8),
            transport_arranged BOOLEAN DEFAULT FALSE,
            volunteer_id INT,
            requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            assigned_at DATETIME,
            completed_at DATETIME,
            FOREIGN KEY (food_id) REFERENCES donations(id) ON DELETE CASCADE,
            FOREIGN KEY (requester_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (volunteer_id) REFERENCES users(id) ON DELETE SET NULL
        )
        """)

        # Verifications table for two-phase (pickup & delivery) confirmation.
        cur.execute("""
        CREATE TABLE IF NOT EXISTS verifications (
            id INT AUTO_INCREMENT PRIMARY KEY,
            request_id INT NOT NULL,
            user_id INT NOT NULL, -- The user who needs to perform the verification (donor or requester)
            token VARCHAR(255) UNIQUE NOT NULL,
            type ENUM('pickup', 'delivery') NOT NULL,
            expires_at DATETIME NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            used_at DATETIME,
            FOREIGN KEY (request_id) REFERENCES requests(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """)
        
        # Notifications table: Added is_read and link for interactive notifications.
        cur.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            message TEXT NOT NULL,
            is_read BOOLEAN NOT NULL DEFAULT FALSE,
            link VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """)

        # Reviews table: For future implementation of a rating/feedback system.
        cur.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INT AUTO_INCREMENT PRIMARY KEY,
            request_id INT NOT NULL,
            reviewer_id INT NOT NULL,
            reviewee_id INT NOT NULL,
            rating INT NOT NULL, -- e.g., 1 to 5
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (request_id) REFERENCES requests(id) ON DELETE CASCADE,
            FOREIGN KEY (reviewer_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (reviewee_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """)

        # Schema Alterations for existing tables
        try:
            cur.execute("ALTER TABLE requests MODIFY status VARCHAR(50) NOT NULL DEFAULT 'pending';")
            app.logger.info("Altered 'requests' table to modify 'status' column length.")
        except Exception as e:
            # This will likely fail if the column is already the correct type, which is fine.
            app.logger.warning(f"Could not alter 'requests' table (may already be up-to-date): {e}")

        # Schema Alterations for verifications table
        try:
            cur.execute("ALTER TABLE verifications ADD COLUMN used_at DATETIME DEFAULT NULL;")
            app.logger.info("Altered 'verifications' table to add 'used_at' column.")
        except Exception as e:
            app.logger.warning(f"Could not alter 'verifications' table to add 'used_at' (may already exist): {e}")
        
        try:
            cur.execute("ALTER TABLE verifications DROP COLUMN is_verified;")
        except Exception as e:
            app.logger.warning(f"Could not alter 'verifications' table to drop 'is_verified' (may not exist): {e}")

        try:
            cur.execute("ALTER TABLE verifications DROP COLUMN verified_at;")
        except Exception as e:
            app.logger.warning(f"Could not alter 'verifications' table to drop 'verified_at' (may not exist): {e}")

        mysql.connection.commit()
        cur.close()
