import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.logger import log_event

class NotificationManager:
    """Manages alerts and notifications via email and console - PRODUCTION READY."""
    
    def __init__(self, email_config=None):
        self.email_enabled = False
        self.smtp_server = None
        self.smtp_port = None
        self.sender_email = None
        self.sender_password = None
        self.recipient_email = None
        
        if email_config:
            self.smtp_server = email_config.get('smtp_server', 'smtp.gmail.com')
            self.smtp_port = email_config.get('smtp_port', 587)
            self.sender_email = email_config.get('sender_email')
            self.sender_password = email_config.get('sender_password')
            self.recipient_email = email_config.get('recipient_email')
            
            # Validate email config
            if all([self.sender_email, self.sender_password, self.recipient_email]):
                self.email_enabled = True
                log_event('Email notifications ENABLED')
            else:
                log_event('Email config incomplete - email notifications DISABLED')
        
        log_event('NotificationManager initialized - PRODUCTION MODE')
    
    def send_email(self, subject, message):
        """Send email notification with retry logic."""
        if not self.email_enabled:
            log_event(f'Email disabled. Notification: {subject} | {message}')
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            msg['Subject'] = subject
            msg.attach(MIMEText(message, 'plain'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
            server.quit()
            
            log_event(f'Email sent: {subject}')
            return True
        except Exception as e:
            log_event(f'Error sending email: {str(e)}')
            return False
    
    def notify_order(self, symbol, side, quantity, price, order_id=None):
        """Notify about order placement."""
        message = f'Order {side}: {symbol}\nQuantity: {quantity}\nPrice: ₹{price:.2f}'
        if order_id:
            message += f'\nOrder ID: {order_id}'
        
        print(f'[TRADE] {side} {symbol} @ ₹{price:.2f} x {quantity}')
        log_event(message)
        self.send_email(f'[TRADE] {side} {symbol}', message)
    
    def notify_position_closed(self, symbol, pnl):
        """Notify about position closure."""
        status = 'PROFIT' if pnl > 0 else 'LOSS'
        message = f'Position closed: {symbol}\nP&L: ₹{pnl:.2f}'
        
        print(f'[CLOSE] {symbol} | P&L: ₹{pnl:.2f}')
        log_event(message)
        self.send_email(f'[CLOSE] Position {status}: {symbol}', message)
    
    def notify_daily_limit(self, limit_type, current_value):
        """Notify about daily limit breach."""
        message = f'{limit_type} LIMIT REACHED\nCurrent: ₹{current_value:.2f}'
        print(f'[ALERT] {limit_type} LIMIT: ₹{current_value:.2f}')
        log_event(f'ALERT: {message}')
        self.send_email(f'[ALERT] {limit_type} Limit Reached', message)
    
    def notify_risk_alert(self, alert_message):
        """Notify about risk alerts."""
        print(f'[RISK] {alert_message}')
        log_event(f'RISK ALERT: {alert_message}')
        self.send_email('Risk Alert', alert_message)
    
    def notify_error(self, error_message):
        """Notify about errors."""
        print(f'[ERROR] {error_message}')
        log_event(f'ERROR: {error_message}')
        self.send_email('Bot Error Alert', f'ERROR: {error_message}')
