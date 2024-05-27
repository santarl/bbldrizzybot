import sqlite3, time, os, random
from telegram import Update
from telegram.ext import Filters, Updater, CommandHandler, MessageHandler, CallbackContext
from config import TOKEN
from datetime import datetime, timedelta

def stop(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    if chat_id == ADMIN_GROUP:
        update.message.reply_text("Bot is shutting down...")
        context.bot_data['updater'].stop()
        return

# Function to handle /bbldrizzybackup command
def bbldrizzybackup(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    if chat_id != ADMIN_GROUP:
        update.message.reply_text("This command is only available in the specified chat.")
        return

    backup_filename = f"database_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    with open('database.db', 'rb') as file:
        context.bot.send_document(chat_id, document=file, filename=backup_filename)

# Function to handle /bbldrizzyrestore command
def bbldrizzyrestore(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    if chat_id != ADMIN_GROUP:
        update.message.reply_text("This command is only available in the specified chat.")
        return

    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        update.message.reply_text("Please reply to a message containing the database backup file.")
        return

    file = update.message.reply_to_message.document
    if not file.file_name.endswith('.db'):
        update.message.reply_text("Invalid file format. Please send the database backup file.")
        return

    file_id = file.file_id
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            new_file = context.bot.get_file(file_id)
            new_file.download(custom_path='database_restore.db')
            break  # Break out of the loop if download succeeds
        except Exception as e:
            if attempt == max_retries:
                update.message.reply_text("Failed to download the file. Please try again later.")
                return
            else:
                time.sleep(1)  # Wait for 1 second before retrying
    
    os.replace('database_restore.db', 'database.db')
    update.message.reply_text("Database restored successfully.")

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
                        username TEXT PRIMARY KEY,
                        drizzles INTEGER DEFAULT 50,
                        last_sticker_transaction TIMESTAMP)''')
    cursor.execute('''INSERT OR IGNORE INTO users (username, drizzles) 
                      VALUES (?, ?)''', ('real_noonlord', 400))
    cursor.execute('''INSERT OR IGNORE INTO users (username, drizzles) 
                    VALUES (?, ?)''', ('santairl', 50))
    close_db_connection(conn)

# Function to update drizzles for a user
def update_drizzles(username, drizzles):
    conn, cursor = get_db_connection()
    cursor.execute('''INSERT OR REPLACE INTO users (username, drizzles) 
                      VALUES (?, ?)''', (username, drizzles))
    close_db_connection(conn)

# Function to get drizzles for a user
def get_drizzles(username):
    conn = sqlite3.connect('database.db', check_same_thread=False)
    cursor = conn.cursor()

    # Check if the user exists in the database
    cursor.execute('''SELECT drizzles FROM users WHERE username = ?''', (username,))
    row = cursor.fetchone()

    if row:
        drizzles_count = row[0]
    else:
        # If the user doesn't exist, initialize them with random drizzles
        drizzles_count = random.randrange(50, 151, 5)
        cursor.execute('''INSERT INTO users (username, drizzles) VALUES (?, ?)''', (username, drizzles_count))

    conn.commit()
    conn.close()

    return drizzles_count


# Function to get the last sticker transaction time for a user
def get_last_sticker_transaction(username):
    conn, cursor = get_db_connection()
    cursor.execute('''SELECT last_sticker_transaction FROM users WHERE username = ?''', (username,))
    row = cursor.fetchone()
    close_db_connection(conn)
    return row[0] if row else None

# Function to update the last sticker transaction time for a user
def update_last_sticker_transaction(username, timestamp):
    conn, cursor = get_db_connection()
    cursor.execute('''UPDATE users SET last_sticker_transaction = ? WHERE username = ?''', (timestamp, username))
    close_db_connection(conn)

# Handler for /start command
def start(update, context):
    update.message.reply_text("`Welcome to Drizzles Bot! Use /drizzles to check your drizzles.`", parse_mode='MarkdownV2')

# Handler for /drizzles command
def drizzles(update, context):
    username = update.message.from_user.username
    drizzles_count = get_drizzles(username)
    update.message.reply_text(f"`You have {drizzles_count} drizzles.`", parse_mode='MarkdownV2')

# Handler for /drizzleboard command
def drizzleboard(update, context):
    get_drizzles(update.message.from_user.username)
    conn, cursor = get_db_connection()
    # Get all users ordered by drizzles (descending order)
    cursor.execute('''SELECT username, drizzles FROM users ORDER BY drizzles DESC''')
    all_users = cursor.fetchall()
    
    close_db_connection(conn)

    # Determine the number of users for each list
    num_users = len(all_users)
    num_users_per_list = num_users // 2 if num_users >= 10 else num_users // 2 + num_users % 2

    top_5 = all_users[:num_users_per_list]
    bottom_5 = all_users[num_users_per_list:]

    # Display the drizzleboard
    top_5_content = ''.join([f'{index}. {username} - {drizzles} drizzles\n' for index, (username, drizzles) in enumerate(top_5, start=1)])
    bottom_5_content = ''.join([f'{index}. {username} - {drizzles} drizzles\n' for index, (username, drizzles) in enumerate(bottom_5, start=1)])

    # Replace '_' with '\_', '.' with '\.', and '-' with '\-'
    top_5_content = top_5_content.replace('_', '\\_').replace('.', '\\.').replace('-', '\\-')
    bottom_5_content = bottom_5_content.replace('_', '\\_').replace('.', '\\.').replace('-', '\\-')

    drizzleboard_text = (
        '```' + '\n'
        'Drizzleboard\n\n'
        '🚸Most likely to be Drake🚸\n'
        f"{top_5_content}\n"
        '🎤Most likely to be Kendrick🎤\n'
        f"{bottom_5_content}\n"
        '```' + '\n'
    )

    update.message.reply_text(drizzleboard_text, parse_mode='MarkdownV2')


# Function to sanitize username
def sanitize_username(username):
    return username.replace("@", "")

# Handler for stickers
def handle_stickers(update, context):
    message = update.message
    sticker = message.sticker

    # Determine the command based on the sticker or text message
    if sticker:
        # Check if the sticker pack name is "bbldrizzybot"
        if sticker.set_name != "bbldrizzybot":
            message.reply_text("`This sticker is not part of the bbldrizzybot sticker pack.`", parse_mode='MarkdownV2')
            return
        command = sticker.emoji
    else:
        text = message.text.strip().lower()
        if text == "/drake":
            command = "🚸"
        elif text == "/kendrick":
            command = "🎤"
        else:
            return  # Ignore other text messages

    if command == "🎒":
        drizzles(update, context)
        return

    if command == "🥇":
        drizzleboard(update, context)
        return

    if not message.reply_to_message:
        message.reply_text("`Please reply to a message to share Drizzles.`", parse_mode='MarkdownV2')
        return

    sender = message.from_user
    receiver = message.reply_to_message.from_user

    if not sender.username or not receiver.username:
        message.reply_text("`Both users need to set a username in their Telegram settings to use this bot.`", parse_mode='MarkdownV2')
        return

    get_drizzles(sender.username)
    get_drizzles(receiver.username)

    if sender.id == receiver.id:
        message.reply_text("`You don't need me for this, just pretend you're transferring Drizzles to yourself 🤓`", parse_mode='MarkdownV2')
        return

    if receiver.is_bot:
        message.reply_text("`I can be your friend but you need to find a real person to play with 🥺`", parse_mode='MarkdownV2')
        return

    sender_username = sanitize_username(sender.username)
    receiver_username = sanitize_username(receiver.username)

    drizzles_count_sender = get_drizzles(sender_username)
    drizzles_count_receiver = get_drizzles(receiver_username)

    # Check if enough time has passed since the last sticker transaction
    last_transaction_time = get_last_sticker_transaction(sender_username)
    if last_transaction_time:
        time_since_last_transaction = datetime.now() - datetime.strptime(last_transaction_time, "%Y-%m-%d %H:%M:%S")
        if time_since_last_transaction < timedelta(seconds=30):
            message.reply_text("`Easy Brother, one transaction 🎤🚸 every 30 seconds`", parse_mode='MarkdownV2')
            return

    transaction_amount = random.randrange(1, 5)
    if command == "🚸":
        drizzles_count_receiver += transaction_amount
        drizzles_count_sender -= transaction_amount
        message.reply_text(f"`{sender_username} has gifted {transaction_amount} Drizzles to {receiver_username} from their account!`", parse_mode='MarkdownV2')
    elif command == "🎤":
        drizzles_count_receiver -= transaction_amount
        drizzles_count_sender += transaction_amount
        message.reply_text(f"`{sender_username} has borrowed {transaction_amount} Drizzles from {receiver_username}'s account!`", parse_mode='MarkdownV2')

    update_drizzles(receiver_username, drizzles_count_receiver)
    update_drizzles(sender_username, drizzles_count_sender)

    # Update the last sticker transaction time
    update_last_sticker_transaction(sender_username, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# Main function to set up the bot
def main():
    create_users_table()

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("drizzles", drizzles))
    dp.add_handler(CommandHandler("drizzleboard", drizzleboard))
    dp.add_handler(MessageHandler(Filters.sticker, handle_stickers))
    dp.add_handler(CommandHandler("drake", handle_stickers))
    dp.add_handler(CommandHandler("kendrick", handle_stickers))
    dp.add_handler(CommandHandler("bbldrizzybackup", bbldrizzybackup))
    dp.add_handler(CommandHandler("bbldrizzyrestore", bbldrizzyrestore))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()