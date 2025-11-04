# api/bot_services.py
import logging
import httpx  # <-- Import httpx instead of requests
from telegram import Update
from telegram.ext import ContextTypes

# Import our validated configuration
from . import config

logger = logging.getLogger(__name__)

# --- start and notify_admin functions (NO CHANGE) ---

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

# --- THIS IS THE UPDATED FUNCTION ---

async def correct_grammar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles a text message, sends it to the grammar API, and returns the correction.
    This version uses httpx for non-blocking async requests.
    """
    user_text = update.message.text
    chat_id = update.effective_chat.id
    logger.info(f"Received text from {chat_id} for correction.")

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        # --- VCSM: Call the External Service (Asynchronously) ---
        
        # 1. Prepare the JSON payload
        payload = {"text": user_text}
        
        # 2. Define a 9-second timeout
        timeout = httpx.Timeout(9.0, connect=5.0)

        # 3. Use an AsyncClient to make the request
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                config.GRAMMAR_ENDPOINT_URL,
                json=payload
            )

        # 4. Handle the response (non-blocking)
        # Raise an exception for 4xx/5xx errors
        response.raise_for_status() 
        
        data = response.json()
        corrected_text = data.get("correctedText")

        if corrected_text:
            await update.message.reply_text(corrected_text)
        else:
            raise Exception("API returned an empty or invalid response.")

    except httpx.TimeoutException:
        logger.error(f"HTTP Request to {config.GRAMMAR_ENDPOINT_URL} timed out.")
        await update.message.reply_text("Error: El servicio de corrección tardó mucho en responder. Inténtalo de nuevo.")
    except httpx.RequestError as e:
        # Handle network-level errors (connection error, DNS, etc.)
        logger.error(f"HTTP Request failed: {e}")
        await update.message.reply_text("Error: No se pudo conectar con el servicio de corrección.")
    except httpx.HTTPStatusError as e:
        # Handle 4xx/5xx errors from the grammar API
        try:
            # Try to get the JSON error message from the API
            error_msg = e.response.json().get("error", e.response.text)
        except Exception:
            error_msg = e.response.text
        logger.error(f"Grammar API Error ({e.response.status_code}): {error_msg}")
        await update.message.reply_text(f"Error al corregir: {error_msg}")
    except Exception as e:
        # Handle all other errors (JSON parsing, RuntimeError, etc.)
        logger.error(f"General error in correct_grammar: {e}")
        await update.message.reply_text(f"Ha ocurrido un error inesperado: {e}")