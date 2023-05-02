
import logging
import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    filters
)
from telegram.error import TimedOut
import asyncio
from helpers import  (
    start_text,
    get_params,
    get_baned_user,
    add_ban_user,
    remove_ban_user,
    add_warn,
    remove_warn,
    get_user_warn,
    convert_am_pm,
    format_number_string
)
from controller.leaderboard import get_broadcasts, update_leaderboard_message_id, get_removed_pairs, get_leaderboard
from controller.advertise import (
    new_advertise,
    check_available_time,
    create_invoice,
    complete_invoice,
    edit_advertise,
    check_available_hour,
    get_invoice,
    get_advertise
)
from controller.shillmaster import user_shillmaster, token_shillmaster, get_user_shillmaster
from config import BOT_TOKEN, LEADERBOARD_ID
from models import Setting

NEXT = map(chr, range(10, 22))
SHOW_HOUR, SHOW_TIME = map(chr, range(8, 10))
TEXT_TYPING = map(chr, range(8, 10))
URL_TYPING = map(chr, range(8, 10))
COOSE_TOKEN = map(chr, range(8, 10))
PAYMENT = map(chr, range(8, 10))
HASH_TYPING = map(chr, range(8, 10))
TRAN_TYPING = map(chr, range(8, 10))
END = ConversationHandler.END

class ShillmasterTelegramBot:

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    def __init__(self):
        logging.info("Bot init")
        asyncio.get_event_loop().create_task(self.leaderboard())
    
    async def _block_user(self, user):
        try:
            await self.application.bot.ban_chat_member(chat_id=user['chat_id'], user_id=user['user_id'])
            add_ban_user(user)
            remove_warn(user['username'])
        except:
            await self._send_message(chat_id=user['chat_id'], text="Can not ban @"+user['username'])

    async def _unblock_user(self, user, context):
        await context.bot.unban_chat_member(chat_id=user['chat_id'], user_id=user['user_id'])
        remove_ban_user(user)
        
    async def _send_message(self, chat_id, text, reply_markup="", disable_preview=False):
        result = await self.application.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
                disable_web_page_preview=disable_preview,
                parse_mode='HTML'
            )
        return result

    async def _edit_message(self, chat_id, message_id, text, reply_markup):
        try:
            await self.application.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                disable_web_page_preview=True,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
        except telegram.error.BadRequest as e:
            if str(e).startswith("Message is not modified"):
                return
            
            if str(e).startswith("Chat not found"):
                logging.warning(f'Failed to edit message: {str(e)}')
                # result = await self.application.bot.send_message(chat_id=item['chat_id'], text=item['text'], disable_web_page_preview=True, reply_markup=reply_markup, parse_mode='HTML')
                # update_leaderboard_message_id(item['_id'], result['message_id'])
                return
        except TimedOut:
            logging.warning("Timeout error, will try after 2 second")
            await asyncio.sleep(2)
            try:
                await self.application.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=text,
                    disable_web_page_preview=True,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            except Exception as e:
                logging.warning(f'Failed to edit message: {str(e)}')
                raise e

        except Exception as e:
            logging.warning(f'Failed to edit message: {str(e)}')
            raise e

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
            logging.info(f"Edit message: {item['chat_id']} => {item['message_id']}")
            asyncio.create_task(self._edit_message(item['chat_id'], item['message_id'], item['text'], reply_markup))
            await asyncio.sleep(2)

    async def _leaderboard_check_pair(self):
        removed_pairs = get_removed_pairs()
        if len(removed_pairs)>0:
            for removed_pair_text in removed_pairs:
                await asyncio.sleep(0.5)
                await self.application.bot.send_message(chat_id=LEADERBOARD_ID, text=removed_pair_text, parse_mode='HTML')

    async def leaderboard(self):
        while True:
            await asyncio.sleep(100)
            asyncio.create_task(self._leaderboard())
            await asyncio.sleep(100)
            asyncio.create_task(self._leaderboard_check_pair())

    async def show_leaderboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        leaderboard_text = get_leaderboard()
        chat_id = update.effective_chat.id

        await context.bot.send_message(chat_id=chat_id, text=leaderboard_text, disable_web_page_preview=True, parse_mode='HTML')


    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        text = start_text()
        await context.bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML')
    
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
            logging.info("shill mode update")
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
    
    async def _shill(self, receive_text, chat_id, user_id, username):
        param = get_params(receive_text, "/shill")
        param = param.replace("@", "")
        response = await user_shillmaster(user_id, username, chat_id, param)
        is_rug = response['is_rug']
        if is_rug:
            user_warn = add_warn(username, user_id, chat_id)
            text = response['text'] + "\n\n@"+username+" warned: "+str(user_warn['count'])+" Project Rugged ❌"
            await self._send_message(chat_id, text)
            if user_warn['count'] > 1:
                text = response['text'] + "\n\n@"+username+" Banned: Posted "+str(user_warn['count'])+" Rugs ❌"
                await self._block_user(user_warn)

        payload_txt = response['text']
        is_new = response['is_new']
        if is_new:
            setting = Setting.find_one({"master": "master"})
            if setting != None:
                if username in setting['top_ten_users']:
                    await self._send_message(LEADERBOARD_ID, payload_txt)
        
        return await self._send_message(chat_id, payload_txt)

    async def _shill_off(self, param, update):
        pair = token_shillmaster(param)

        if pair == None:
            return await update.message.reply_text(f"Nobody shilled token: {param}", disable_web_page_preview=True)
        
        text = ""
        for user in pair['user_list']:
            text += f"@{user} shilled \n"
        
        text += f"\nMarketcap: ${format_number_string(pair['marketcap'])}"
        return await update.message.reply_text(text, disable_web_page_preview=True)

    async def shill(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        setting = Setting.find_one({"master": "master"})
        receive_text = update.message.text
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        username = update.effective_user.username
        if setting != None:
            if setting['shill_mode'] == False:
                param = get_params(receive_text, "/shill")
                param = param.replace("@", "")
                asyncio.get_event_loop().create_task(self._shill_off(param, update))
                return None

        asyncio.get_event_loop().create_task(self._shill(receive_text, chat_id, user_id, username))

        return None

    async def show_token_usage(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        setting = Setting.find_one({"master": "master"})
        receive_text = update.message.text
        if setting != None:
            if setting['shill_mode'] == False:
                param = get_params(receive_text, "/")
                param = param.replace("@", "")
                asyncio.get_event_loop().create_task(self._shill_off(param, update))
                return None

        return None

    async def _shillmaster(self, receive_text, chat_id):
        param = get_params(receive_text, "/shillmaster")
        param = param.replace("@", "")
        payload_txt = await get_user_shillmaster(param)
        has_warn = get_user_warn(param)
        if has_warn != None:
            payload_txt += "\n⚠️ Has 1 Warning ⚠️"
        
        return await self._send_message(chat_id, payload_txt, "", True)

    async def shillmaster(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        receive_text = update.message.text
        chat_id = update.effective_chat.id
        asyncio.get_event_loop().create_task(self._shillmaster(receive_text, chat_id))
        print("show shillmaster status")
        return None

    async def _remove_warning(self, receive_text, chat_id, user_id, context):
        param = get_params(receive_text, "/remove_warning")
        param = param.replace("@", "")
        member = await context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        if member['status'] == "creator":
            text = remove_warn(param)
            return await self._send_message(chat_id, text)
        else:
            text = "Only admin can remove user's warn"
            return await self._send_message(chat_id, text)

    async def remove_warning(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        receive_text = update.message.text
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        asyncio.get_event_loop().create_task(self._remove_warning(receive_text, chat_id, user_id, context))

        return None

    async def _unban(self, receive_text, chat_id, user_id, context):
        param = get_params(receive_text, "/unban")
        param = param.replace("@", "")
        member = await context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        if member['status'] == "creator":
            baned_user = get_baned_user(param)
            text = "@"+param+" is not banned"
            if baned_user != None:
                text = "@"+baned_user['username']+" is now unbanned ✅"
                self._unblock_user(baned_user, context)
            return await self._send_message(chat_id, text)
        else:
            text = "Only admin can unban user"
            return await self._send_message(chat_id, text)

    async def unban(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        receive_text = update.message.text
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        asyncio.get_event_loop().create_task(self._unban(receive_text, chat_id, user_id, context))
        
        return None
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data[NEXT] = False
        context.user_data['time'] = None
        context.user_data['hours'] = None
        context.user_data['text'] = None
        context.user_data['url'] = None
        context.user_data['username'] = None
        context.user_data['advertise_id'] = None
        context.user_data['invoice_id'] = None
        await update.message.reply_text("Bye! I hope we can talk again some day.")

        return END

    async def advertise(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        text = "If you want to advertise your project or services under the leaderboards, click the button below."
        keyboard = [
            [InlineKeyboardButton(text="Book an Ad", callback_data=str(SHOW_TIME))],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await self._send_message(chat_id, text, reply_markup, True)

        return SHOW_TIME

    async def show_time(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        available_time_list = check_available_time()
        keyboard = []
        query = update.callback_query
        if len(available_time_list)>0:
            if len(available_time_list)>12:
                start_index = 0
                end_index = 12
                last_button = [InlineKeyboardButton(text="NEXT", callback_data="SHOW_TIME_NEXT")]
                if context.user_data.get(NEXT):
                    start_index = 12
                    end_index = len(available_time_list)
                    last_button = [InlineKeyboardButton(text="BACK", callback_data="SHOW_TIME")]
                
                row = int((end_index-start_index+1)/2)
                total_array = []
                for item in range(start_index, row+start_index):
                    first_num = item
                    first_time = available_time_list[first_num]
                    first_button_text = convert_am_pm(first_time)
                    row_array = []
                    first_button = InlineKeyboardButton(text=first_button_text+" UTC", callback_data=first_time)
                    row_array.append(first_button)
                    second_num = first_num+row
                    if second_num < len(available_time_list):
                        second_time = available_time_list[second_num]
                        second_button_text = convert_am_pm(second_time)
                        second_button = InlineKeyboardButton(text=second_button_text+" UTC", callback_data=second_time)
                        row_array.append(second_button)
                    total_array.append(row_array)
                
                total_array.append(last_button)
                keyboard = total_array
            else:
                start_index = 0
                end_index = len(available_time_list)
                row = int((len(available_time_list)+1)/2)
                total_array = []
                for item in range(start_index, row+start_index):
                    first_num = item
                    first_time = available_time_list[first_num]
                    first_button_text = convert_am_pm(first_time)
                    row_array = []
                    first_button = InlineKeyboardButton(text=first_button_text+" UTC", callback_data=first_time)
                    row_array.append(first_button)
                    second_num = first_num+row
                    if second_num < len(available_time_list):
                        second_time = available_time_list[second_num]
                        second_button_text = convert_am_pm(second_time)
                        second_button = InlineKeyboardButton(text=second_button_text+" UTC", callback_data=second_time)
                        row_array.append(second_button)
                    total_array.append(row_array)
                
                keyboard = total_array
            cancel_button = [InlineKeyboardButton(text="CANCEL", callback_data="CANCEL_CONV")]
            keyboard.append(cancel_button)
            time_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text="When do you want the advertisement to begin being displayed?", reply_markup=time_markup)

            return SHOW_HOUR
        else:
            await query.edit_message_text(text="Sorry there are no available ads for today.")

            return END

    async def show_hour(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        command = query.data
        if "SHOW_TIME" in command:
            status = command.replace("SHOW_TIME", "")
            if status == "_NEXT":
                context.user_data[NEXT] = True
            else:
                context.user_data[NEXT] = False
            
            await self.show_time(update, context)
        elif "CANCEL_CONV" in command:
            await query.edit_message_text(text="Bye! I hope we can talk again some day.")

            return END
        else:
            context.user_data['time'] = command
            hours_array = check_available_hour(int(command))
            keyboard = []
            for hour in hours_array:
                budget_text = ""
                if hour == 2:
                    budget_text = "2 Hours - 0.075 ETH / 0.45 BNB"
                elif hour == 4:
                    budget_text = "4 Hours - 0.13 ETH / 0.78 BNB"
                elif hour == 8:
                    budget_text = "8 Hours - 0.2 ETH / 1.2 BNB"
                elif hour == 12:
                    budget_text = "12 Hours - 0.3 ETH / 1.8 BNB"
                elif hour == 24:
                    budget_text = "24 Hours - 0.5 ETH / 3 BNB"
                single_hour_array = [InlineKeyboardButton(text=budget_text, callback_data=hour)]
                keyboard.append(single_hour_array)

            hour_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text="Please choose", reply_markup=hour_markup)

            return COOSE_TOKEN

    async def choose_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        keyboard=[]
        await query.answer()
        hours = int(query.data)
        context.user_data['hours'] = hours
        if hours==2:
            keyboard = [
                [
                    InlineKeyboardButton(text="0.075 ETH", callback_data="0.075ETH"),
                    InlineKeyboardButton(text="0.45 BNB", callback_data="0.45BNB")
                ],
            ]
        elif hours==4:
            keyboard = [
                [
                    InlineKeyboardButton(text="0.13 ETH", callback_data="0.13ETH"),
                    InlineKeyboardButton(text="0.78 BNB", callback_data="0.78BNB")
                ],
            ]
        elif hours == 8:
            keyboard = [
                [
                    InlineKeyboardButton(text="0.2 ETH", callback_data="0.2ETH"),
                    InlineKeyboardButton(text="1.2 BNB", callback_data="1.2BNB")
                ],
            ]
        elif hours == 12:
            keyboard = [
                [
                    InlineKeyboardButton(text="0.3 ETH", callback_data="0.3ETH"),
                    InlineKeyboardButton(text="1.8 BNB", callback_data="1.8BNB")
                ],
            ]
        elif hours==24:
            keyboard = [
                [
                    InlineKeyboardButton(text="0.5 ETH", callback_data="0.5ETH"),
                    InlineKeyboardButton(text="3 BNB", callback_data="3BNB")
                ],
            ]
        cancel_button = [InlineKeyboardButton(text="CANCEL", callback_data="CANCEL_CONV")]
        keyboard.append(cancel_button)
        token_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text="Please choose", reply_markup=token_markup)

        return PAYMENT

    async def payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        param = query.data
        if "CANCEL_CONV" in param:
            await query.edit_message_text(text="Bye! I hope we can talk again some day.")

            return END
        else:
            symbol=""
            quantity=""
            if "ETH" in param:
                symbol = "ETH"
                quantity = param.replace("ETH", "")

            if "BNB" in param:
                symbol = "BNB"
                quantity = param.replace("BNB", "")
            
            username = update.effective_user.username
            context.user_data['username'] = username
            advertise = new_advertise(context.user_data)
            invoice = create_invoice(advertise, symbol, quantity)

            text = "✌ New Invoice ✌\n\nYour Invoice ID is:\n<code>"+str(invoice['hash'])+"</code>\n\n"
            text += "Please send "+str(invoice['quantity'])+" "+str(invoice['symbol'])+" to\n<code>"+str(invoice['address'])+"</code>\nwithin 30 minutes\n"
            text += "After completing the payment, kindly enter '/invoice' in the chat to secure your advertisement..\n"

            await query.edit_message_text(text=text, parse_mode='HTML')

            context.user_data[NEXT] = False
            context.user_data['time'] = None
            context.user_data['hours'] = None
            context.user_data['username'] = None

            return END

    async def invoice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        text = "Please Enter your invoice ID\n"
        await self._send_message(chat_id, text, "", True)

        return HASH_TYPING

    async def save_hash_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        hash = update.message.text
        username = update.effective_user.username
        invoice = get_invoice(hash, username)
        chat_id = update.effective_chat.id
        if invoice != None:
            context.user_data['invoice_id'] = invoice['_id']
            text = "Perfect. Now Please input your transaction ID"
            await context.bot.send_message(chat_id=chat_id, text=text)
            return TRAN_TYPING
        else:
            text = "Sorry, We can not find your Invoice."
            await context.bot.send_message(chat_id=chat_id, text=text)
            return END

    async def save_transaction_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        transaction = update.message.text
        context.user_data['transaction'] = transaction
        is_complete = complete_invoice(context.user_data)
        chat_id = update.effective_chat.id
        if is_complete:
            await context.bot.send_message(chat_id=chat_id, text="Payment Accepted\nProvide text for the button ad, up to a maximum of 30 characters.")

            return TEXT_TYPING
        else:
            await context.bot.send_message(chat_id=chat_id, text="Payment can not be Accepted\nPlease Make correct payment.")

            return END

    async def save_text_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['text'] = update.message.text
        chat_id = update.effective_chat.id
        await context.bot.send_message(chat_id=chat_id, text="Provide ad URL: Share the link to be accessed when the advertisement is clicked. This can be Telegram group or the Project's website.")

        return URL_TYPING

    async def save_url_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['url'] = update.message.text
        chat_id = update.effective_chat.id
        advertise = edit_advertise(context.user_data)
        start_date = advertise['start'].strftime('%d/%m/%Y')
        start_time_str = advertise['start'].strftime('%H')
        start_time = convert_am_pm(start_time_str)
        await context.bot.send_message(chat_id=chat_id, text="Ad purchase confirmation✅\nThank you for purchasing an advertisement. Your ad will go live at: "+start_date+" "+start_time)
        context.user_data['text'] = None
        context.user_data['url'] = None
        context.user_data['transaction'] = None
        context.user_data['invoice_id'] = None
        return END

    def run(self):
        self.application.add_handler(CommandHandler(["start", "help"], self.start))
        self.application.add_handler(CommandHandler("leaderboard", self.show_leaderboard))
        self.application.add_handler(MessageHandler(filters.Regex("/shillmode@(s)?"), self.shillmode))
        self.application.add_handler(MessageHandler(filters.Regex("/banmode@(s)?"), self.banmode))
        self.application.add_handler(MessageHandler(filters.Regex("/shill0x(s)?"), self.shill))
        self.application.add_handler(MessageHandler(filters.Regex("/shill 0x(s)?"), self.shill))
        self.application.add_handler(MessageHandler(filters.Regex("/shillmaster@(s)?"), self.shillmaster))
        self.application.add_handler(MessageHandler(filters.Regex("/shillmaster @(s)?"), self.shillmaster))
        self.application.add_handler(MessageHandler(filters.Regex("/remove_warning@(s)?"), self.remove_warning))
        self.application.add_handler(MessageHandler(filters.Regex("/remove_warning @(s)?"), self.remove_warning))
        self.application.add_handler(MessageHandler(filters.Regex("0x(s)?"), self.show_token_usage))
        self.application.add_handler(MessageHandler(filters.Regex("/unban@(s)?"), self.unban))
        self.application.add_handler(MessageHandler(filters.Regex("/unban @(s)?"), self.unban))
        self.application.add_handler(ConversationHandler(
            entry_points=[CommandHandler("advertise", self.advertise)],
            states={
                SHOW_TIME: [CallbackQueryHandler(self.show_time)],
                SHOW_HOUR: [CallbackQueryHandler(self.show_hour)],
                COOSE_TOKEN: [CallbackQueryHandler(self.choose_token)],
                PAYMENT: [CallbackQueryHandler(self.payment)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        ))
        self.application.add_handler(ConversationHandler(
            entry_points=[CommandHandler("invoice", self.invoice)],
            states={
                HASH_TYPING: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.save_hash_input)],
                TRAN_TYPING: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.save_transaction_input)],
                TEXT_TYPING: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.save_text_input)],
                URL_TYPING: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.save_url_input)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        ))
        self.application.run_polling()