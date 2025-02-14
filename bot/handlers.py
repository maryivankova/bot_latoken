# handlers.py
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters

async def start(update: Update, context) -> None:
    await update.message.reply_text('Привет! Я ваш Telegram-бот. Чем могу помочь?')

async def help_command(update: Update, context) -> None:
    await update.message.reply_text('Я могу ответить на ваши сообщения. Просто напишите мне что-нибудь.')

async def echo(update: Update, context) -> None:
    await update.message.reply_text(f'Вы написали: {update.message.text}')

def register_handlers(application):
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))