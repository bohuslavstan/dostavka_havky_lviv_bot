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

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, InlineQueryHandler, MessageHandler, filters, \
    CallbackQueryHandler, ConversationHandler

from callbacks.admin_tools import (
    check_applications, 
    remove_promotions, 
    confirm_remove_promotion, 
    remove_promotion_final,
    accept_application,
    cancel_application)
from callbacks.delivery_guy_tools import activate_delivery_status, deactivate_delivery_status
from callbacks.general import start_bot, registration, back
from callbacks.restaurant_owner_tools import register_restaurant
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
    application = Application.builder().token("5051303173:AAG_0Lbgy5WGm7iOs4hbcW1EOcAXKlUDGDQ").build()

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

    application.add_handler(ConversationHandler(entry_points=[CallbackQueryHandler(register_restaurant, "create_restaurant")],
                                                states={}))


    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()