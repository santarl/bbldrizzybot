import sqlite3
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import Sticker
from config import TOKEN

# Function to get a new database connection and cursor
def get_db_connection():
    conn = sqlite3.connect('database.db', check_same_thread=False)
    cursor = conn.cursor()
    return conn, cursor

# Function to close database connection
def close_db_connection(conn):
    conn.commit()
    conn.close()

# Function to create the users table if it doesn't exist
def create_users_table():
    conn, cursor = get_db_connection()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        drizzles INTEGER DEFAULT 100)''')
    # Set drizzles to 960 for @real_noonlord
    cursor.execute('''INSERT OR IGNORE INTO users (user_id, username, drizzles) 
                      VALUES (?, ?, ?)''', (1, 'real_noonlord', 960))
    close_db_connection(conn)


# Function to update drizzles for a user
def update_drizzles(user_id, drizzles):
    conn, cursor = get_db_connection()
    cursor.execute('''INSERT OR REPLACE INTO users (user_id, drizzles) 
                      VALUES (?, ?)''', (user_id, drizzles))
    close_db_connection(conn)

# Function to get drizzles for a user
def get_drizzles(user_id):
    conn, cursor = get_db_connection()
    cursor.execute('''SELECT drizzles FROM users WHERE user_id = ?''', (user_id,))
    row = cursor.fetchone()
    close_db_connection(conn)
    if row:
        return row[0]
    else:
        return 0

# Handler for /start command
def start(update, context):
    update.message.reply_text("Welcome to Drizzles Bot! Use /drizzles to check your drizzles.")

# Handler for /drizzles command
def drizzles(update, context):
    user_id = update.message.from_user.id
    drizzles_count = get_drizzles(user_id)
    update.message.reply_text(f"You have {drizzles_count} drizzles.")

# Handler for /drizzyboard command
def drizzyboard(update, context):
    conn, cursor = get_db_connection()
    cursor.execute('''SELECT username, drizzles FROM users ORDER BY drizzles DESC LIMIT 10''')
    rows = cursor.fetchall()
    close_db_connection(conn)
    drizzyboard_text = "Drizzyboard:\n"
    for index, row in enumerate(rows, start=1):
        drizzyboard_text += f"{index}. {row[0]} - {row[1]} drizzles\n"
    update.message.reply_text(drizzyboard_text)

# Function to update or insert user information
def update_user_info(user_id, username, drizzles):
    conn, cursor = get_db_connection()
    # Sanitize username
    username = username.replace("@", "")
    cursor.execute('''INSERT OR REPLACE INTO users (user_id, username, drizzles) 
                      VALUES (?, ?, ?)''', (user_id, username, drizzles))
    close_db_connection(conn)

# Handler for stickers
def handle_stickers(update, context):
    sticker = update.message.sticker
    sender = update.message.from_user
    sticker_emoji = sticker.emoji
    receiver = update.message.reply_to_message.from_user

    if sender.username or receiver.username is None:
        update.message.reply_text("Please set a username in your Telegram settings to use this bot.")
        return
    
    drizzles_count_replied = get_drizzles(receiver.id)
    drizzles_count_sender = get_drizzles(sender.id)

    if sticker_emoji == "🚸":
        # Increment drizzles for the replied user
        drizzles_count_replied += 5
        drizzles_count_sender -= 5
        update.message.reply_text(f"{sender.username} has gifted 5 Drizzles to {receiver.username} from their account!")

    elif sticker_emoji == "🎤":
        # Decrement drizzles for the user who sent the sticker
        drizzles_count_replied -= 5
        drizzles_count_sender += 5
        update.message.reply_text(f"{sender.username} has borrowed 5 Drizzles from {receiver.username}'s account!")

    update_drizzles(receiver.id, drizzles_count_replied)
    update_drizzles(sender.id, drizzles_count_sender)

    # Update user info
    update_user_info(sender.id, sender.username, get_drizzles(sender.id))
    update_user_info(receiver.id, receiver.username, get_drizzles(receiver.id))

# # Handler for unknown commands
# def unknown(update, context):
#     update.message.reply_text("Sorry, I didn't understand that command.")

def main():
    # Create the users table if it doesn't exist
    create_users_table()

    # Set up the bot
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Add handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("drizzles", drizzles))
    dp.add_handler(CommandHandler("drizzleboard", drizzyboard))
    dp.add_handler(MessageHandler(Filters.sticker, handle_stickers))
    # dp.add_handler(MessageHandler(Filters.command, unknown))

    # Start the Bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
