#!/usr/bin/env python3
"""
Tinder Setup System
Automatically obtains auth tokens from login credentials
"""

import json
import time
import requests
import re
from urllib.parse import urlparse, parse_qs
import getpass

class TinderSetup:
    def __init__(self):
        self.config_file = "src/config/config.json"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def load_config(self):
        """Load current configuration"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to load config: {e}")
            return {}
    
    def save_config(self, config):
        """Save configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            print(f"Failed to save config: {e}")
            return False
    
    def get_tinder_x_auth_token(self, email, password):
        """Get Tinder X-Auth-Token directly from browser login (headless)"""
        print("Attempting to get Tinder X-Auth-Token automatically...")
        
        try:
            # Tinder login endpoint
            login_url = "https://tinder.com/login"
            
            # Get login page to extract form data
            response = self.session.get(login_url)
            if response.status_code != 200:
                print(f"Failed to get Tinder login page: {response.status_code}")
                return None
            
            # Extract CSRF token and other form data
            csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', response.text)
            if not csrf_match:
                print("Could not extract CSRF token from login page")
                return None
            
            csrf_token = csrf_match.group(1)
            print(f"Extracted CSRF token: {csrf_token[:10]}...")
            
            # Prepare login data
            login_data = {
                'email': email,
                'password': password,
                'csrf_token': csrf_token
            }
            
            # Set proper headers for Tinder
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': login_url,
                'Origin': 'https://tinder.com',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            # Submit login form
            login_response = self.session.post(login_url, data=login_data, headers=headers, allow_redirects=True)
            
            if login_response.status_code == 200:
                # Check if login was successful
                if 'dashboard' in login_response.url or 'app' in login_response.url:
                    print("Tinder login successful!")
                    
                    # Now get the X-Auth-Token from the dashboard
                    dashboard_url = "https://tinder.com/app"
                    dashboard_response = self.session.get(dashboard_url)
                    
                    if dashboard_response.status_code == 200:
                        # Extract X-Auth-Token from response headers or cookies
                        auth_token = None
                        
                        # Check cookies first
                        for cookie in self.session.cookies:
                            if 'tinder_token' in cookie.name.lower() or 'auth' in cookie.name.lower():
                                auth_token = cookie.value
                                break
                        
                        # If not in cookies, check response headers
                        if not auth_token:
                            auth_headers = [h for h in dashboard_response.headers.keys() if 'auth' in h.lower() or 'token' in h.lower()]
                            for header in auth_headers:
                                print(f"Found auth header: {header}")
                        
                        # If still no token, check response body for API calls
                        if not auth_token:
                            # Look for API calls in the JavaScript
                            api_calls = re.findall(r'X-Auth-Token["\']?\s*:\s*["\']([^"\']+)', dashboard_response.text)
                            if api_calls:
                                auth_token = api_calls[0]
                                print(f"Found X-Auth-Token in response: {auth_token[:20]}...")
                        
                        # Try to make an API call to trigger the token
                        if not auth_token:
                            print("Attempting to trigger API call to get X-Auth-Token...")
                            try:
                                # Make a request to Tinder's API to trigger authentication
                                api_url = "https://api.gotinder.com/v2/profile"
                                api_response = self.session.get(api_url)
                                
                                if api_response.status_code == 200:
                                    # Check if we got a token in the response
                                    token_match = re.search(r'X-Auth-Token["\']?\s*:\s*["\']([^"\']+)', api_response.text)
                                    if token_match:
                                        auth_token = token_match.group(1)
                                        print(f"Found X-Auth-Token in API response: {auth_token[:20]}...")
                                    else:
                                        # Check response headers
                                        for header, value in api_response.headers.items():
                                            if 'auth' in header.lower() or 'token' in header.lower():
                                                print(f"Found auth header: {header}: {value[:20]}...")
                                                if 'x-auth-token' in header.lower():
                                                    auth_token = value
                                                    break
                            except Exception as e:
                                print(f"API call failed: {e}")
                        
                        if auth_token:
                            print("✅ Successfully extracted X-Auth-Token!")
                            return auth_token
                        else:
                            print("Could not extract X-Auth-Token automatically")
                            print("Please check the Network tab in your browser and copy the X-Auth-Token header")
                            print("Or provide it manually:")
                            token = input("Enter your X-Auth-Token: ").strip()
                            if token:
                                return token
                            return None
                    else:
                        print(f"Failed to access dashboard: {dashboard_response.status_code}")
                        return None
                else:
                    print("Tinder login failed - check credentials")
                    return None
            else:
                print(f"Login request failed: {login_response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error during Tinder authentication: {e}")
            print("Falling back to manual token input...")
            token = input("Enter your X-Auth-Token manually: ").strip()
        if token:
            return token
        return None
    
    def get_tinder_auth_token(self, facebook_token):
        """Get Tinder auth token using Facebook token"""
        print("Getting Tinder auth token...")
        
        try:
            # Tinder API endpoint for Facebook authentication
            url = "https://api.gotinder.com/v2/auth/login/facebook"
            
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Tinder/3.0.4 (iPhone; iOS 7.1; Scale/2.00)'
            }
            
            data = {
                'token': facebook_token
            }
            
            response = self.session.post(url, json=data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if 'data' in result and 'api_token' in result['data']:
                    auth_token = result['data']['api_token']
                    print("Successfully obtained Tinder auth token")
                    return auth_token
                else:
                    print("No auth token in response")
                    print(f"Response: {result}")
                    return None
            else:
                print(f"Failed to get auth token: HTTP {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"Error getting auth token: {e}")
            return None
    
    def test_tinder_connection(self, auth_token):
        """Test Tinder API connection with auth token"""
        print("Testing Tinder API connection...")
        
        try:
            headers = {
                "X-Auth-Token": auth_token,
                "Content-type": "application/json"
            }
            
            response = self.session.get(
                "https://api.gotinder.com/v2/profile?include=account%2Cuser",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                profile_data = response.json()
                if 'data' in profile_data and 'user' in profile_data['data']:
                    user = profile_data['data']['user']
                    print("Tinder API connection successful!")
                    print(f"Logged in as: {user.get('name', 'Unknown')}")
                    return True
                else:
                    print("Invalid profile response")
                    return False
            else:
                print(f"API test failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
    
    def manual_setup(self):
        """Manual setup process"""
        print("Tinder Setup - Manual Mode")
        print("=" * 40)
        
        # Get credentials
        print("\nEnter your Tinder login credentials:")
        email = input("Email: ").strip()
        password = getpass.getpass("Password: ").strip()
        
        if not email or not password:
            print("Email and password are required")
            return False
        
        print(f"\nAttempting to authenticate with Tinder using email: {email}")
        
        # Get Tinder X-Auth-Token directly
        auth_token = self.get_tinder_x_auth_token(email, password)
        if not auth_token:
            print("Failed to get Tinder X-Auth-Token")
            return False
        
        # Test connection
        if not self.test_tinder_connection(auth_token):
            print("Connection test failed")
            return False
        
        # Update config
        config = self.load_config()
        config['tinder-auth-token'] = auth_token
        config['tinder-credentials'] = {
            'email': email,
            'last_updated': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if self.save_config(config):
            print("Configuration updated successfully!")
            return True
        else:
            print("Failed to save configuration")
            return False
    
    def automatic_setup(self):
        """Fully automatic setup using stored credentials"""
        print("Tinder Setup - Automatic Configuration")
        print("=" * 40)
        
        config = self.load_config()
        
        # Check if we have stored credentials
        if 'tinder-credentials' not in config or 'email' not in config['tinder-credentials']:
            print("No stored credentials found. Please run manual setup first.")
            return False
        
        email = config['tinder-credentials']['email']
        
        print(f"Using stored credentials for: {email}")
        print("Note: Password not stored for security. Please enter it:")
        password = getpass.getpass("Password: ").strip()
        
        if not password:
            print("Password required for automatic setup")
            return False
        
        # Get Tinder X-Auth-Token automatically
        tinder_token = self.get_tinder_x_auth_token(email, password)
        if not tinder_token:
            print("Failed to get Tinder X-Auth-Token automatically")
            return False
        
        # Test connection automatically
        if not self.test_tinder_connection(tinder_token):
            print("Failed to test Tinder connection automatically")
            return False
        
        # Update config with new token
        config['tinder-auth-token'] = tinder_token
        config['tinder-credentials']['last_updated'] = time.strftime('%Y-%m-%d %H:%M:%S')
        
        if self.save_config(config):
            print("Automatic setup completed successfully!")
            print("New Tinder auth token obtained and saved")
            return True
        else:
            print("Failed to save configuration")
            return False
    
    def auto_setup_trigger(self):
        """Automatically trigger setup when API fails"""
        print("Auto-setup triggered due to API failure")
        
        # Check if we have stored credentials
        config = self.load_config()
        credentials = config.get('tinder-credentials', {})
        
        if credentials.get('email'):
            print(f"Found stored email: {credentials['email']}")
            retry = input("Retry with stored credentials? (y/N): ").strip().lower()
            
            if retry == 'y':
                return self.manual_setup()
        
        # Ask user if they want to set up now
        setup_now = input("Would you like to set up Tinder authentication now? (y/N): ").strip().lower()
        
        if setup_now == 'y':
            return self.manual_setup()
        else:
            print("Setup skipped. Bot may not function properly.")
            return False
    
    def check_auth_token_validity(self):
        """Check if current auth token is valid"""
        config = self.load_config()
        auth_token = config.get('tinder-auth-token')
        
        if not auth_token:
            print("No auth token found in config")
            return False
        
        return self.test_tinder_connection(auth_token)
    
    def get_user_profile(self):
        """Get current user profile"""
        config = self.load_config()
        auth_token = config.get('tinder-auth-token')
        
        if not auth_token:
            print("No auth token found")
            return None
        
        try:
            headers = {
                "X-Auth-Token": auth_token,
                "Content-type": "application/json"
            }
            
            response = self.session.get(
                "https://api.gotinder.com/v2/profile?include=account%2Cuser",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to get profile: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error getting profile: {e}")
            return None

def main():
    """Test Tinder setup"""
    setup = TinderSetup()
    
    print("Tinder Setup System")
    print("=" * 40)
    
    # Check current token
    print("Checking current auth token...")
    if setup.check_auth_token_validity():
        print("Current auth token is valid")
        
        # Get profile info
        profile = setup.get_user_profile()
        if profile and 'data' in profile and 'user' in profile['data']:
            user = profile['data']['user']
            print(f"Current user: {user.get('name', 'Unknown')}")
            print(f"Age: {user.get('age', 'Unknown')}")
            print(f"Location: {user.get('city', {}).get('name', 'Unknown')}")
    else:
        print("Current auth token is invalid or missing")
        
        # Offer setup
        setup_now = input("\nWould you like to set up authentication? (y/N): ").strip().lower()
        if setup_now == 'y':
            setup.manual_setup()

if __name__ == "__main__":
    main()
