import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, JobQueue

# --- CONFIGURATION ---
# Replace with your bot's token
TOKEN = "8500888325:AAFL7F1D1jKex7sC6wpeI6hcDaw41A2gKmo"

# Your specific Chat ID is set here:
ADMIN_CHAT_ID = 1581506880
# --- END CONFIGURATION ---


# Configura logging (buena práctica para ver errores)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


# Función para enviar el mensaje de prueba
async def send_startup_message(context: ContextTypes.DEFAULT_TYPE):
    """
    Sends a test message to the ADMIN_CHAT_ID when the bot first starts.
    """
    try:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text="✅ ¡Bot iniciado y en línea! Este es un mensaje de prueba."
        )
        logger.info(f"Mensaje de prueba enviado a ADMIN_ID: {ADMIN_CHAT_ID}")
    except Exception as e:
        logger.error(
            f"Error al enviar mensaje de prueba a {ADMIN_CHAT_ID}: {e}. "
            "¿Has iniciado el chat con tu bot al menos una vez?"
        )

# Función para el comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Sends a welcome message and reveals the user's chat_id.
    """
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    logger.info(f"User {user.first_name} (ID: {user.id}) started a chat. Chat_ID is: {chat_id}")
    
    await update.message.reply_text(
        f"¡Hola {user.first_name}!\n"
        f"Envíame un mensaje y te lo repetiré.\n\n"
        f"Tu `chat_id` es: {chat_id}\n"
    )

# Función para "eco" (repetir mensajes)
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Repeats any text message sent by the user."""
    logger.info(f"Echoing message from chat_id: {update.effective_chat.id}")
    await update.message.reply_text(update.message.text)

# Función para notificar al admin (ejemplo)
async def notify_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    EXAMPLE: Sends a specific message to the hardcoded ADMIN_CHAT_ID.
    """
    trigger_user = update.effective_user.first_name 
    logger.info(f"Command /notify triggered by {trigger_user}. Sending message to ADMIN_ID: {ADMIN_CHAT_ID}")
    
    try:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"¡Hola Admin! El usuario {trigger_user} acaba de usar el comando /notify."
        )
        await update.message.reply_text("Notificación enviada al admin.")
        
    except Exception as e:
        logger.error(f"Failed to send message to {ADMIN_CHAT_ID}: {e}")
        await update.message.reply_text(f"Error: No se pudo enviar el mensaje al admin.")


def main():
    
    # --- CORRECCIÓN AQUÍ ---
    # 1. Crear la instancia de JobQueue PRIMERO
    job_queue = JobQueue()

    # 2. Crear la Aplicación e INYECTAR el job_queue
    application = (
        Application.builder()
        .token(TOKEN)
        .job_queue(job_queue)  # <--- Esta es la corrección
        .build()
    )
    # --- FIN DE LA CORRECCIÓN ---

    # 3. Añadir manejadores (handlers) for los comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("notify", notify_admin)) 

    # 4. Añadir manejador para mensajes de texto (que no sean comandos)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # 5. Programar el mensaje de prueba
    # Ahora 'job_queue' está garantizado que no es None
    job_queue.run_once(send_startup_message, when=1) 

    # 6. Iniciar el bot (modo "Polling")
    logger.info("Iniciando bot...")
    application.run_polling()

if __name__ == "__main__":
    main()