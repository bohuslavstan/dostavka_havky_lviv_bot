from sqlalchemy import Update
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from models.base import PromotionApplication, User


async def check_applications(update: Update, context: CallbackContext):
    applications = PromotionApplication.all_open(update.callback_query.data.replace("check_applications_", ""))
    await context.bot.delete_message(chat_id=update.effective_user.id,
                                     message_id=context.chat_data["last_message"])
    context.chat_data["application"] = {}
    for application in applications:
        text = str(application)
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(text="Прийняти",
                                                                   callback_data=f"accept_promotion_{application.user_id}"),
                                              InlineKeyboardButton(text="Відхилити",
                                                                   callback_data=f"reject_promotion_{application.user_id}")]])
        message = await context.bot.send_message(chat_id=update.effective_user.id,
                                                 text=text,
                                                 reply_markup=reply_markup)
        context.chat_data["application"][application.user_id] = message.message_id


async def remove_promotions(update: Update, context: CallbackContext):
    promotions = User.find(update.callback_query.data.replace("remove_promotions_", ""))
    context.chat_data["promotion"] = {}
    for promotion in promotions:
        text = str(promotion)
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(text="Видалити",
                                                                   callback_data=f"downgrade_{promotion.telegram_id}")]])
        message = await context.bot.send_message(chat_id=update.effective_user.id,
                                                 text=text,
                                                 reply_markup=reply_markup)
        context.chat_data["promotion"][promotion.telegram_id] = message.message_id


async def confirm_remove_promotion(update: Update, context: CallbackContext):
    promotion = User.get(int(update.callback_query.data.replace("downgrade_", "")))
    for user_id in context.chat_data["promotion"]:
        if int(user_id) == promotion.telegram_id:
            text = f"Ви впевнені?\n{str(promotion)}"
            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(text="Підтвердити видалення",
                                                                       callback_data=f"confirm_downgrade_{promotion.telegram_id}"),
                                                  InlineKeyboardButton(text="Відмінити",
                                                                       callback_data=f"to_start_menu")
                                                  ]])
            await context.bot.edit_message_text(chat_id=update.effective_user.id,
                                                message_id=context.chat_data["promotion"][user_id],
                                                text=text)
            await context.bot.edit_message_reply_markup(chat_id=update.effective_user.id,
                                                        message_id=context.chat_data["promotion"][user_id],
                                                        reply_markup=reply_markup)
            context.chat_data["last_message"] = context.chat_data["promotion"][user_id]
        else:
            await context.bot.delete_message(chat_id=update.effective_user.id,
                                             message_id=context.chat_data["promotion"][user_id])
    context.chat_data.pop("promotion")


async def remove_promotion_final(update: Update, context: CallbackContext):
    user_id = int(update.callback_query.data.replace("confirm_downgrade_", ""))
    User.get(user_id).promote("client")
    text = "Успішно!"
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(text="Назад",
                                                               callback_data=f"to_start_menu")
                                          ]])
    await context.bot.edit_message_text(chat_id=update.effective_user.id,
                                        message_id=context.chat_data["last_message"],
                                        text=text)
    await context.bot.edit_message_reply_markup(chat_id=update.effective_user.id,
                                                message_id=context.chat_data["last_message"],
                                                reply_markup=reply_markup)
    await context.bot.send_message(chat_id=user_id,
                                   text="Вас підвищили до клієнта!")


async def accept_application(update: Update, context: CallbackContext):
    user_id = int(update.callback_query.data.replace("accept_promotion_", ""))
    role_to_promote = PromotionApplication.promote(user_id)
    user = User.get(user_id)
    text = f"Ви успішно підтвердили заявку!\n{str(user)}"
    await context.bot.edit_message_text(chat_id=update.effective_user.id,
                                        message_id=context.chat_data["application"][user_id],
                                        text=text)
    text_to_client = f"Вас підвищили до {'кур`єра' if role_to_promote == 'delivery_guy' else 'менеджера ресторану'}!"
    await context.bot.send_message(chat_id=user_id,
                                   text=text_to_client)


async def cancel_application(update: Update, context: CallbackContext):
    user_id = int(update.callback_query.data.replace("reject_promotion_", ""))
    PromotionApplication.close(user_id)
    user = User.get(user_id)
    text = f"Ви відмінили заявку.\n{str(user)}"
    await context.bot.edit_message_text(chat_id=update.effective_user.id,
                                        message_id=context.chat_data["application"][user_id],
                                        text=text)
    text_to_client = f"Ваша заявку була відхилена."
    await context.bot.send_message(chat_id=user_id,
                                   text=text_to_client)
