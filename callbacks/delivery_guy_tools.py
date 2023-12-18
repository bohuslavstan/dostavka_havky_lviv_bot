from sqlalchemy import Update
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext

from models.base import DeliveryGuyStatus


async def activate_delivery_status(update: Update, context: CallbackContext):
    DeliveryGuyStatus.check_in(delivery_guy_id=update.effective_user.id, status=True)
    text = "Готово! Ви розпочали роботу.\nМеню кур'єра.\nЗараз ви працюєте. Коли появиться нове замовлення, ви отримаєте сповіщення."
    buttons = ({"text": "Закінчити роботу", "callback_data": "end_delivery_job"},
               {"text": "Назад", "callback_data": "to_start_menu"})
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(**x)] for x in buttons])
    await context.bot.edit_message_text(chat_id=update.effective_user.id,
                                        message_id=context.chat_data['last_message'],
                                        text=text)
    await context.bot.edit_message_reply_markup(chat_id=update.effective_user.id,
                                                message_id=context.chat_data['last_message'],
                                                reply_markup=reply_markup)


async def deactivate_delivery_status(update: Update, context: CallbackContext):
    timediff = DeliveryGuyStatus.check_in(delivery_guy_id=update.effective_user.id, status=False)
    text = f"Ти пропрацював {str(timediff).split('.')[0]}. До насупних зустрічей!\nМеню кур'єра.\nЗараз ви не працюєте. Щоб розпочати роботу, натисніть клавішу знизу."
    buttons = ({"text": "Розпочати роботу", "callback_data": "start_delivery_job"},
               {"text": "Назад", "callback_data": "to_start_menu"})
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(**x)] for x in buttons])
    await context.bot.edit_message_text(chat_id=update.effective_user.id,
                                        message_id=context.chat_data['last_message'],
                                        text=text)
    await context.bot.edit_message_reply_markup(chat_id=update.effective_user.id,
                                                message_id=context.chat_data['last_message'],
                                                reply_markup=reply_markup)
