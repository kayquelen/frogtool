from commenter import CommentBot
import logging
import json
import time
import os
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def clean_mint_id(text):
    """Extracts mint ID from URL or direct mint ID"""
    logger.info(f"Received text: {text}")
    
    # If it's a pump.fun URL
    if "pump.fun/coin/" in text:
        # Get the last part after /coin/
        mint_id = text.split("/coin/")[-1].strip()
        # Remove anything after pump
        mint_id = mint_id.split("pump")[0] + "pump"
        logger.info(f"Mint ID extracted from URL: {mint_id}")
        return mint_id
        
    # If it's already a mint ID (44 chars ending in pump)
    elif text.endswith('pump') and len(text) == 44:
        logger.info(f"Mint ID already in correct format: {text}")
        return text
        
    logger.warning(f"Invalid format. Received text: {text}")
    return None

logger.info("Starting bot...")

# Load configuration
logger.info("Loading config.json...")
with open("config.json", "r") as f:
    config = json.load(f)

# Show proxy information
if config.get('proxies'):
    logger.info(f"Proxies found: {len(config['proxies'])}")
    for i, proxy in enumerate(config['proxies'], 1):
        logger.info(f"Proxy #{i}: {proxy['protocol']}://{proxy['host']}:{proxy['port']}")
else:
    logger.warning("No proxy configured in config.json")

# JWT token for authentication
jwt_token = config['jwt_tokens'][0]
logger.info("JWT token loaded")

# Get mint_id from environment variable or use default
raw_mint_id = os.getenv('MINT_ID', "4TgsKLurtR71jMoVMC3Un3V3fdNRFwX6Dj9ny1T9pump")
mint_id = clean_mint_id(raw_mint_id)
if not mint_id:
    logger.error(f"Invalid mint ID: {raw_mint_id}")
    exit(1)

# Initialize bot
logger.info("Initializing bot with settings...")
bot = CommentBot(
    delay_range=(1, 3),
    proxies=None
)

try:
    # Mint ID to comment on
    logger.info(f"Trying to comment on mint ID: {mint_id}")

    # Test with a single comment
    comment = "Test comment!"
    logger.info(f"Comment to be posted: {comment}")

    success = bot.post_comment(mint_id, comment)
    
    if success:
        logger.info(f"✅ Comment posted successfully on mint {mint_id}")
        # Keep browser open for 5 seconds for visual verification
        time.sleep(5)
    else:
        logger.error(f"❌ Failed to post comment on mint {mint_id}")

finally:
    # Always close browser
    bot.close()
