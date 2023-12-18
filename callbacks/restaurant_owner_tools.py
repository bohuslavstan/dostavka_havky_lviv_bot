from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, ConversationHandler

from callbacks import conversation_states
from callbacks.special_actions import RESTAURANT_OWNER_BUTTONS
from models.base import Restaurant, MenuCategory, MenuItem

CATEGORY_MENU_BUTTONS = [{"text": "Добавити категорію", "callback_data": "add_menu_category"},
                         {"text": "Редагувати категорію", "callback_date": "edit_menu_category"},
                         {"text": "Назад", "callback_date": "special_actions"}]


async def register_restaurant(update: Update, context: CallbackContext):
    await context.bot.edit_message_text(chat_id=update.effective_user.id,
                                        message_id=context.chat_data["last_message"],
                                        text="Введіть назву вашого закладу:")
    return conversation_states.ENTER_RESTAURANT_NAME


async def added_name(update: Update, context: CallbackContext):
    context.chat_data["restaurant_name"] = update.message.text
    await context.bot.send_message(chat_id=update.effective_user.id,
                                   text=f"Назва закладу: {update.message.text}\n"
                                        f"Добавте опис вашого закладу:")
    return conversation_states.ENTER_RESTAURANT_DESCRIPTION


async def added_description(update: Update, context: CallbackContext):
    restaurant = Restaurant.create(name=context.chat_data["restaurant_name"],
                                   description=update.message.text,
                                   owner_id=update.effective_user.id)
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(**x)] for x in RESTAURANT_OWNER_BUTTONS])
    message = await context.bot.send_message(chat_id=update.effective_user.id,
                                       text=f"Ваш заклад зареєстрований успішно!\n{str(restaurant)}",
                                       reply_markup=reply_markup)
    context.chat_data["last_message"] = message.message_id
    context.chat_data.pop("restaurant_name")
    return ConversationHandler.END


async def category_manager(update: Update, context: CallbackContext):
    buttons = [{"text": "Добавити категорію", "callback_data": "add_menu_category"}]
    if Restaurant.find(owner_id=update.effective_user.id).list_categories():
        buttons.append({"text": "Редагувати категорію", "callback_date": "edit_menu_category"})
    buttons.append({"text": "Назад", "callback_date": "special_actions"})
    text = "Менеджер категорій: тут ви можете добавити нову категорію у ваше меню, або ж редагувати вже існуючу"
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(**x)] for x in buttons])
    await context.bot.edit_message_text(chat_id=update.effective_user.id,
                                        message_id=context.chat_data["last_message"],
                                        text=text)
    await context.bot.edit_message_reply_markup(chat_id=update.effective_user.id,
                                                message_id=context.chat_data["last_message"],
                                                reply_markup=reply_markup)


def add_category(update: Update, context: CallbackContext):
    text = "Введіть назву категорії:"
    context.bot.edit_message_text(chat_id=update.effective_user.id,
                                  message_id=context.chat_data["last_message"],
                                  text=text)
    return conversation_states.ENTER_CATEGORY_NAME


def category_added(update: Update, context: CallbackContext):
    Restaurant.find(owner_id=update.effective_user.id).create_category(update.message.text)
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(**x)] for x in CATEGORY_MENU_BUTTONS])
    message = await context.bot.send_message(chat_id=update.effective_user.id,
                                             text=f"Категорію '{update.message.text}' успішно додано!",
                                             reply_markup=reply_markup)
    context.chat_data["last_message"] = message.message_id
    return ConversationHandler.END


async def edit_categories(update: Update, context: CallbackContext):
    categories = Restaurant.find(owner_id=update.effective_user.id).list_categories()
    context.chat_data["menu_categories"] = {}
    for category in categories:
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(text="Змінити назву",
                                                                   callback_data=f"menu_category_change_{category.id}"),
                                              InlineKeyboardButton(text="Видалити",
                                                                   callback_data=f"menu_category_delete_{category.id}")]])

        message = await context.bot.send_message(chat_id=update.effective_user.id,
                                           text=str(category),
                                           reply_markup=reply_markup)
        context.chat_data["menu_categories"][category.id] = {"message_id": message.message_id,
                                                             "category_name": str(category)}


async def change_category_name(update: Update, context: CallbackContext):
    category_to_change = update.callback_query.data.replace("menu_category_change_", "")
    context.chat_data["category_to_change"] = category_to_change
    for category in context.chat_data["menu_categories"]:
        if category == category_to_change:
            text = f"{context.chat_data['menu_categories']['category']['category_name']}\n" \
                   f"Введіть нову назву для цієї категорії:"
            await context.bot.edit_message_text(chat_id=update.effective_user.id,
                                                message_id=context.chat_data["menu_categories"]["category"]["message_id"],
                                                text=text)
        else:
            await context.bot.delete_message(chat_id=update.effective_user.id,
                                             message_id=context.chat_data["menu_categories"]["category"]["message_id"])
    context.chat_data.pop("menu_categories")
    return conversation_states.CHANGE_CATEGORY_NAME


async def changed_category_name(update: Update, context: CallbackContext):
    MenuCategory.get(category_id=context.chat_data["category_to_change"]).change_name(name=update.message.text)
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(**x)] for x in CATEGORY_MENU_BUTTONS])
    message = await context.bot.send_message(chat_id=update.effective_user.id,
                                             text=f"Категорію '{update.message.text}' успішно перейменовано!",
                                             reply_markup=reply_markup)
    context.chat_data["last_message"] = message.message_id
    return ConversationHandler.END


async def delete_category_confirmation(update: Update, context: CallbackContext):
    pass


async def delete_category(update: Update, context: CallbackContext):
    pass


async def choose_menu_category(update: Update, context: CallbackContext):
    buttons = ((str(category), category.id) for category in Restaurant.find(owner_id=update.effective_user.id).list_categories())
    text = "Виберіть категорію, до якої належить(належатиме) страва:"
    buttons = [[InlineKeyboardButton(text=x, callback_data=f"menu_item_category_{y}")] for x, y in buttons]
    buttons.append([InlineKeyboardButton(text="Назад", callback_data="special_actions")])
    await context.bot.edit_message_text(chat_id=update.effective_user.id,
                                        message_id=context.chat_data["last_message"],
                                        text=text)
    await context.bot.edit_message_reply_markup(chat_id=update.effective_user.id,
                                                message_id=context.chat_data["last_message"],
                                                reply_markup=InlineKeyboardMarkup(buttons))


async def choose_menu_add_or_delete(update: Update, context: CallbackContext):
    category_id = int(update.callback_query.data.replace("menu_item_category_", ""))
    text = f"{str(MenuCategory.get(category_id))}\nВиберіть, добавити чи редагувати страву?"
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(text="Добавити",
                                                               callback_data=f"add_menu_item_{category_id}"),
                                          InlineKeyboardButton(text="Редагувати",
                                                               callback_data=f"edit_menu_item_{category_id}"),
                                          InlineKeyboardButton(text="Назад",
                                                               callback_data=f"menu_items_manager")
                                          ]])
    await context.bot.edit_message_text(chat_id=update.effective_user.id,
                                        message_id=context.chat_data["last_message"],
                                        text=text)
    await context.bot.edit_message_reply_markup(chat_id=update.effective_user.id,
                                                message_id=context.chat_data["last_message"],
                                                reply_markup=reply_markup)


async def add_menu_item_start(update: Update, context: CallbackContext):
    context.chat_data["menu_item"]["category_id"] = update.callback_query.data.replace("add_menu_item_", "")
    await context.bot.edit_message_text(chat_id=update.effective_user.id,
                                        message_id=context.chat_data['last_message'],
                                        text="Введіть назву страви:")
    return conversation_states.ADD_MENU_ITEM_NAME


async def add_menu_item_add_description(update: Update, context: CallbackContext):
    context.chat_data["menu_item"]["name"] = update.message.text
    await context.bot.send_message(chat_id=update.effective_user.id,
                                   text="Чудово. Тепер введіть опис страви (складники, алергени і т.д.) "
                                        "одним повідомленням.")
    return conversation_states.ADD_MENU_ITEM_DESCRIPTION


async def add_menu_item_add_price(update: Update, context: CallbackContext):
    context.chat_data["menu_item"]["description"] = update.message.text
    await context.bot.send_message(chat_id=update.effective_user.id,
                                   text="Чудово. Тепер введіть ціну страви. "
                                        "Використовуйте для десяткового дробу крапку, а не кому.")
    return conversation_states.ADD_MENU_ITEM_PRICE


async def add_menu_item_finish(update: Update, context: CallbackContext):
    item = MenuItem.create(name=context.chat_data["menu_item"]["name"],
                           category_id=context.chat_data["menu_item"]["category_id"],
                           description=context.chat_data["menu_item"]["description"],
                           price=float(update.message.text))
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(text="Назад",
                                                               callback_data=f"menu_item_category_{context.chat_data['menu_item']['category_id']}")]])
    message = await context.bot.send_message(chat_id=update.effective_user.id,
                                             text=f"Страву додано!\n{str(item)}",
                                             reply_markup=reply_markup)
    context.chat_data['last_message'] = message.message_id
    context.chat_data.pop("menu_item")


async def edit_menu_item_choose(update: Update, context: CallbackContext):
    category_id = update.callback_query.data.replace("edit_menu_item_", "")
    menu_item_list = MenuCategory.list_items(category_id=category_id)
    for item in menu_item_list:
        pass
