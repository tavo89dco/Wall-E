#!/usr/bin/env python3
import logging
from time import sleep
import traceback
import sys
from html import escape

from telegram import Emoji, ParseMode, TelegramError, Update
from telegram.ext import Updater, MessageHandler, CommandHandler, Filters
from telegram.ext.dispatcher import run_async

import python3pickledb as pickledb

# Configuration
BOTNAME = 'Wall_eGoBot'
TOKEN = '576309431:AAHBEe8bmLgBi-1sMUP3mmiLrVhSicbznnM'
BOTAN_TOKEN = 'BOTANTOKEN'

help_text = 'Da la Bienvenida a todo aquel que se une al grupo de Incursiones' \
            'en el que este bot es miembro. Por defecto, solo la persona que invita al bot' \
            'al grupo, es capaz de cambiar las configuraciones.\nCommands:\n\n' \
            '/bienvenido - Configurar mensaje de Bienvenida\n' \
            '/adios - Configurar mensaje de despedida\n' \
            '/deshabilitar\\_adios - Deshabilitar el mensaje de despedida \n' \
            '/lock - Solo la persona que invita al bot puede cambiar los mensajes\n' \
            '/unlock - Cualquiera puede cambiar los mensajes\n' \
            '/quiet - Deshabilitar "Lo siento, solo la persona que..." ' \
            'y mensajes de ayuda\n' \
            '/unquiet - Habilita "Lo siento, solo la persona que..." ' \
            'y mensajes de ayuda\n\n' \
            'Puedes usar _$username_ y _$title_ como marcador cuando configuras el' \
            ' mensaje. [HTML formatting]' \
            '(https://core.telegram.org/bots/api#formatting-options) ' \
            'tambien es soportado.\n' \
            'Creditos [califiquenlo](http://storebot.me/bot/jh0ker_welcomebot) :) '
'''
Create database object
Database schema:
<chat_id> -> mensaje de bienvenida
<chat_id>_bye -> mensaje de despedida
<chat_id>_adm -> id del usuario que invito al bot
<chat_id>_lck -> boolean if the bot is locked or unlocked
<chat_id>_quiet -> boolean if the bot is quieted
chats -> lista de los id de chats de los que el bot ha recibido mensajes. 
'''
# Create database object
db = pickledb.load('bot.db', True)

if not db.get('chats'):
    db.set('chats', [])

# Set up logging
root = logging.getLogger()
root.setLevel(logging.INFO)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)


@run_async
def send_async(bot, *args, **kwargs):
    bot.sendMessage(*args, **kwargs);


def check(bot, update, override_lock=None):
    """
    Perform some checks on the update. If checks were successful, returns True,
    else sends an error message to the chat and returns False.
    """

    chat_id = update.message.chat_id
    chat_str = str(chat_id)

    if chat_id > 0:
        send_async(bot, chat_id=chat_id,
                   text='Please add me to a group first!')
        return False

    locked = override_lock if override_lock is not None \
        else db.get(chat_str + '_lck')

    if locked and db.get(chat_str + '_adm') != update.message.from_user.id:
        if not db.get(chat_str + '_quiet'):
            send_async(bot, chat_id=chat_id, text='Sorry, only the person who '
                                                  'invited me can do that.')
        return False

    return True


# Welcome a user to the chat
def bienvenido(bot, update):
    """Bienvenid@! $username

¡Espero que puedas compartir muchos encuentros con nosotros! 
Estas son las reglas del grupo. Por cualquier duda, puedes consultar con algun administrador.
     
REGLAS:
· Por favor, ver el tutorial del bot para saber cómo anclar raids y confirmar tu asistencia.
· No se pasan códigos de grupos privados de raids a jugadores que no se encuentran presentes en el lugar.
· Normalmente se espera a los que faltan llegar a la raid hasta los últimos 20 minutos.
· Si se quiere, y están todos de acuerdo, incluso se puede esperar unos minutos más.
· No se permite referencias al uso de aplicaciones de terceros para falsificar la ubicacion del GPS
· Por último, pero no menos importante, no se debe insultar ni tratar mal a NADIE. """

    message = update.message
    chat_id = message.chat.id
    logger.info('%s joined to chat %d (%s)'
                 % (escape(message.new_chat_member.first_name),
                    chat_id,
                    escape(message.chat.title)))

    # Pull the custom message for this chat from the database
    text = db.get(str(chat_id))

    # Use default message if there's no custom one set
    if text is None:
        text = 'Hello $username! Welcome to $title %s' \
                  % Emoji.GRINNING_FACE_WITH_SMILING_EYES

    # Replace placeholders and send message
    text = text.replace('$username',
                        message.new_chat_member.first_name)\
        .replace('$title', message.chat.title)
    send_async(bot, chat_id=chat_id, text=text, parse_mode=ParseMode.HTML)


# Welcome a user to the chat
def adios(bot, update):
    """ Vuelve pronto! No dejes de escribir! """

    message = update.message
    chat_id = message.chat.id
    logger.info('%s left chat %d (%s)'
                 % (escape(message.left_chat_member.first_name),
                    chat_id,
                    escape(message.chat.title)))

    # Pull the custom message for this chat from the database
    text = db.get(str(chat_id) + '_bye')

    # Goodbye was disabled
    if text is False:
        return

    # Use default message if there's no custom one set
    if text is None:
        text = 'Goodbye, $username!'

    # Replace placeholders and send message
    text = text.replace('$username',
                        message.left_chat_member.first_name)\
        .replace('$title', message.chat.title)
    send_async(bot, chat_id=chat_id, text=text, parse_mode=ParseMode.HTML)


# Introduce the bot to a chat its been added to
def introduce(bot, update):
    """ Hola, mi nombre es Wall-e"""

    chat_id = update.message.chat.id
    invited = update.message.from_user.id

    logger.info('Invited by %s to chat %d (%s)'
                % (invited, chat_id, update.message.chat.title))

    db.set(str(chat_id) + '_adm', invited)
    db.set(str(chat_id) + '_lck', True)

    text = 'Hello %s! I will now greet anyone who joins this chat with a' \
           ' nice message %s \nCheck the /help command for more info!'\
           % (update.message.chat.title,
              Emoji.GRINNING_FACE_WITH_SMILING_EYES)
    send_async(bot, chat_id=chat_id, text=text)


# Print help text
def ayuda(bot, update):
    """ Prints help text """

    chat_id = update.message.chat.id
    chat_str = str(chat_id)
    if (not db.get(chat_str + '_quiet') or db.get(chat_str + '_adm') ==
            update.message.from_user.id):
        send_async(bot, chat_id=chat_id,
                   text=help_text,
                   parse_mode=ParseMode.MARKDOWN,
                   disable_web_page_preview=True)


# Set custom message
def set_welcome(bot, update, args):
    """ Sets custom welcome message """

    chat_id = update.message.chat.id

    # Check admin privilege and group context
    if not check(bot, update):
        return

    # Split message into words and remove mentions of the bot
    message = ' '.join(args)

    # Only continue if there's a message
    if not message:
        send_async(bot, chat_id=chat_id, 
                   text='You need to send a message, too! For example:\n'
                        '<code>/welcome Hello $username, welcome to '
                        '$title!</code>',
                   parse_mode=ParseMode.HTML)
        return

    # Put message into database
    db.set(str(chat_id), message)

    send_async(bot, chat_id=chat_id, text='Got it!')


# Set custom message
def set_goodbye(bot, update, args):
    """ Enables and sets custom goodbye message """

    chat_id = update.message.chat.id

    # Check admin privilege and group context
    if not check(bot, update):
        return

    # Split message into words and remove mentions of the bot
    message = ' '.join(args)

    # Only continue if there's a message
    if not message:
        send_async(bot, chat_id=chat_id, 
                   text='You need to send a message, too! For example:\n'
                        '<code>/goodbye Goodbye, $username!</code>',
                   parse_mode=ParseMode.HTML)
        return

    # Put message into database
    db.set(str(chat_id) + '_bye', message)

    send_async(bot, chat_id=chat_id, text='Got it!')


def disable_goodbye(bot, update):
    """ Disables the goodbye message """

    chat_id = update.message.chat.id

    # Check admin privilege and group context
    if not check(bot, update):
        return

    # Disable goodbye message
    db.set(str(chat_id) + '_bye', False)

    send_async(bot, chat_id=chat_id, text='Got it!')


def lock(bot, update):
    """ Locks the chat, so only the invitee can change settings """

    chat_id = update.message.chat.id

    # Check admin privilege and group context
    if not check(bot, update, override_lock=True):
        return

    # Lock the bot for this chat
    db.set(str(chat_id) + '_lck', True)

    send_async(bot, chat_id=chat_id, text='Got it!')


def quiet(bot, update):
    """ Quiets the chat, so no error messages will be sent """

    chat_id = update.message.chat.id

    # Check admin privilege and group context
    if not check(bot, update, override_lock=True):
        return

    # Lock the bot for this chat
    db.set(str(chat_id) + '_quiet', True)

    send_async(bot, chat_id=chat_id, text='Got it!')


def unquiet(bot, update):
    """ Unquiets the chat """

    chat_id = update.message.chat.id

    # Check admin privilege and group context
    if not check(bot, update, override_lock=True):
        return

    # Lock the bot for this chat
    db.set(str(chat_id) + '_quiet', False)

    send_async(bot, chat_id=chat_id, text='Got it!')


def unlock(bot, update):
    """ Unlocks the chat, so everyone can change settings """

    chat_id = update.message.chat.id

    # Check admin privilege and group context
    if not check(bot, update):
        return

    # Unlock the bot for this chat
    db.set(str(chat_id) + '_lck', False)

    send_async(bot, chat_id=chat_id, text='Got it!')


def empty_message(bot, update):
    """
    Empty messages could be status messages, so we check them if there is a new
    group member, someone left the chat or if the bot has been added somewhere.
    """

    # Keep chatlist
    chats = db.get('chats')

    if update.message.chat.id not in chats:
        chats.append(update.message.chat.id)
        db.set('chats', chats)
        logger.info("I have been added to %d chats" % len(chats))

    if update.message.new_chat_member is not None:
        # Bot was added to a group chat
        if update.message.new_chat_member.username == BOTNAME:
            return introduce(bot, update)
        # Another user joined the chat
        else:
            return bienvenido(bot, update)

    # Someone left the chat
    elif update.message.left_chat_member is not None:
        if update.message.left_chat_member.username != BOTNAME:
            return adios(bot, update)



def error(bot, update, error, **kwargs):
    """ Error handling """

    try:
        if isinstance(error, TelegramError)\
                and error.message == "Unauthorized"\
                or "PEER_ID_INVALID" in error.message\
                and isinstance(update, Update):

            chats = db.get('chats')
            chats.remove(update.message.chat_id)
            db.set('chats', chats)
            logger.info('Removed chat_id %s from chat list'
                        % update.message.chat_id)
        else:
            logger.error("An error (%s) occurred: %s"
                         % (type(error), error.message))
    except:
        pass



def main():
    # Create the Updater and pass it your bot's token.
    updater = Updater(TOKEN, workers=10)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", help))
    dp.add_handler(CommandHandler("ayuda", help))
    dp.add_handler(CommandHandler('bienvenido', set_welcome, pass_args=True))
    dp.add_handler(CommandHandler('adios', set_goodbye, pass_args=True))
    dp.add_handler(CommandHandler('disable_goodbye', disable_goodbye))
    dp.add_handler(CommandHandler("lock", lock))
    dp.add_handler(CommandHandler("unlock", unlock))
    dp.add_handler(CommandHandler("quiet", quiet))
    dp.add_handler(CommandHandler("unquiet", unquiet))

    dp.add_handler(MessageHandler([Filters.status_update], empty_message))
    dp.add_handler(MessageHandler([Filters.text], stats))

    dp.add_error_handler(error)

    update_queue = updater.start_polling(timeout=30, clean=False)

    updater.idle()

if __name__ == '__main__':
    main()