from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, ConversationHandler

from callbacks import conversation_states
from callbacks.special_actions import RESTAURANT_OWNER_BUTTONS, FREE_RESTAURANT_OWNER_BUTTONS
from models.base import Restaurant, MenuCategory, MenuItem

CATEGORY_MENU_BUTTONS = [{"text": "Добавити категорію", "callback_data": "add_menu_category"},
                         {"text": "Редагувати категорію", "callback_data": "edit_menu_category"},
                         {"text": "Назад", "callback_data": "special_actions"}]


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
        buttons.append({"text": "Редагувати категорію", "callback_data": "edit_menu_category"})
    buttons.append({"text": "Назад", "callback_data": "special_actions"})
    text = "Менеджер категорій: тут ви можете добавити нову категорію у ваше меню, або ж редагувати вже існуючу"
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(**x)] for x in buttons])
    await context.bot.edit_message_text(chat_id=update.effective_user.id,
                                        message_id=context.chat_data["last_message"],
                                        text=text)
    await context.bot.edit_message_reply_markup(chat_id=update.effective_user.id,
                                                message_id=context.chat_data["last_message"],
                                                reply_markup=reply_markup)


async def add_category(update: Update, context: CallbackContext):
    text = "Введіть назву категорії:"
    await context.bot.edit_message_text(chat_id=update.effective_user.id,
                                        message_id=context.chat_data["last_message"],
                                        text=text)
    return conversation_states.ENTER_CATEGORY_NAME


async def category_added(update: Update, context: CallbackContext):
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
    category_to_change = int(update.callback_query.data.replace("menu_category_change_", ""))
    context.chat_data["category_to_change"] = category_to_change
    for category in context.chat_data["menu_categories"]:
        if category == category_to_change:
            text = f"{context.chat_data['menu_categories'][category]['category_name']}\n" \
                   f"Введіть нову назву для цієї категорії:"
            await context.bot.edit_message_text(chat_id=update.effective_user.id,
                                                message_id=context.chat_data["menu_categories"][category]["message_id"],
                                                text=text)
        else:
            await context.bot.delete_message(chat_id=update.effective_user.id,
                                             message_id=context.chat_data["menu_categories"][category]["message_id"])
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
    category_to_delete = int(update.callback_query.data.replace("menu_category_delete_", ""))
    for category in context.chat_data["menu_categories"]:
        if category == category_to_delete:
            text = f"{context.chat_data['menu_categories'][category]['category_name']}\n" \
                   f"Ви впевнені, що хочете видалити цю категорію?" \
                   f" Разом з нею будуть видалені усі страви цієї категорії."
            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(text="Видалити",
                                                                       callback_data=f"confirm_category_delete_{category_to_delete}")],
                                                 [InlineKeyboardButton(text="Відмінити",
                                                                       callback_data="edit_menu_category")]])
            await context.bot.edit_message_text(chat_id=update.effective_user.id,
                                                message_id=context.chat_data["menu_categories"][category]["message_id"],
                                                text=text)
            await context.bot.edit_message_reply_markup(chat_id=update.effective_user.id,
                                                        message_id=context.chat_data["menu_categories"][category]["message_id"],
                                                        reply_markup=reply_markup)
        else:
            await context.bot.delete_message(chat_id=update.effective_user.id,
                                             message_id=context.chat_data["menu_categories"][category]["message_id"])


async def delete_category(update: Update, context: CallbackContext):
    category_to_delete = int(update.callback_query.data.replace("confirm_category_delete_", ""))
    MenuCategory.get(category_id=category_to_delete).delete()
    text = "Категорію видалено!"
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(**x)] for x in CATEGORY_MENU_BUTTONS])
    await context.bot.edit_message_text(chat_id=update.effective_user.id,
                                        message_id=context.chat_data["menu_categories"][category_to_delete]["message_id"],
                                        text=text)
    await context.bot.edit_message_reply_markup(chat_id=update.effective_user.id,
                                                message_id=context.chat_data["menu_categories"][category_to_delete]["message_id"],
                                                reply_markup=reply_markup)
    context.chat_data.pop("menu_categories")


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
    buttons = [{"text": "Добавити", "callback_data": f"add_menu_item_{category_id}"},
               {"text": "Назад", "callback_data": f"menu_items_manager"}]
    if MenuCategory.list_items(category_id=category_id):
        buttons.insert(1, {"text": "Редагувати", "callback_data": f"1_edit_menu_item_{category_id}"})

    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(**x) for x in buttons]])
    await context.bot.edit_message_text(chat_id=update.effective_user.id,
                                        message_id=context.chat_data["last_message"],
                                        text=text)
    await context.bot.edit_message_reply_markup(chat_id=update.effective_user.id,
                                                message_id=context.chat_data["last_message"],
                                                reply_markup=reply_markup)


async def add_menu_item_start(update: Update, context: CallbackContext):
    context.chat_data["menu_item"] = {"category_id": update.callback_query.data.replace("add_menu_item_", "")}
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
    return ConversationHandler.END


async def edit_menu_item_choose(update: Update, context: CallbackContext):
    category_id = update.callback_query.data.replace("1_edit_menu_item_", "")
    context.chat_data["menu_search_category_id"] = category_id
    menu_item_list = MenuCategory.list_items(category_id=category_id)
    context.chat_data["menu_item_list"] = {}
    for item in menu_item_list:
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(text="Редагувати",
                                                                   callback_data=f"2_edit_menu_item_details_{item.id}"),
                                              InlineKeyboardButton(text="Видалити",
                                                                   callback_data=f"delete_menu_item_{item.id}")]])
        message = await context.bot.send_message(chat_id=update.effective_user.id,
                                                 text=str(item),
                                                 reply_markup=reply_markup)
        context.chat_data["menu_item_list"][item.id] = message.message_id


async def delete_menu_item_confirmation(update: Update, context: CallbackContext):
    category_id = context.chat_data["menu_search_category_id"]
    menu_item_id = int(update.callback_query.data.replace("delete_menu_item_", ""))
    text = update.callback_query.message.text
    for item_id in context.chat_data["menu_item_list"]:
        if item_id == menu_item_id:
            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(text="Видалити",
                                                                       callback_data=f"confirm_item_delete_{item_id}")],
                                                 [InlineKeyboardButton(text="Відмінити",
                                                                       callback_data=f"1_edit_menu_item_{category_id}")]])
            await context.bot.edit_message_text(chat_id=update.effective_user.id,
                                                message_id=context.chat_data["menu_item_list"][item_id],
                                                text=f"Ви впевнені, що хочете видалити цю страву?\n{text}")
            await context.bot.edit_message_reply_markup(chat_id=update.effective_user.id,
                                                        message_id=context.chat_data["menu_item_list"][item_id],
                                                        reply_markup=reply_markup)
        else:
            await context.bot.delete_message(chat_id=update.effective_user.id,
                                             message_id=context.chat_data["menu_item_list"][item_id])


async def delete_menu_item(update: Update, context: CallbackContext):
    menu_item_id = int(update.callback_query.data.replace("confirm_item_delete_", ""))
    MenuItem.delete(menu_item_id=menu_item_id)
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(**x)] for x in RESTAURANT_OWNER_BUTTONS])
    await context.bot.edit_message_text(chat_id=update.effective_user.id,
                                        message_id=context.chat_data["menu_item_list"][menu_item_id],
                                        text="Страва видалена")
    await context.bot.edit_message_reply_markup(chat_id=update.effective_user.id,
                                                message_id=context.chat_data["menu_item_list"][menu_item_id],
                                                reply_markup=reply_markup)
    context.chat_data["last_message"] = context.chat_data["menu_item_list"][menu_item_id]
    context.chat_data.pop("menu_item_list")


async def menu_item_edit_choose(update: Update, context: CallbackContext):
    menu_item_id = int(update.callback_query.data.replace("2_edit_menu_item_details_", ""))
    for item_id in context.chat_data["menu_item_list"]:
        if item_id == menu_item_id:
            text = f"Що ви хочете змінити?\n{update.callback_query.message.text}"
            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(text="Назву",
                                                                       callback_data=f"3_edit_menu_item_name_{menu_item_id}"),
                                                  InlineKeyboardButton(text="Опис",
                                                                       callback_data=f"3_edit_menu_item_description_{menu_item_id}"),
                                                  InlineKeyboardButton(text="Ціну",
                                                                       callback_data=f"3_edit_menu_item_price_{menu_item_id}")]])
            await context.bot.edit_message_text(chat_id=update.effective_user.id,
                                                message_id=context.chat_data["menu_item_list"][item_id],
                                                text=text)
            await context.bot.edit_message_reply_markup(chat_id=update.effective_user.id,
                                                        message_id=context.chat_data["menu_item_list"][item_id],
                                                        reply_markup=reply_markup)
        else:
            await context.bot.delete_message(chat_id=update.effective_user.id,
                                             message_id=context.chat_data["menu_item_list"][item_id])
    context.chat_data.pop("menu_item_list")


async def menu_item_edit(update: Update, context: CallbackContext):
    context.chat_data["change_menu_item"] = {}
    (context.chat_data["change_menu_item"]["change_type"],
     context.chat_data["change_menu_item"]["id"]) = update.callback_query.data.replace("3_edit_menu_item_", "")\
        .split("_")
    match context.chat_data["change_menu_item"]["change_type"]:
        case "name":
            text = "Введіть нову назву страви:"
        case "description":
            text = "Введіть новий опис страви:"
        case _:
            text = "Введіть нову ціну страви:"
    await context.bot.edit_message_text(chat_id=update.effective_user.id,
                                        message_id=update.callback_query.message.message_id,
                                        text=text)
    return conversation_states.EDIT_MENU_ITEM_DETAILS


async def menu_item_edit_finish(update: Update, context: CallbackContext):
    change = {context.chat_data["change_menu_item"]["change_type"]: update.message.text}
    item = MenuItem.edit(menu_item_id=int(context.chat_data["change_menu_item"]["id"]), **change)
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(**x)] for x in RESTAURANT_OWNER_BUTTONS])
    message = await context.bot.send_message(chat_id=update.effective_user.id,
                                             text=f"Успішно!\n{str(item)}",
                                             reply_markup=reply_markup)
    context.chat_data["last_message"] = message.message_id
    context.chat_data.pop("change_menu_item")
    return ConversationHandler.END


async def delete_restaurant_confirmation(update: Update, context: CallbackContext):
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(text="Видалити",
                                                               callback_data="restaurant_confirm_delete")],
                                         [InlineKeyboardButton(text="Відмінити",
                                                               callback_data="special_actions")]])
    await update.callback_query.message.edit_text(text="Ви впевнені? Після видалення заклад не можна буде повернути")
    await update.callback_query.message.edit_reply_markup(reply_markup=reply_markup)


async def delete_restaurant_final(update: Update, context: CallbackContext):
    Restaurant.find(owner_id=update.effective_user.id).delete()
    text = "Заклад видалений"
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(**x)] for x in FREE_RESTAURANT_OWNER_BUTTONS])
    await update.callback_query.edit_message_text(text=text,
                                                  reply_markup=reply_markup)


async def restaurant_location_manager(update: Update, context: CallbackContext):
    text = "Менеджер локацій вашого закладу."
    buttons = [[InlineKeyboardButton(text="Добавити локацію",
                                          callback_data="add_restaurant_location")],
                    [InlineKeyboardButton(text="Назад",
                                          callback_data="special_actions")]]
    if Restaurant.find(owner_id=update.effective_user.id).list_locations():
        buttons[0].append(InlineKeyboardButton(text="Редагувати локацію",
                                                    callback_data="edit_restaurant_locations"))
    reply_markup = InlineKeyboardMarkup(buttons)
    await update.callback_query.message.edit_text(text=text,
                                                  reply_markup=reply_markup)


async def add_restaurant_location_name(update: Update, context: CallbackContext):
    text = "Введіть назву для вашої локації: вулицю, номер будинку і т.д.:"
    await update.callback_query.message.edit_text(text=text)
    return conversation_states.ADD_RESTAURANT_LOCATION_NAME


async def add_restaurant_location_location(update: Update, context: CallbackContext):
    context.chat_data["restaurant_location"] = {"location_description": update.message.text}
    text = "Чудово! Тепер надішліть точну локацію вашого закладу (за допомогою 'Пощирити локацію')"
    await context.bot.send_message(chat_id=update.effective_user.id,
                                   text=text)
    return conversation_states.ADD_RESTAURANT_LOCATION_LOCATION


async def add_restaurant_location_finish(update: Update, context: CallbackContext):
    context.chat_data["restaurant_location"]["latitude"] = update.message.location.latitude
    context.chat_data["restaurant_location"]["longitude"] = update.message.location.longitude
    Restaurant.find(owner_id=update.effective_user.id).add_location(**context.chat_data["restaurant_location"])
    text = "Успішно! Локація була додана."
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(**x)]for x in RESTAURANT_OWNER_BUTTONS])
    await context.bot.send_message(chat_id=update.effective_user.id,
                                   text=text,
                                   reply_markup=reply_markup)
    return ConversationHandler.END
