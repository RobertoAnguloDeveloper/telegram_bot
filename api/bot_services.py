# api/bot_services.py
import logging
import httpx  # <-- Import httpx instead of requests
from telegram import Update
from telegram.ext import ContextTypes

# Import our validated configuration
from . import config

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    logger.info(f"User {user.first_name} (ID: {user.id}) started a chat. Chat_ID is: {chat_id}")
    await update.message.reply_text(
        f"¡Hola {user.first_name}!\n\n"
        f"Envíame cualquier texto y yo lo corregiré (gramática y ortografía) "
        f"y lo traduciré a inglés americano estándar.\n\n"
        f"Tu `chat_id` es: {chat_id}\n"
    )

async def notify_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /notify command."""
    trigger_user = update.effective_user.first_name
    admin_id = config.ADMIN_CHAT_ID
    logger.info(f"Command /notify triggered by {trigger_user}. Sending message to ADMIN_ID: {admin_id}")
    try:
        await context.bot.send_message(
            chat_id=admin_id,
            text=f"¡Hola Admin! El usuario {trigger_user} acaba de usar el comando /notify."
        )
        await update.message.reply_text("Notificación enviada al admin.")
    except Exception as e:
        logger.error(f"Failed to send message to {admin_id}: {e}")
        await update.message.reply_text(f"Error: No se pudo enviar el mensaje al admin.")

async def correct_grammar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles a text message, sends it to the grammar API, and returns the correction.
    This function is now fully asynchronous using httpx.
    """
    user_text = update.message.text
    chat_id = update.effective_chat.id
    logger.info(f"Received text from {chat_id} for correction.")

    # Show a "typing..." status in Telegram to show work is being done
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        # --- VCSM: Call the External Service Asynchronously ---
        
        # 1. Prepare the JSON payload for the "Grammar Fix" API
        payload = {"text": user_text}
        
        # 2. Use an async client to call the endpoint
        async with httpx.AsyncClient() as client:
            response = await client.post(
                config.GRAMMAR_ENDPOINT_URL, 
                json=payload, 
                timeout=25.0 # Set a 25-second timeout
            )
        
        # 3. Handle the response
        response.raise_for_status() # Raises an exception for 4xx or 5xx status codes
        
        corrected_text = response.json().get("correctedText")
        if corrected_text:
            await update.message.reply_text(corrected_text)
        else:
            raise Exception("API returned an empty or invalid response.")

    except httpx.TimeoutException:
        logger.error(f"HTTP Request to {config.GRAMMAR_ENDPOINT_URL} timed out.")
        await update.message.reply_text("Error: El servicio de corrección tardó mucho en responder. Inténtalo de nuevo.")
    except httpx.RequestError as e:
        # Handle network-level errors (e.g., connection error)
        logger.error(f"HTTP Request failed: {e}")
        await update.message.reply_text("Error: No se pudo conectar con el servicio de corrección.")
    except httpx.HTTPStatusError as e:
        # Handle API error responses (4xx, 5xx)
        try:
            error_msg = e.response.json().get("error", e.response.text)
        except:
            error_msg = e.response.text
        logger.error(f"Grammar API Error ({e.response.status_code}): {error_msg}")
        await update.message.reply_text(f"Error al corregir: {error_msg}")
    except Exception as e:
        # Handle other errors (JSON parsing, etc.)
        logger.error(f"General error in correct_grammar: {e}")
        await update.message.reply_text(f"Ha ocurrido un error inesperado: {e}")
