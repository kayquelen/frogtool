from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import json
import time
import random
import string
import logging
import zipfile
import imaplib
import email
import re
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AccountCreator:
    def __init__(self, proxy=None, email_settings=None):
        """Initialize account creator with proxy and email settings"""
        self.base_url = "https://pump.fun"
        self.proxy = proxy
        self.email_settings = email_settings
        self.driver = None
        self.short_wait = None
        self.initialize_driver()
        
    def initialize_driver(self):
        """Initialize Chrome driver with necessary settings"""
        chrome_options = Options()
        
        # Basic settings
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Disable Google services and optimization
        chrome_options.add_argument('--disable-features=OptimizationHints')
        chrome_options.add_argument('--disable-features=OptimizationGuideModelDownloading')
        chrome_options.add_argument('--disable-features=OptimizationHintsFetching')
        chrome_options.add_argument('--disable-features=OptimizationTargetPrediction')
        chrome_options.add_argument('--disable-domain-reliability')
        chrome_options.add_argument('--disable-breakpad')
        chrome_options.add_argument('--disable-component-update')
        chrome_options.add_argument('--disable-default-apps')
        chrome_options.add_argument('--disable-sync')
        chrome_options.add_argument('--disable-background-networking')

        # Configure proxy if available
        if self.proxy:
            manifest_json = """
            {
                "version": "1.0.0",
                "manifest_version": 2,
                "name": "Chrome Proxy",
                "permissions": [
                    "proxy",
                    "tabs",
                    "unlimitedStorage",
                    "storage",
                    "<all_urls>",
                    "webRequest",
                    "webRequestBlocking"
                ],
                "background": {
                    "scripts": ["background.js"]
                },
                "minimum_chrome_version":"22.0.0"
            }
            """

            background_js = """
            var config = {
                    mode: "fixed_servers",
                    rules: {
                    singleProxy: {
                        scheme: "http",
                        host: "%s",
                        port: parseInt(%s)
                    },
                    bypassList: ["localhost"]
                    }
                };

            chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

            function callbackFn(details) {
                return {
                    authCredentials: {
                        username: "%s",
                        password: "%s"
                    }
                };
            }

            chrome.webRequest.onAuthRequired.addListener(
                        callbackFn,
                        {urls: ["<all_urls>"]},
                        ['blocking']
            );
            """ % (self.proxy['host'], self.proxy['port'], 
                   self.proxy['username'], self.proxy['password'])

            pluginfile = 'proxy_auth_plugin.zip'
            with zipfile.ZipFile(pluginfile, 'w') as zp:
                zp.writestr("manifest.json", manifest_json)
                zp.writestr("background.js", background_js)
            
            chrome_options.add_extension(pluginfile)
            logger.info(f"Proxy configured: {self.proxy['host']}:{self.proxy['port']}")

        # Initialize driver
        self.driver = webdriver.Chrome(options=chrome_options)
        self.short_wait = WebDriverWait(self.driver, 5)
        logger.info("Chrome driver initialized")

    def get_verification_code(self):
        """Wait for user to input verification code"""
        try:
            print("\n🔍 Por favor, verifique seu Gmail e cole o código de 6 dígitos aqui:")
            code = input("Código: ").strip()
            
            # Validate that it's a 6 digit code
            if re.match(r'^\d{6}$', code):
                return code
            else:
                print("❌ Código inválido! Precisa ser 6 dígitos.")
                return self.get_verification_code()  # try again

        except Exception as e:
            logger.error(f"Error getting verification code: {str(e)}")
            return None

    def create_account(self):
        """Create a new account on pump.fun"""
        try:
            # Navigate to site
            self.driver.get(self.base_url)
            time.sleep(2)  # wait for page load

            # First click "I'm ready to pump"
            ready_button = self.short_wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 
                    'button[data-sentry-element="Button"][data-sentry-source-file="HowItWorks.tsx"]'))
            )
            ready_button.click()
            logger.info("Clicked 'I'm ready to pump'")
            time.sleep(1)  # wait for animation

            # Wait for overlay to disappear
            try:
                overlay = self.driver.find_element(By.CSS_SELECTOR, "div[data-state='open'].fixed.inset-0")
                if overlay.is_displayed():
                    time.sleep(2)  # wait for overlay animation
            except:
                pass  # overlay not found, continue

            # Click connect wallet button
            connect_button = self.short_wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 
                    'button[data-sentry-element="DialogTrigger"][data-sentry-source-file="Wallet.tsx"]'))
            )
            self.driver.execute_script("arguments[0].click();", connect_button)  # use JS click
            logger.info("Clicked 'Connect Wallet'")
            time.sleep(1)  # wait for modal

            # Enter email
            email_address = self.email_settings['username']
            email_input = self.short_wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#email-input"))
            )
            email_input.send_keys(email_address)
            logger.info(f"Email entered: {email_address}")

            # Click submit using the span text
            submit_button = self.short_wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Submit']"))
            )
            self.driver.execute_script("arguments[0].click();", submit_button)
            logger.info("Clicked submit")
            
            print(f"\n✉️ Email de verificação enviado para: {email_address}")
            
            # Get verification code from user input
            code = self.get_verification_code()
            if not code:
                logger.error("Could not get verification code")
                return None

            # Enter verification code
            code_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
            for i, digit in enumerate(code):
                if i < len(code_inputs):
                    code_inputs[i].send_keys(digit)
            logger.info("Verification code entered")

            # Wait for verification
            time.sleep(3)

            # Wait for account creation to complete
            time.sleep(3)

            # Get JWT token
            jwt_token = self.driver.get_cookie('jwt')
            if jwt_token:
                token = jwt_token['value']
                logger.info("Account created successfully")
                
                # Save token to config
                self.save_token(token)
                
                return {
                    'email': email_address,
                    'jwt_token': token
                }
            
            logger.error("Could not get JWT token")
            return None

        except Exception as e:
            logger.error(f"Error creating account: {str(e)}")
            return None

    def save_token(self, token):
        """Save JWT token to config file"""
        try:
            config_file = 'config.json'
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
            else:
                config = {}

            if 'jwt_tokens' not in config:
                config['jwt_tokens'] = []
            
            config['jwt_tokens'].append(token)

            with open(config_file, 'w') as f:
                json.dump(config, f, indent=4)
            
            logger.info("Token saved to config.json")

        except Exception as e:
            logger.error(f"Error saving token: {str(e)}")

    def close(self):
        """Close browser"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser closed successfully")
            except Exception as e:
                logger.error(f"Error closing browser: {str(e)}")

    def __del__(self):
        """Destructor"""
        self.close()

if __name__ == "__main__":
    # Load config
    with open("config.json", "r") as f:
        config = json.load(f)

    # Create account with proxy and email settings
    creator = AccountCreator(
        proxy=config.get('proxy'),
        email_settings=config.get('email_settings')
    )

    try:
        result = creator.create_account()
        if result:
            print(f"✅ Account created successfully!")
            print(f"Email: {result['email']}")
            print(f"JWT Token: {result['jwt_token']}")
        else:
            print("❌ Failed to create account")
    finally:
        creator.close()
