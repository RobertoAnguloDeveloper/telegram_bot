# api/index.py
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
# Import BackgroundTasks
from fastapi import FastAPI, Request, BackgroundTasks 

# Import our new modules. The 'from .' makes it a relative import.
from . import config
from . import bot_services

# --- 1. Logging Setup ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- 2. Bot Application Setup (Links to Service Layer) ---
# We initialize the application using the TOKEN from our config file
application = (
    Application.builder()
    .token(config.TOKEN)
    .build()
)

# Add handlers, pointing to the functions in our bot_services.py file
application.add_handler(CommandHandler("start", bot_services.start))
application.add_handler(CommandHandler("notify", bot_services.notify_admin))

# **This is the key change**: We replaced 'echo' with our new 'correct_grammar' function
application.add_handler(MessageHandler(
    filters.TEXT & ~filters.COMMAND, 
    bot_services.correct_grammar
))

# --- 3. FastAPI App Setup (Controller Layer) ---
app = FastAPI()

# --- THIS IS THE UPDATED FUNCTION ---
@app.post("/")
async def handle_update(request: Request, background_tasks: BackgroundTasks):
    """
    Main webhook endpoint.
    It receives an update from Telegram, adds the processing of that 
    update to BackgroundTasks, and returns "ok" immediately.
    """
    try:
        # We must initialize the app on each request for serverless
        await application.initialize()
        data = await request.json()
        update = Update.de_json(data, application.bot)
        
        # This is the crucial change:
        # Instead of awaiting the long-running task, we add it
        # to the background worker.
        # FastAPI will await the coroutine for us.
        background_tasks.add_task(application.process_update, update=update)
        
        # Return "ok" to Telegram immediately
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error in handle_update: {e}")
        # Even on error, we must return a 200 to Telegram
        return {"status": "error", "message": str(e)}

@app.get("/set_webhook")
async def set_webhook():
    """One-time endpoint to set the bot's webhook to this Vercel URL."""
    try:
        await application.initialize()
        # Use the VERCEL_URL from our config file
        webhook_url = f"{config.VERCEL_URL}" 
        await application.bot.set_webhook(webhook_url)
        
        # Notify admin on successful setup
        await application.bot.send_message(
            chat_id=config.ADMIN_CHAT_ID,
            text=f"Webhook configurado exitosamente en: {webhook_url}"
        )
        return f"Webhook set successfully to: {webhook_url}"
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        return f"Error setting webhook: {e}"