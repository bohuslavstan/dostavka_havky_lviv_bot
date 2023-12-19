from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, ConversationHandler

from callbacks import conversation_states
from callbacks.general import get_start_menu
from models.base import User, ClientSavedLocation, Restaurant, OrderHeader, MenuCategory, MenuItem, OrderItem


async def client_saved_location_manager(update: Update, context: CallbackContext):
    text = "Менеджер ваших локацій.\nТут ви можете добавити часто використовувані локації для зручності," \
           " а також підписати їх за своїм бажанням"
    buttons = [[InlineKeyboardButton(text="Добавити локацію",
                                     callback_data="add_сlient_location")],
               [InlineKeyboardButton(text="Назад",
                                     callback_data="special_actions")]]
    if User.get(telegram_id=update.effective_user.id).list_locations():
        buttons[0].append(InlineKeyboardButton(text="Редагувати локацію",
                                               callback_data="edit_client_locations"))
    reply_markup = InlineKeyboardMarkup(buttons)
    await update.callback_query.message.edit_text(text=text,
                                                  reply_markup=reply_markup)


async def add_client_location_name(update: Update, context: CallbackContext):
    text = "Введіть назву для вашої локації: дім, робота і т.д.:"
    await update.callback_query.message.edit_text(text=text)
    return conversation_states.ADD_CLIENT_LOCATION_NAME


async def add_client_location_location(update: Update, context: CallbackContext):
    context.chat_data["client_location"] = {"name": update.message.text}
    text = "Чудово! Тепер надішліть точну локацію (за допомогою 'Пощирити локацію')"
    await context.bot.send_message(chat_id=update.effective_user.id,
                                   text=text)
    return conversation_states.ADD_CLIENT_LOCATION_LOCATION


async def add_client_location_finish(update: Update, context: CallbackContext):
    context.chat_data["client_location"]["latitude"] = update.message.location.latitude
    context.chat_data["client_location"]["longitude"] = update.message.location.longitude
    User.get(telegram_id=update.effective_user.id).add_location(**context.chat_data["client_location"])
    text = "Успішно! Локація була додана."
    await context.bot.send_message(chat_id=update.effective_user.id,
                                   text=text,
                                   reply_markup=get_start_menu())
    return ConversationHandler.END


async def edit_client_locations(update: Update, context: CallbackContext):
    await update.callback_query.message.delete()
    context.chat_data["client_locations"] = {}
    for location in User.get(telegram_id=update.effective_user.id).list_locations():
        text = str(location)
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(text="Змінити назву",
                                                                   callback_data=f"client_location_change_name_{location.id}"),
                                              InlineKeyboardButton(text="Видалити",
                                                                   callback_data=f"client_location_delete_{location.id}")]])
        message = await context.bot.send_message(chat_id=update.effective_user.id,
                                                 text=text,
                                                 reply_markup=reply_markup)
        context.chat_data["client_locations"][location.id] = message


async def edit_client_location_name(update: Update, context: CallbackContext):
    context.chat_data["change_location_id"] = int(update.callback_query.data.replace("client_location_change_name_", ""))
    for location_id, message in context.chat_data["client_locations"].items():
        if location_id == context.chat_data["change_location_id"]:
            text = f"Введіть нову назву для {message.text}:"
            await message.edit_text(text=text)
        else:
            await message.delete()
    context.chat_data.pop("client_locations")
    return conversation_states.EDIT_CLIENT_LOCATION_NAME


async def edit_client_location_finish(update: Update, context: CallbackContext):
    location = ClientSavedLocation.find(location_id=context.chat_data["change_location_id"]).edit(name=update.message.text)
    text = f"Успішно перейменовано в {str(location)}"
    reply_markup = get_start_menu()
    message = await context.bot.send_message(chat_id=update.effective_user.id,
                                             text=text,
                                             reply_markup=reply_markup)
    context.chat_data["last_message"] = message.message_id
    context.chat_data.pop("change_location_id")
    return ConversationHandler.END


async def start_ordering(update: Update, context: CallbackContext):
    locations = User.get(update.effective_user.id).list_locations()
    if locations:
        text = "Виберіть, куди варто доставити замовлення:"
        buttons = [[InlineKeyboardButton(text=str(location),
                                         callback_data=f"order_choose_location_{location.id}")]
                   for location in locations]
        buttons.append([InlineKeyboardButton(text="Назад",
                                            callback_data=f"to_start_menu")])
        reply_markup = InlineKeyboardMarkup(buttons)
    else:
        text = "Для початку, варто добавити локацію, куди доставити замовлення (Менеджер локацій)"
        reply_markup = get_start_menu()
    message = await update.callback_query.message.edit_text(text=text,
                                                            reply_markup=reply_markup)
    context.chat_data["order_message"] = message


async def choose_restaurant(update: Update, context: CallbackContext):
    context.chat_data["order"] = {"location_id": update.callback_query.data.replace("order_choose_location_", "")}
    context.chat_data["restaurant_choose"] = {}
    for restaurant in Restaurant.list_all():
        text = str(restaurant)
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(text="Вибрати цей заклад",
                                                                   callback_data=f"choose_restaurant_{restaurant.id}")]])
        message = await update.effective_user.send_message(text=text,
                                                           reply_markup=reply_markup)
        context.chat_data["restaurant_choose"][restaurant.id] = message


async def order_choose_category(update: Update, context: CallbackContext):
    context.chat_data["order"]["restaurant_id"] = update.callback_query.data.replace("choose_restaurant_", "")
    restaurant_location = Restaurant.get(restaurant_id=context.chat_data["order"]["restaurant_id"]).list_locations()[0]
    if not context.chat_data["order"].get("header"):
        context.chat_data["order"]["header"] = OrderHeader.create(client_id=update.effective_user.id,
                                                                  restaurant_location_id=restaurant_location.id,
                                                                  client_location_id=context.chat_data["order"]["location_id"])
        for restaurant_id, message in context.chat_data["restaurant_choose"].items():
            await message.delete()
        if context.chat_data.get("order_menu_items"):
            for item_id, message in context.chat_data["order_menu_items"].items():
                await message.delete()
            context.chat_data.pop("order_menu_items")
        context.chat_data.pop("restaurant_choose")
    text = f"Ваше замовлення:\n{str(context.chat_data['order']['header'])}"
    buttons = [[InlineKeyboardButton(text=str(category),
                                     callback_data=f"order_choose_category_{category.id}")]
               for category in Restaurant.get(restaurant_id=context.chat_data["order"]["restaurant_id"]).list_categories()]
    reply_markup = InlineKeyboardMarkup(buttons)
    message = await context.chat_data["order_message"].edit_text(text=text,
                                                                 reply_markup=reply_markup)
    context.chat_data["order_message"] = message


async def order_choose_item(update: Update, context: CallbackContext):
    buttons = [[InlineKeyboardButton(text="Назад",
                                     callback_data=f"choose_restaurant_{context.chat_data['order']['restaurant_id']}")]]
    context.chat_data["order"]["header"] = context.chat_data["order"]["header"].update()
    if context.chat_data["order"]["header"].list_items():
        buttons.insert(0, [InlineKeyboardButton(text="Оформити замовлення",
                                                callback_data="finish_order")])
    reply_markup = InlineKeyboardMarkup(buttons)
    await context.chat_data["order_message"].edit_reply_markup(reply_markup=reply_markup)
    context.chat_data["order_menu_items"] = {}
    category_id = int(update.callback_query.data.replace("order_choose_category_", ""))
    for item in MenuCategory.list_items(category_id=category_id):
        text = str(item)
        buttons = [[InlineKeyboardButton(text="Добавити",
                                         callback_data=f"order_add_item_{item.id}")]]
        context.chat_data["order"]["header"] = context.chat_data["order"]["header"].update()
        if context.chat_data["order"]["header"].has_item(item):
            buttons[0].append(InlineKeyboardButton(text="Прибрати",
                                                   callback_data=f"order_remove_item_{item.id}"))
        reply_markup = InlineKeyboardMarkup(buttons)
        message = await update.effective_user.send_message(text=text, reply_markup=reply_markup)
        context.chat_data["order_menu_items"][item.id] = message


async def order_add_item(update: Update, context: CallbackContext):
    menu_item_id = int(update.callback_query.data.replace("order_add_item_", ""))
    menu_item = MenuItem.find(item_id=menu_item_id)
    context.chat_data["order"]["header"] = context.chat_data["order"]["header"].update()
    order_item = context.chat_data["order"]["header"].has_item(menu_item)
    if order_item:
        order_item.change_quantity(1)
    else:
        OrderItem.create(header=context.chat_data["order"]["header"],
                         menu_item=menu_item)
    text = f"Ваше замовлення:\n{str(context.chat_data['order']['header'])}"
    buttons = [[InlineKeyboardButton(text="Назад",
                                     callback_data=f"choose_restaurant_{context.chat_data['order']['restaurant_id']}")]]
    context.chat_data["order"]["header"] = context.chat_data["order"]["header"].update()
    if context.chat_data["order"]["header"].list_items():
        buttons.insert(0, [InlineKeyboardButton(text="Оформити замовлення",
                                                callback_data="finish_order")])
    reply_markup = InlineKeyboardMarkup(buttons)
    await context.chat_data["order_message"].edit_text(text=text,
                                                       reply_markup=reply_markup)
    buttons = [[InlineKeyboardButton(text="Добавити",
                                     callback_data=f"order_add_item_{menu_item_id}"),
                InlineKeyboardButton(text="Прибрати",
                                     callback_data=f"order_remove_item_{menu_item_id}")]]
    reply_markup = InlineKeyboardMarkup(buttons)
    await update.callback_query.message.edit_reply_markup(reply_markup=reply_markup)


async def order_remove_item(update: Update, context: CallbackContext):
    menu_item_id = int(update.callback_query.data.replace("order_remove_item_", ""))
    menu_item = MenuItem.find(item_id=menu_item_id)
    context.chat_data["order"]["header"] = context.chat_data["order"]["header"].update()
    order_item = context.chat_data["order"]["header"].has_item(menu_item)
    quantity = order_item.change_quantity(-1)
    buttons = [[InlineKeyboardButton(text="Добавити",
                                     callback_data=f"order_add_item_{menu_item_id}")]]
    if quantity > 0:
        buttons[0].append(InlineKeyboardButton(text="Прибрати",
                                               callback_data=f"order_remove_item_{menu_item_id}"))

    reply_markup = InlineKeyboardMarkup(buttons)
    await update.callback_query.message.edit_reply_markup(reply_markup=reply_markup)

    context.chat_data['order']['header'] = context.chat_data['order']['header'].update()
    text = f"Ваше замовлення:\n{str(context.chat_data['order']['header'])}"
    buttons = [[InlineKeyboardButton(text="Назад",
                                     callback_data=f"choose_restaurant_{context.chat_data['order']['restaurant_id']}")]]
    context.chat_data["order"]["header"] = context.chat_data["order"]["header"].update()
    if context.chat_data["order"]["header"].list_items():
        buttons.insert(0, [InlineKeyboardButton(text="Оформити замовлення",
                                                callback_data="finish_order")])
    reply_markup = InlineKeyboardMarkup(buttons)
    await context.chat_data["order_message"].edit_text(text=text,
                                                       reply_markup=reply_markup)


async def finish_ordering(update: Update, context: CallbackContext):
    if context.chat_data.get("order_menu_items"):
        for item_id, message in context.chat_data["order_menu_items"].items():
            await message.delete()
        context.chat_data.pop("order_menu_items")
    context.chat_data["order"]["header"].publish()
    await update.callback_query.message.edit_text(f"Ваше замовлення оформлене!\n{str(context.chat_data['order']['header'])}")
    context.chat_data.pop("order")
    context.chat_data.pop("order_message")
