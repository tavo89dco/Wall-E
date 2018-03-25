#!/usr/bin/env python3
import logging
from time import sleep
import traceback
import sys
from html import escape

from telegram import ParseMode, TelegramError, Update
from telegram.ext import Updater, MessageHandler, CommandHandler, Filters
from telegram.ext.dispatcher import run_async

import python3pickledb as pickledb

# Configuration
BOTNAME = 'Wall-e Go'
TOKEN = '576309431:AAHBEe8bmLgBi-1sMUP3mmiLrVhSicbznnM'

help_text = 'Da la Bienvenida a todo aquel que se une al grupo de Incursiones' \
            'en el que este bot es miembro. Por defecto, solo la persona que invita al bot' \
            'al grupo, es capaz de cambiar las configuraciones.\nCommands:\n\n' \
            '/bienvenido - Configurar mensaje de Bienvenida\n' \
            '/adios - Configurar mensaje de despedida\n' \
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
    bot.sendMessage(*args, **kwargs)


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

# Print help text
def help(bot, update):
    """ Prints help text """

    chat_id = update.message.chat.id
    chat_str = str(chat_id)
    if (not db.get(chat_str + '_quiet') or db.get(chat_str + '_adm') ==
            update.message.from_user.id):
        send_async(bot, chat_id=chat_id,
                   text=help_text,
                   parse_mode=ParseMode.MARKDOWN,
                   disable_web_page_preview=True)