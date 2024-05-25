import telebot
import datetime
from config import TOKEN
from queries import *

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, 'started')

@bot.message_handler(commands=['drizzles'])
def get_drizzles(message):
    user_id = message.from_user.id
    drizzles = get_drizzles(user_id)
    bot.send_message(message.chat.id, f'you have {drizzles} drizzles')

@bot.message_handler(content_types=['sticker'])
def social_credit(message):
    try:
        if message.chat.type == 'supergroup' and not message.reply_to_message.from_user.is_bot and message.reply_to_message.from_user.id != message.from_user.id:
            now = datetime.datetime.now()
            last_time = get_last_sticker_time(message.from_user.id)
            drizzles = get_drizzles(message.from_user.id)

            if (now - datetime.datetime.strptime(last_time, '%Y-%m-%d %H:%M:%S')).total_seconds() < 300:
                bot.send_message(message.chat.id, f'you can vote every 5 minutes\nwait {300 - int((now - datetime.datetime.strptime(last_time, "%Y-%m-%d %H:%M:%S")).total_seconds())} seconds')
                return

            if message.sticker.set_name == 'bbldrizzybot':
                if message.sticker.emoji == '🚸':
                    add_drizzles(message.reply_to_message.from_user.id)
                    drizzles = get_drizzles(message.reply_to_message.from_user.id)
                    add_last_sticker_time(message.from_user.id)
                    bot.send_message(message.chat.id, f'Added {drizzles} Drizzles to {message.reply_to_message.from_user.first_name}\nThey are becoming more Drake!')
                elif message.sticker.emoji == '🎤':
                    subtract_drizzles(message.reply_to_message.from_user.id)
                    drizzles = get_drizzles(message.reply_to_message.from_user.id)
                    add_last_sticker_time(message.from_user.id)
                    bot.send_message(message.chat.id, f'Removed {drizzles} Drizzles from {message.reply_to_message.from_user.first_name}\nThey are becoming more Kendrick!')
            # elif drizzles < 100:
            #     bot.send_message(message.chat.id, f'плохой человек, нужно больше соц. кредитов\n{drizzles} из необходимых 100')
            else:
                bot.send_message(message.chat.id, f'you can vote every 5 minutes\nwait {300 - int((now - datetime.datetime.strptime(last_time, "%Y-%m-%d %H:%M:%S")).total_seconds())} seconds')
    except Exception as e:
        print(e)

bot.polling(none_stop=True)