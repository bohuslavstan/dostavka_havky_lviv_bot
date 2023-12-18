from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext

from models.base import User, DeliveryGuyStatus, PromotionApplication


RESTAURANT_OWNER_BUTTONS = ({"text": "Добавити рестораторів", "callback_data": "check_applications_restaurant_owner"},
                            {"text": "Видалити рестораторів", "callback_data": "remove_promotions_restaurant_owner"},
                            {"text": "Добавити кур'єрів", "callback_data": "check_applications_delivery_guy"},
                            {"text": "Видалити кур'єрів", "callback_data": "remove_promotions_delivery_quy"},
                            {"text": "Відкрити повідомлення про проблеми", "callback_data": "reported_issues"},
                            {"text": "Назад", "callback_data": "to_start_menu"})


async def special_actions_menu(update: Update, context: CallbackContext):
    user = User.get(update.effective_user.id)
    text = ""
    buttons = ()
    match user.role:
        case "client":
            if not PromotionApplication.find(user_id=update.effective_user.id):
                text = "Тут ви можете подати заявку на роботу або ж зареєструвати свій заклад.\n" \
                       "Якщо ви залишете свою заявку, наш менеджер зв'яжеться з вами незабаром."
                buttons = ({"text": "Подати заявку на роботу", "callback_data": "apply_for_delivery_guy"},
                           {"text": "Зареєструвати заклад", "callback_data": "apply_for_restaurant_owner"},
                           {"text": "Назад", "callback_data": "to_start_menu"})
            else:
                text = "Зачекайте, будь ласка, ваша заявка опрацьовується."
                buttons = [{"text": "Назад", "callback_data": "to_start_menu"}]
        case "delivery_guy":
            if DeliveryGuyStatus.last_status(update.effective_user.id).active:
                text = "Меню кур'єра.\nЗараз ви працюєте. Коли появиться нове замовлення, ви отримаєте сповіщення."
                buttons = ({"text": "Закінчити роботу", "callback_data": "end_delivery_job"},
                           {"text": "Назад", "callback_data": "to_start_menu"})
            else:
                text = "Меню кур'єра.\nЗараз ви не працюєте. Щоб розпочати роботу, натисніть клавішу знизу."
                buttons = ({"text": "Розпочати роботу", "callback_data": "start_delivery_job"},
                           {"text": "Назад", "callback_data": "to_start_menu"})
        case "restaurant_owner":
            restaurant = user.get_restaurant()
            if restaurant:
                text = f"Меню ресторатора.\nВаш ресторан: {restaurant.name}.\nТут можна працювати зі всім," \
                       f" що пов'язано з вашим закладом"
                buttons = ({"text": "Менеджер категорій", "callback_data": "category_manager"},
                           {"text": "Менеджер тегів закладу", "callback_data": "restaurant_tags_manager"},
                           {"text": "Менеджер ресторанів закладу", "callback_data": "restaurant_locations_manager"},
                           {"text": "Менеджер меню закладу", "callback_data": "menu_items_manager"},
                           {"text": "Видалити заклад", "callback_data": "delete_restaurant"},
                           {"text": "Назад", "callback_data": "to_start_menu"})
            else:
                text = "Меню ресторатора.\n" \
                       "Ви можете зареєструвати свій заклад для того, щоби доєднатися до нашої системи"
                buttons = ({"text": "Зареєструвати ресторан", "callback_data": "create_restaurant"},
                           {"text": "Назад", "callback_data": "to_start_menu"})
        case "admin":
            text = "Меню адміністратора."
            buttons = RESTAURANT_OWNER_BUTTONS

    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(**x)] for x in buttons])
    await context.bot.edit_message_text(chat_id=update.effective_user.id,
                                        message_id=context.chat_data['last_message'],
                                        text=text)
    await context.bot.edit_message_reply_markup(chat_id=update.effective_user.id,
                                                message_id=context.chat_data['last_message'],
                                                reply_markup=reply_markup)


async def apply_for_promotion(update: Update, context: CallbackContext):
    role_to_promote = update.callback_query.data.replace("apply_for_", "")
    PromotionApplication.create(user_id=update.effective_user.id, role_to_promote=role_to_promote)
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(text="Назад", callback_data="to_start_menu")]])
    await context.bot.edit_message_text(chat_id=update.effective_user.id,
                                        message_id=context.chat_data['last_message'],
                                        text="Заявку подано! Лишилося зачекати, щоб її оглянув адміністратор.\n"
                                             "Адміністратор зв'яжеться з вами незабаром.")
    await context.bot.edit_message_reply_markup(chat_id=update.effective_user.id,
                                                message_id=context.chat_data['last_message'],
                                                reply_markup=reply_markup)
    admins = User.find("admin")
    text_to_admin = f"{'Нова заявка на посаду кур`єра' if role_to_promote=='delivery_guy' else 'Заявка на новий заклад'}" \
                    f". Перевірте її в панелі Адміністратора (Особливі дії)"
    if admins:
        for admin in admins:
            await context.bot.send_message(chat_id=admin.telegram_id,
                                           text=text_to_admin)
