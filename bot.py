
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)
import asyncio
from helpers import get_params
from controller.leaderboard import get_broadcasts
from controller.advertise import get_advertise
from config import BOT_TOKEN
from models import Setting

class ShillmasterTelegramBot:

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    def __init__(self):
        logging.info("Bot init")
        asyncio.get_event_loop().create_task(self.leaderboard())
    
    async def _leaderboard(self):
        broadcasts = get_broadcasts()
        advertise = get_advertise()
        reply_markup=""
        if advertise != None:
            keyboard = [
                [InlineKeyboardButton(text=f"🐶 ‼ {advertise['text']} ‼ 🐶", url=advertise['url'])],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
        
        for item in broadcasts:
            logging.info(item['message_id'])
            # try:
            #     await self.application.bot.edit_message_text(
            #         chat_id=item['chat_id'],
            #         message_id=item['message_id'],
            #         text=item['text'],
            #         disable_web_page_preview=True,
            #         reply_markup=reply_markup,
            #         parse_mode='HTML'
            #     )
            # except:
            #     logging.info("error")
                # await self.application.bot.send_message(chat_id=item['chat_id'], text=item['text'], parse_mode='HTML')
                # update_leaderboard(item['_id'], {"message_id": result['message_id']})

    async def leaderboard(self):
        while True:
            await asyncio.sleep(100)
            asyncio.create_task(self._leaderboard())

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        await context.bot.send_message(chat_id=chat_id, text="Start Message")
    
    async def _shillmode(self, receive_text, chat_id, context: ContextTypes.DEFAULT_TYPE):
        param = get_params(receive_text, "/shillmode")
        is_shill = True
        is_shill_str = "On"
        logging.info(param)
        if param == "off":
            is_shill = False
            is_shill_str = "Off"

        setting = Setting.find_one({"master": "master"})
        if setting != None:
            Setting.find_one_and_update({"_id": setting['_id']}, {"$set": {"shill_mode": is_shill}})
        else:
            setting = {"master": "master","shill_mode": is_shill}
            Setting.insert_one(setting)
        
        return await context.bot.send_message(chat_id=chat_id, text=f"Shill Mode Turned {is_shill_str}")

    async def shillmode(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        receive_text = update.message.text
        chat_id = update.effective_chat.id
        asyncio.get_event_loop().create_task(self._shillmode(receive_text, chat_id, context))

        return None

    async def _banmode(self, receive_text, chat_id, context: ContextTypes.DEFAULT_TYPE):
        param = get_params(receive_text, "/banmode")
        is_ban = True
        is_ban_str = "On"
        logging.info(param)
        if param == "off":
            is_ban = False
            is_ban_str = "Off"

        setting = Setting.find_one({"master": "master"})
        if setting != None:
            Setting.find_one_and_update({"_id": setting['_id']}, {"$set": {"ban_mode": is_ban}})
        else:
            setting = {"master": "master","ban_mode": is_ban}
            Setting.insert_one(setting)
        
        return await context.bot.send_message(chat_id=chat_id, text=f"Ban Mode Turned {is_ban_str}")

    async def banmode(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        receive_text = update.message.text
        chat_id = update.effective_chat.id
        asyncio.get_event_loop().create_task(self._banmode(receive_text, chat_id, context))

        return None
    
    def run(self):
        self.application.add_handler(CommandHandler(["start", "help"], self.start))
        self.application.add_handler(MessageHandler(filters.Regex("/shillmode@(s)?"), self.shillmode))
        self.application.add_handler(MessageHandler(filters.Regex("/banmode@(s)?"), self.banmode))
        self.application.run_polling()