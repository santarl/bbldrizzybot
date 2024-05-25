import sqlite3
from datetime import datetime

DB_FILE = 'database.db'

def add_drizzles(chat_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET social_credit = social_credit + 5 WHERE user_id = ?', (chat_id,))
    conn.commit()
    conn.close()

def subtract_drizzles(chat_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET social_credit = social_credit - 5 WHERE user_id = ?', (chat_id,))
    conn.commit()
    conn.close()

def get_drizzles(chat_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT social_credit FROM users WHERE user_id = ?', (chat_id,))
    res = cursor.fetchone()
    if res is None:
        cursor.execute('INSERT INTO users (user_id, social_credit) VALUES (?, 300)', (chat_id,))
        conn.commit()
        drizzles = 300
    else:
        drizzles = res[0]
    conn.close()
    return drizzles

def add_last_sticker_time(chat_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('UPDATE time_restriction SET last_sticker_time = ? WHERE user_id = ?', (now, chat_id))
    conn.commit()
    conn.close()

def get_last_sticker_time(chat_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT last_sticker_time FROM time_restriction WHERE user_id = ?', (chat_id,))
    last_time = cursor.fetchone()
    if last_time is None:
        cursor.execute('INSERT INTO time_restriction (user_id, last_sticker_time) VALUES (?, ?)', (chat_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        last_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    else:
        last_time = last_time[0]
    conn.close()
    return last_time