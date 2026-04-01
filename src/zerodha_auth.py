"""
Zerodha API Authentication Module

Handles session management, token generation, and authentication flows.
"""

from kiteconnect import KiteConnect
from src.logger import log_event
import os
import json
from datetime import datetime

class ZerodhaAuth:
    """Handle Zerodha authentication and session management."""
    
    def __init__(self, api_key, api_secret):
        """
        Initialize authentication handler.
        
        Args:
            api_key (str): Zerodha API key
            api_secret (str): Zerodha API secret
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.kite = KiteConnect(api_key=api_key)
        self.session_file = '.zerodha_session.json'
        log_event('ZerodhaAuth initialized')
    
    def get_login_url(self):
        """
        Get Zerodha login URL for obtaining request token.
        
        Returns:
            str: Login URL
        """
        try:
            login_url = self.kite.login_url()
            log_event(f'Generated login URL')
            return login_url
        except Exception as e:
            log_event(f'Error generating login URL: {str(e)}')
            return None
    
    def generate_access_token(self, request_token):
        """
        Generate access token from request token.
        
        Args:
            request_token (str): Request token from login
        
        Returns:
            str: Access token or None
        """
        try:
            response = self.kite.generate_session(request_token, api_secret=self.api_secret)
            access_token = response['access_token']
            
            # Save session
            self.save_session(access_token)
            
            log_event(f'Access token generated and saved')
            return access_token
        except Exception as e:
            log_event(f'Error generating access token: {str(e)}')
            return None
    
    def save_session(self, access_token):
        """
        Save session to file.
        
        Args:
            access_token (str): Access token to save
        """
        try:
            session_data = {
                'access_token': access_token,
                'api_key': self.api_key,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(self.session_file, 'w') as f:
                json.dump(session_data, f)
            
            log_event('Session saved to file')
        except Exception as e:
            log_event(f'Error saving session: {str(e)}')
    
    def load_session(self):
        """
        Load saved session from file.
        
        Returns:
            tuple: (access_token, api_key) or (None, None)
        """
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, 'r') as f:
                    session_data = json.load(f)
                
                access_token = session_data.get('access_token')
                api_key = session_data.get('api_key')
                
                log_event('Session loaded from file')
                return access_token, api_key
        except Exception as e:
            log_event(f'Error loading session: {str(e)}')
        
        return None, None
    
    def clear_session(self):
        """Clear saved session."""
        try:
            if os.path.exists(self.session_file):
                os.remove(self.session_file)
            log_event('Session cleared')
        except Exception as e:
            log_event(f'Error clearing session: {str(e)}')
    
    def validate_access_token(self, access_token):
        """
        Validate if access token is valid.
        
        Args:
            access_token (str): Access token to validate
        
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            self.kite.set_access_token(access_token)
            profile = self.kite.profile()
            log_event(f'Access token validated for user: {profile.get("user_id")}')
            return True
        except Exception as e:
            log_event(f'Access token validation failed: {str(e)}')
            return False


class SessionManager:
    """Manage Zerodha sessions with auto-renewal."""
    
    def __init__(self, api_key, api_secret, access_token=None):
        """
        Initialize session manager.
        
        Args:
            api_key (str): Zerodha API key
            api_secret (str): Zerodha API secret
            access_token (str): Optional access token
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self.auth = ZerodhaAuth(api_key, api_secret)
        
        log_event('SessionManager initialized')
    
    def get_valid_access_token(self):
        """
        Get a valid access token (load from file or use provided).
        
        Returns:
            str: Access token
        """
        if self.access_token:
            return self.access_token
        
        # Try to load from file
        saved_token, _ = self.auth.load_session()
        if saved_token and self.auth.validate_access_token(saved_token):
            self.access_token = saved_token
            return saved_token
        
        log_event('No valid access token available. Please authenticate.')
        return None
    
    def authenticate(self, request_token):
        """
        Authenticate and get access token.
        
        Args:
            request_token (str): Request token from Zerodha login
        
        Returns:
            str: Access token or None
        """
        access_token = self.auth.generate_access_token(request_token)
        if access_token:
            self.access_token = access_token
        return access_token
    
    def refresh_session(self):
        """Refresh session (re-authenticate if needed)."""
        if not self.auth.validate_access_token(self.access_token):
            log_event('Access token expired. Please re-authenticate.')
            return False
        return True
