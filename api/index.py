import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- Framework web ---
from fastapi import FastAPI, Request
import uvicorn

# --- CONFIGURATION ---
TOKEN = "8500888325:AAFL7F1D1jKex7sC6wpeI6hcDaw41A2gKmo"
ADMIN_CHAT_ID = 1581506880

# URL de Vercel (¡IMPORTANTE! Cámbiala después de desplegar)
VERCEL_URL = "https://telegram-bot-delta-orpin.vercel.app"
# --- END CONFIGURATION ---

# Configura logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


# --- TUS FUNCIONES DE BOT (Sin cambios) ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    logger.info(f"User {user.first_name} (ID: {user.id}) started a chat. Chat_ID is: {chat_id}")
    await update.message.reply_text(
        f"¡Hola {user.first_name}!\n"
        f"Envíame un mensaje y te lo repetiré.\n\n"
        f"Tu `chat_id` es: {chat_id}\n"
    )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Echoing message from chat_id: {update.effective_chat.id}")
    await update.message.reply_text(update.message.text)

async def notify_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


# --- LÓGICA DE WEBHOOKS (La parte nueva) ---

# 1. Inicializar la aplicación de bot (sin JobQueue)
# JobQueue no funciona en serverless, ya que no hay procesos persistentes.
application = (
    Application.builder()
    .token(TOKEN)
    .build()
)

# 2. Añadir manejadores (igual que antes)
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("notify", notify_admin))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# 3. Inicializar la aplicación FastAPI
app = FastAPI()

# 4. Endpoint principal para recibir actualizaciones de Telegram
@app.post("/")
async def handle_update(request: Request):
    """Maneja las actualizaciones entrantes de Telegram."""
    try:
        # Inicializar la app de bot (necesario en serverless)
        await application.initialize()
        
        # Procesar la actualización
        data = await request.json()
        update = Update.de_json(data, application.bot)
        await application.process_update(update)
        
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error processing update: {e}")
        return {"status": "error"}

# 5. Endpoint para configurar el Webhook (SOLO LO USARÁS UNA VEZ)
@app.get("/set_webhook")
async def set_webhook():
    """Configura el webhook de Telegram apuntando a esta app Vercel."""
    try:
        await application.initialize()
        webhook_url = f"{VERCEL_URL}"
        
        # Le decimos a Telegram dónde enviar las actualizaciones
        await application.bot.set_webhook(webhook_url)
        
        return f"¡Webhook configurado exitosamente en: {webhook_url}!"
    except Exception as e:
        return f"Error al configurar el webhook: {e}"

# Nota: La función send_startup_message fue eliminada
# porque JobQueue.run_once() no es compatible con serverless.
# Si necesitas una notificación de inicio, puedes hacer que 
# el endpoint /set_webhook también te envíe un mensaje.