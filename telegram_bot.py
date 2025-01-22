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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def start(update, context):
    """Start command handler"""
    await update.message.reply_text(
        "Welcome! I'm here to help you post comments.\n"
        "Use /comment to start commenting!"
    )

async def comment(update, context):
    """Inicia o processo de comentário"""
    logger.info("Comando /comment recebido")
    
    await update.message.reply_text(
        "Please send me the mint ID or pump.fun URL where you want to comment.\n"
        "Example: 4TgsKLurtR71jMoVMC3Un3V3fdNRFwX6Dj9ny1T9pump\n"
        "Or: https://pump.fun/coin/4TgsKLurtR71jMoVMC3Un3V3fdNRFwX6Dj9ny1T9pump"
    )
    return ESCOLHER_QUANTIDADE

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

async def get_mint_id(update, context):
    """Processa o mint ID e pede a quantidade"""
    logger.info("Recebido possível mint ID")
    
    raw_mint_id = update.message.text.strip()
    mint_id = clean_mint_id(raw_mint_id)
    
    if not mint_id:
        await update.message.reply_text(
            "Invalid mint ID! Please send a valid mint ID or pump.fun URL\n"
            "Example mint ID: 4TgsKLurtR71jMoVMC3Un3V3fdNRFwX6Dj9ny1T9pump\n"
            "Example URL: https://pump.fun/coin/4TgsKLurtR71jMoVMC3Un3V3fdNRFwX6Dj9ny1T9pump"
        )
        return ESCOLHER_QUANTIDADE
    
    context.user_data['mint_id'] = mint_id
    logger.info(f"Valid mint ID: {mint_id}")
    
    # Criar botões inline para quantidade
    keyboard = [
        [InlineKeyboardButton("1", callback_data='1'),
         InlineKeyboardButton("2", callback_data='2'),
         InlineKeyboardButton("3", callback_data='3')],
        [InlineKeyboardButton("5", callback_data='5'),
         InlineKeyboardButton("10", callback_data='10'),
         InlineKeyboardButton("20", callback_data='20')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Valid mint ID! Now choose how many comments you want to make:",
        reply_markup=reply_markup
    )
    return ESCOLHER_QUANTIDADE

async def process_quantity(update, context):
    query = update.callback_query
    await query.answer()
    
    try:
        mint_id = context.user_data.get('mint_id')
        if not mint_id:
            await query.message.reply_text("Error: Mint ID not found. Please use /comment again.")
            return ConversationHandler.END
            
        num_comentarios = int(query.data)
        logger.info(f"Starting bot...")
        logger.info(f"Processing {num_comentarios} comments for mint ID: {mint_id}")
        
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
            
        comentarios = [
            "Amazing project",
            "Great work",
            "Love this project",
            "Fantastic project",
            "Impressive work",
            "This is brilliant",
            "Excellent project",
            "Super excited about this"
        ]
        
        # Initialize bot
        logger.info("Initializing bot with settings...")
        bot = CommentBot(
            config_path="config.json",
            delay_range=(1, 3),
            proxies=None
        )
        
        await query.message.reply_text(f"Starting {num_comentarios} comments... Check console for progress.")
        
        sucessos = 0
        for i in range(num_comentarios):
            comentario = random.choice(comentarios)
            logger.info(f"Comment to be posted ({i+1}/{num_comentarios}): {comentario}")
            
            try:
                success = bot.post_comment(mint_id, comentario)
                if success:
                    sucessos += 1
                    logger.info(f"Comment {i+1}/{num_comentarios} posted successfully on mint {mint_id}")
                else:
                    logger.error(f"Failed to post comment {i+1}/{num_comentarios} on mint {mint_id}")
            except Exception as e:
                logger.error(f"Error posting comment {i+1}/{num_comentarios}: {str(e)}")
                
        logger.info(f"Process finished. {sucessos}/{num_comentarios} comments posted successfully")
        await query.message.reply_text(f"Process finished. {sucessos}/{num_comentarios} comments posted successfully.")
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Critical error in process: {str(e)}")
        await query.message.reply_text("An error occurred.")
        return ConversationHandler.END

def main():
    """Start the bot"""
    # Carrega config
    with open("config.json", "r") as f:
        config = json.load(f)
    
    # Create application
    application = Application.builder().token(config['telegram_token']).build()

    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('comment', comment)],
        states={
            ESCOLHER_QUANTIDADE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_mint_id),
                CallbackQueryHandler(process_quantity)
            ]
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