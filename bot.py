import sqlite3
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from config import TOKEN
from datetime import datetime, timedelta

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
                      VALUES (?, ?)''', ('real_noonlord', 200))
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
        # If the user doesn't exist, initialize them with 50 drizzles
        cursor.execute('''INSERT INTO users (username, drizzles) VALUES (?, ?)''', (username, 50))
        drizzles_count = 50

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
    sticker = update.message.sticker
    sender = update.message.from_user

    if not update.message.reply_to_message:
        update.message.reply_text("`Please reply to a message when sending a sticker.`", parse_mode='MarkdownV2')
        return

    receiver = update.message.reply_to_message.from_user

    if not sender.username or not receiver.username:
        update.message.reply_text("`Both users need to set a username in their Telegram settings to use this bot.`", parse_mode='MarkdownV2')
        return
    
    if sender.id == receiver.id:
        update.message.reply_text("`You don't need me for this, just pretend you're transferring Drizzles to yourself 🤓`", parse_mode='MarkdownV2')
        return

    if receiver.is_bot:
        update.message.reply_text("`I can be your friend but you need to find a real person to play with 🥺`", parse_mode='MarkdownV2')
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
            update.message.reply_text("`Easy Brother, one transaction 🎤🚸 every 30 seconds`", parse_mode='MarkdownV2')
            return

    if sticker.emoji == "🚸":
        drizzles_count_receiver += 5
        drizzles_count_sender -= 5
        update.message.reply_text(f"`{sender_username} has gifted 5 Drizzles to {receiver_username} from their account!`", parse_mode='MarkdownV2')
    elif sticker.emoji == "🎤":
        drizzles_count_receiver -= 5
        drizzles_count_sender += 5
        update.message.reply_text(f"`{sender_username} has borrowed 5 Drizzles from {receiver_username}'s account!`", parse_mode='MarkdownV2')

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

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
