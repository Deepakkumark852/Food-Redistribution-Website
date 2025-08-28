import smtplib
import logging
from config import Config

try:
    from email.mime.text import MIMEText as MimeText
    from email.mime.multipart import MIMEMultipart as MimeMultipart
except ImportError:
    from email.MIMEText import MIMEText as MimeText
    from email.MIMEMultipart import MIMEMultipart as MimeMultipart

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = Config.MAIL_SERVER
        self.smtp_port = Config.MAIL_PORT
        self.username = Config.MAIL_USERNAME
        self.password = Config.MAIL_PASSWORD
        self.sender = Config.MAIL_DEFAULT_SENDER
        self.app_name = Config.APP_NAME
        self.frontend_url = Config.FRONTEND_URL
    
    def send_email(self, to_email, subject, html_content, text_content=None):
        """Send email using Gmail SMTP"""
        try:
            if not self.username or not self.password:
                logger.error("Gmail credentials not configured")
                return False
            
            # Create message
            msg = MimeMultipart('alternative')
            msg['From'] = self.sender
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add text and HTML parts
            if text_content:
                text_part = MimeText(text_content, 'plain')
                msg.attach(text_part)
            
            html_part = MimeText(html_content, 'html')
            msg.attach(html_part)
            
            # Connect to Gmail SMTP server
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            
            # Send email
            text = msg.as_string()
            server.sendmail(self.sender, to_email, text)
            server.quit()
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def send_login_notification(self, user_email, username, login_time, ip_address=None):
        """Send login notification email"""
        subject = f"Login Alert - {self.app_name}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; color: #4F46E5; margin-bottom: 30px; }}
                .content {{ color: #333; line-height: 1.6; }}
                .info-box {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
                .btn {{ display: inline-block; padding: 12px 24px; background-color: #4F46E5; color: white; text-decoration: none; border-radius: 5px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Login Alert</h1>
                </div>
                <div class="content">
                    <p>Hello <strong>{username}</strong>,</p>
                    <p>We detected a new login to your {self.app_name} account.</p>
                    
                    <div class="info-box">
                        <strong>Login Details:</strong><br>
                        📅 Time: {login_time}<br>
                        👤 Username: {username}<br>
                        {f'🌐 IP Address: {ip_address}<br>' if ip_address else ''}
                    </div>
                    
                    <p>If this was you, no action is needed. If you didn't log in, please secure your account immediately.</p>
                    
                    <a href="{self.frontend_url}/profile" class="btn">Manage Account</a>
                </div>
                <div class="footer">
                    <p>This is an automated message from {self.app_name}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Login Alert - {self.app_name}
        
        Hello {username},
        
        We detected a new login to your account.
        
        Login Details:
        Time: {login_time}
        Username: {username}
        {f'IP Address: {ip_address}' if ip_address else ''}
        
        If this wasn't you, please secure your account immediately.
        
        Visit: {self.frontend_url}/profile
        """
        
        return self.send_email(user_email, subject, html_content, text_content)
    
    def send_logout_notification(self, user_email, username, logout_time):
        """Send logout notification email"""
        subject = f"Logout Confirmation - {self.app_name}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; color: #28a745; margin-bottom: 30px; }}
                .content {{ color: #333; line-height: 1.6; }}
                .info-box {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>👋 Logout Confirmation</h1>
                </div>
                <div class="content">
                    <p>Hello <strong>{username}</strong>,</p>
                    <p>You have successfully logged out of your {self.app_name} account.</p>
                    
                    <div class="info-box">
                        <strong>Logout Details:</strong><br>
                        📅 Time: {logout_time}<br>
                        👤 Username: {username}
                    </div>
                    
                    <p>Thank you for using our platform to help redistribute food and reduce waste!</p>
                </div>
                <div class="footer">
                    <p>This is an automated message from {self.app_name}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(user_email, subject, html_content)
    
    def send_verification_email(self, recipient_email, recipient_name, volunteer_name, food_name, verification_type, verification_link):
        """Send a verification email for pickup or delivery."""
        subject = f"Action Required: Confirm Food {verification_type.title()}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; color: #ffc107; margin-bottom: 30px; }}
                .content {{ color: #333; line-height: 1.6; }}
                .info-box {{ background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #ffc107; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
                .btn {{ display: inline-block; padding: 12px 24px; background-color: #ffc107; color: #212529; text-decoration: none; border-radius: 5px; margin: 10px 0; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Action Required: Confirm {verification_type.title()}</h1>
                </div>
                <div class="content">
                    <p>Hello <strong>{recipient_name}</strong>,</p>
                    <p>Volunteer <strong>{volunteer_name}</strong> has initiated the <strong>{verification_type}</strong> for the food item: <strong>{food_name}</strong>.</p>
                    <p>Please click the button below to verify that this action has been completed. This link is valid for 24 hours.</p>
                    
                    <a href="{verification_link}" class="btn">Confirm {verification_type.title()}</a>
                    
                    <p>If you did not request this or do not recognize this activity, please ignore this email. Do not click the link if you are not the intended recipient.</p>
                </div>
                <div class="footer">
                    <p>This is an automated message from {self.app_name}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Action Required: Confirm Food {verification_type.title()}
        
        Hello {recipient_name},
        
        Volunteer {volunteer_name} has initiated the {verification_type} for the food item: {food_name}.
        
        Please visit the following link to verify this action:
        {verification_link}
        
        If you did not request this, please ignore this email.
        
        Thank you,
        The {self.app_name} Team
        """
        
        return self.send_email(recipient_email, subject, html_content, text_content)

# Create global email service instance
email_service = EmailService()

def send_verification_email(recipient_email, recipient_name, volunteer_name, food_name, verification_type, verification_link):
    """A wrapper function to send verification email using the global email_service instance."""
    return email_service.send_verification_email(
        recipient_email=recipient_email,
        recipient_name=recipient_name,
        volunteer_name=volunteer_name,
        food_name=food_name,
        verification_type=verification_type,
        verification_link=verification_link
    )
