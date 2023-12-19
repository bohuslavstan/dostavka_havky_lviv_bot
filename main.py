#!/usr/bin/env python
# pylint: disable=unused-argument
# This program is dedicated to the public domain under the CC0 license.

"""
Don't forget to enable inline mode with @BotFather

First, a few handler functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Basic inline bot example. Applies different text transformations.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""
import logging

import yaml
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, InlineQueryHandler, MessageHandler, filters, \
    CallbackQueryHandler, ConversationHandler, PicklePersistence

from callbacks import conversation_states
from callbacks.admin_tools import (
    check_applications, 
    remove_promotions, 
    confirm_remove_promotion, 
    remove_promotion_final,
    accept_application,
    cancel_application)
from callbacks.client_tools import client_saved_location_manager, add_client_location_name, \
    add_client_location_location, add_client_location_finish, edit_client_location_name, edit_client_location_finish, \
    edit_client_locations, start_ordering, choose_restaurant, order_choose_category, order_choose_item, order_add_item, \
    order_remove_item, finish_ordering
from callbacks.delivery_guy_tools import activate_delivery_status, deactivate_delivery_status
from callbacks.general import start_bot, registration, back
from callbacks.restaurant_owner_tools import register_restaurant, added_name, added_description, category_manager, \
    add_category, category_added, edit_categories, change_category_name, choose_menu_category, \
    choose_menu_add_or_delete, add_menu_item_start, add_menu_item_add_description, add_menu_item_add_price, \
    add_menu_item_finish, changed_category_name, delete_category_confirmation, delete_category, \
    delete_menu_item_confirmation, delete_menu_item, edit_menu_item_choose, menu_item_edit_choose, \
    menu_item_edit_finish, menu_item_edit, delete_restaurant_confirmation, delete_restaurant_final, \
    restaurant_location_manager, add_restaurant_location_name, add_restaurant_location_location, \
    add_restaurant_location_finish
from callbacks.special_actions import special_actions_menu, apply_for_promotion

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    with open("config.yml", "r") as file:
        config = yaml.safe_load(file)
    persistence = PicklePersistence(filepath=config["persistence_file"])

    application = Application.builder().token(config["token"]).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start_bot))
    application.add_handler(MessageHandler(filters.CONTACT, registration))
    application.add_handler(CallbackQueryHandler(special_actions_menu, "special_actions"))
    application.add_handler(CallbackQueryHandler(back, "to_start_menu"))
    application.add_handler(CallbackQueryHandler(activate_delivery_status, "start_delivery_job"))
    application.add_handler(CallbackQueryHandler(deactivate_delivery_status, "end_delivery_job"))
    application.add_handler(CallbackQueryHandler(apply_for_promotion, "apply_for_.+"))
    application.add_handler(CallbackQueryHandler(check_applications, "check_applications_.+"))
    application.add_handler(CallbackQueryHandler(remove_promotions, "remove_promotions_.+"))
    application.add_handler(CallbackQueryHandler(confirm_remove_promotion, "downgrade_.+"))
    application.add_handler(CallbackQueryHandler(remove_promotion_final, "confirm_downgrade_.+"))
    application.add_handler(CallbackQueryHandler(accept_application, "accept_promotion_.+"))
    application.add_handler(CallbackQueryHandler(cancel_application, "reject_promotion_.+"))
    application.add_handler(CallbackQueryHandler(category_manager, "category_manager"))
    application.add_handler(CallbackQueryHandler(edit_categories, "edit_menu_category"))
    application.add_handler(CallbackQueryHandler(choose_menu_category, "menu_items_manager"))
    application.add_handler(CallbackQueryHandler(choose_menu_add_or_delete, "menu_item_category_.+"))
    application.add_handler(CallbackQueryHandler(delete_category_confirmation, "menu_category_delete_.+"))
    application.add_handler(CallbackQueryHandler(delete_category, "confirm_category_delete_.+"))
    application.add_handler(CallbackQueryHandler(edit_menu_item_choose, "1_edit_menu_item_.+"))
    application.add_handler(CallbackQueryHandler(delete_menu_item_confirmation, "delete_menu_item_.+"))
    application.add_handler(CallbackQueryHandler(delete_menu_item, "confirm_item_delete_.+"))
    application.add_handler(CallbackQueryHandler(menu_item_edit_choose, "2_edit_menu_item_details_.+"))
    application.add_handler(CallbackQueryHandler(delete_restaurant_confirmation, "delete_restaurant"))
    application.add_handler(CallbackQueryHandler(delete_restaurant_final, "restaurant_confirm_delete"))
    application.add_handler(CallbackQueryHandler(restaurant_location_manager, "restaurant_locations_manager"))
    application.add_handler(CallbackQueryHandler(client_saved_location_manager, "location_manager"))
    application.add_handler(CallbackQueryHandler(edit_client_locations, "edit_client_locations"))

    application.add_handler(CallbackQueryHandler(start_ordering, "make_order"))
    application.add_handler(CallbackQueryHandler(choose_restaurant, "order_choose_location_.+"))
    application.add_handler(CallbackQueryHandler(order_choose_category, "choose_restaurant_.+"))
    application.add_handler(CallbackQueryHandler(order_choose_item, "order_choose_category_.+"))
    application.add_handler(CallbackQueryHandler(order_add_item, "order_add_item_.+"))
    application.add_handler(CallbackQueryHandler(order_remove_item, "order_remove_item_.+"))
    application.add_handler(CallbackQueryHandler(finish_ordering, "order_finish"))

    application.add_handler(ConversationHandler(entry_points=[CallbackQueryHandler(register_restaurant, "create_restaurant")],
                                                states={conversation_states.ENTER_RESTAURANT_NAME: [
                                                        MessageHandler(filters.TEXT, added_name)],
                                                        conversation_states.ENTER_RESTAURANT_DESCRIPTION: [
                                                        MessageHandler(filters.TEXT, added_description)]},
                                                fallbacks=[CommandHandler("start", start_bot)]))

    application.add_handler(ConversationHandler(entry_points=[CallbackQueryHandler(add_category, "add_menu_category")],
                                                states={conversation_states.ENTER_CATEGORY_NAME: [
                                                    MessageHandler(filters.TEXT, category_added)]},
                                                fallbacks=[CommandHandler("start", start_bot)]))

    application.add_handler(ConversationHandler(entry_points=[CallbackQueryHandler(change_category_name, "menu_category_change_.+")],
                                                states={conversation_states.CHANGE_CATEGORY_NAME: [
                                                    MessageHandler(filters.TEXT, changed_category_name)]},
                                                fallbacks=[CommandHandler("start", start_bot)]))

    application.add_handler(ConversationHandler(entry_points=[CallbackQueryHandler(add_menu_item_start, "add_menu_item_.+")],
                                                states={conversation_states.ADD_MENU_ITEM_NAME: [
                                                        MessageHandler(filters.TEXT, add_menu_item_add_description)],
                                                        conversation_states.ADD_MENU_ITEM_DESCRIPTION: [
                                                        MessageHandler(filters.TEXT, add_menu_item_add_price)],
                                                        conversation_states.ADD_MENU_ITEM_PRICE: [
                                                        MessageHandler(filters.TEXT, add_menu_item_finish)]},
                                                fallbacks=[CommandHandler("start", start_bot)]))

    application.add_handler(ConversationHandler(entry_points=[CallbackQueryHandler(menu_item_edit, "3_edit_menu_item_.+")],
                                                states={conversation_states.EDIT_MENU_ITEM_DETAILS: [
                                                    MessageHandler(filters.TEXT, menu_item_edit_finish)]},
                                                fallbacks=[CommandHandler("start", start_bot)]))

    application.add_handler(ConversationHandler(entry_points=[CallbackQueryHandler(add_restaurant_location_name, "add_restaurant_location")],
                                                states={conversation_states.ADD_RESTAURANT_LOCATION_NAME: [
                                                        MessageHandler(filters.TEXT, add_restaurant_location_location)],
                                                        conversation_states.ADD_RESTAURANT_LOCATION_LOCATION: [
                                                        MessageHandler(filters.LOCATION, add_restaurant_location_finish)]},
                                                fallbacks=[CommandHandler("start", start_bot)]))

    application.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(add_client_location_name, "add_сlient_location")],
        states={conversation_states.ADD_CLIENT_LOCATION_NAME: [
            MessageHandler(filters.TEXT, add_client_location_location)],
            conversation_states.ADD_CLIENT_LOCATION_LOCATION: [
                MessageHandler(filters.LOCATION, add_client_location_finish)]},
        fallbacks=[CommandHandler("start", start_bot)]))

    application.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_client_location_name, "client_location_change_name_.+")],
        states={conversation_states.EDIT_CLIENT_LOCATION_NAME: [
            MessageHandler(filters.TEXT, edit_client_location_finish)]},
        fallbacks=[CommandHandler("start", start_bot)]))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()