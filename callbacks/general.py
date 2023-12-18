from typing import List

from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, \
    ReplyKeyboardRemove
from telegram.ext import CallbackContext

from callbacks import conversation_states
from models.base import User, DeliveryGuyStatus


def menu_builder(buttons: List[KeyboardButton] | List[InlineKeyboardButton],
                 n_cols: int = 1,
                 header: KeyboardButton | List[KeyboardButton] | InlineKeyboardButton | List[InlineKeyboardButton]= None,
                 footer: KeyboardButton | List[KeyboardButton] | InlineKeyboardButton | List[InlineKeyboardButton] = None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header:
        menu.insert(0, header if isinstance(header, list) else [header])
    if footer:
        menu.append(footer if isinstance(footer, list) else [footer])
    return menu


def get_start_menu():
    menu = InlineKeyboardMarkup([[InlineKeyboardButton(**x)] for x in (
        {"text": "Зробити замовлення", "callback_data": "make_order"},
        {"text": "Менеджер локацій", "callback_data": "location_manager"},
        {"text": "Повідомити про проблему", "callback_data": "report_issue"},
        {"text": "Особливі дії", "callback_data": "special_actions"})])
    return menu


async def start_menu(update: Update, context: CallbackContext):
    last_message = await context.bot.send_message(chat_id=update.effective_user.id,
                                                  text="Давай розпочнемо працювати!\n"
                                                       "Якщо ти ще не добавив свій розташування свого дому, можеш зробити це в \"Менеджер локацій\"\n"
                                                       "Якщо ж все готово, і ти зголоднів, то нумо відкривай список ресторанів!\n"
                                                       "А якщо ж у тебе є якісь зауваження, повідом їх за допомогою третьої кнопки.",
                                                  reply_markup=get_start_menu())
    context.chat_data['last_message'] = last_message.message_id


async def start_bot(update: Update, context: CallbackContext):
    if not User.get(update.effective_user.id):
        reply_markup = ReplyKeyboardMarkup([[KeyboardButton(text="Зареєструватися", request_contact=True)]])
        await context.bot.send_message(chat_id=update.effective_user.id,
                                       text="Вітаю! Дякую, що доєдналися до нашого сервісу \"Хавка на хатку!\""
                                            "Для початку, поділіться вашим контактом для реєстрації у застосунку:",
                                       reply_markup=reply_markup)
    else:
        return await start_menu(update, context)


async def registration(update: Update, context: CallbackContext):
    data = {"telegram_id": update.effective_user.id,
            "full_name": f"{update.message.contact.first_name if update.message.contact.first_name else ''} "
                         f"{update.message.contact.last_name if update.message.contact.last_name else ''}",
            "username": update.effective_user.username,
            "phone_number": update.message.contact.phone_number}
    User.register(**data)
    await update.message.reply_text(text="Реєстрація пройшла успішно!", reply_markup=ReplyKeyboardRemove())
    return await start_menu(update, context)


async def back(update: Update, context: CallbackContext):
    await context.bot.edit_message_text(chat_id=update.effective_user.id,
                                        message_id=context.chat_data["last_message"],
                                        text="Давай розпочнемо працювати!\n"
                                              "Якщо ти ще не добавив свій розташування свого дому, можеш зробити це в \"Менеджер локацій\"\n"
                                              "Якщо ж все готово, і ти зголоднів, то нумо відкривай список ресторанів!\n"
                                              "А якщо ж у тебе є якісь зауваження, повідом їх за допомогою третьої кнопки.",)
    await context.bot.edit_message_reply_markup(chat_id=update.effective_user.id,
                                                message_id=context.chat_data["last_message"],
                                                reply_markup=get_start_menu())
