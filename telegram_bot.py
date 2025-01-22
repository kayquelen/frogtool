import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from commenter import CommentBot
import json
import random
import os
from datetime import datetime

# Estados
MINT_ID = 0
ESCOLHER_QUANTIDADE = 1
CHOOSE_QUANTITY = ESCOLHER_QUANTIDADE

# Configuração de logs
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, f"bot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()  # Mostra logs no console também
    ]
)

logger = logging.getLogger(__name__)

async def start(update, context):
    """Start command handler"""
    await update.message.reply_text(
        "👋 Welcome! I'm here to help you post comments.\n"
        "Use /comment to start commenting!"
    )

async def comment(update, context):
    """Handler for the /comment command"""
    logger.info(f"Comando /comment recebido de {update.effective_user.id}")
    await update.message.reply_text(
        "Please send me the mint ID or pump.fun URL where you want to comment.\n"
        "Example: 4TgsKLurtR71jMoVMC3Un3V3fdNRFwX6Dj9ny1T9pump\n"
        "Or: https://pump.fun/coin/4TgsKLurtR71jMoVMC3Un3V3fdNRFwX6Dj9ny1T9pump"
    )
    return MINT_ID

def extract_mint_id(text):
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

async def process_mint_id(update, context):
    mint_id = extract_mint_id(update.message.text)
    if not mint_id:
        await update.message.reply_text(
            "❌ Invalid mint ID! Please send a valid mint ID or pump.fun URL\n"
            "Example mint ID: 4TgsKLurtR71jMoVMC3Un3V3fdNRFwX6Dj9ny1T9pump\n"
            "Example URL: https://pump.fun/coin/4TgsKLurtR71jMoVMC3Un3V3fdNRFwX6Dj9ny1T9pump"
        )
        return MINT_ID
    
    context.user_data['mint_id'] = mint_id
    logger.info(f"Mint ID received: {mint_id}")
    
    # Create inline keyboard with quantity options
    keyboard = [
        [InlineKeyboardButton("1", callback_data='1'),
         InlineKeyboardButton("2", callback_data='2'),
         InlineKeyboardButton("3", callback_data='3')],
        [InlineKeyboardButton("5", callback_data='5'),
         InlineKeyboardButton("10", callback_data='10')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"✅ Valid mint ID! Now choose how many comments you want to make:",
        reply_markup=reply_markup
    )
    
    return ESCOLHER_QUANTIDADE

async def process_quantity(update, context):
    query = update.callback_query
    await query.answer()
    
    try:
        mint_id = context.user_data.get('mint_id')
        if not mint_id:
            await query.message.reply_text("❌ Error: Mint ID not found. Please use /comment again.")
            return ConversationHandler.END
            
        num_comments = int(query.data)
        logger.info(f"Starting process for {num_comments} comments on mint {mint_id}")
        
        # Execute test_commenter.py with parameters
        import subprocess
        import sys
        import os

        for i in range(num_comments):
            try:
                logger.info(f"Executing comment {i+1} of {num_comments}")
                
                # Configure environment variables for test_commenter
                env = os.environ.copy()
                env['MINT_ID'] = mint_id
                
                # Execute test_commenter.py
                process = subprocess.Popen(
                    [sys.executable, 'test_commenter.py'],
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                
                # Read output in real-time
                success = False
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        output = output.strip()
                        logger.info(output)  
                        if "✅ Comment posted successfully" in output:
                            success = True
                
                # Get return code 
                return_code = process.poll()
                    
            except Exception as e:
                logger.error(f"Error executing test_commenter.py: {str(e)}")
        
        # Only show final message
        await query.message.reply_text(f"✅ Process completed! {num_comments} comments processed.")
        
    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
    
    return ConversationHandler.END

def main():
    """Start the bot"""
    # Carrega config
    with open("config.json", "r") as f:
        config = json.load(f)
    
    # Create application
    application = Application.builder().token(config['telegram_token']).build()

    # Add conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('comment', comment)],
        states={
            MINT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_mint_id)],
            ESCOLHER_QUANTIDADE: [CallbackQueryHandler(process_quantity)]
        },
        fallbacks=[CommandHandler('cancel', lambda u,c: ConversationHandler.END)]
    )
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)
    
    # Log de início
    logger.info("Bot iniciado! Pressione Ctrl+C para parar.")
    
    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()