import logging
import sqlite3
import random
import subprocess
import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackContext

# Configuration
BOT_TOKEN = '<YOUR_TELEGRAM_BOT_TOKEN_GOES_HERE>'
DICE_SIDES = 9
WINNING_NUMBERS = [6, 9]
ROLL_COOLDOWN_MINUTES = 60  # Cooldown period in minute
ROLLS_BEFORE_COOLDOWN = 3  # Number of rolls allowed before cooldown
TOKEN_ID = "<TOKEN_ID_OF_THE_TOKEN_TO_SEND>"

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Connect to the SQLite database
conn = sqlite3.connect('users.db')
c = conn.cursor()

# Create table if it doesn't exist for users
c.execute('''CREATE TABLE IF NOT EXISTS users
             (user_id INTEGER PRIMARY KEY, wallet_address TEXT, roll_count INTEGER DEFAULT 0, last_roll_date TEXT)''')
conn.commit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    explanation = ("I'm an alien bot that allows you to roll a dice and potentially win 👽 tokens. Rolling a 6 or 9 is nice. Here are the available commands:\n"
                   "/alien - Display this help message\n"
                   "/roll - Roll the dice and try your luck\n"
                   "/register <walletaddress> - Register your Ergo wallet address\n"
                   "/list - Check the registered wallet address\n"
                   "/update <walletaddress> - Update the registered wallet address\n"
                   "/delete - Delete the registered wallet address")
    await context.bot.send_message(chat_id=update.effective_chat.id, text=explanation)

import asyncio

async def roll(update: Update, context: CallbackContext) -> None:
    # Introduce a delay of 3 seconds
    await asyncio.sleep(3)

    user_id = update.effective_user.id

    # Get the current time
    now = datetime.datetime.now()

    # Get user info from the database
    c.execute("SELECT wallet_address, roll_count, last_roll_date FROM users WHERE user_id=?", (user_id,))
    user_info = c.fetchone()

    if user_info:
        wallet_address, roll_count, last_roll_date_str = user_info
        # Convert last_roll_date string to datetime object
        if last_roll_date_str:
            try:
                last_roll_date = datetime.datetime.strptime(last_roll_date_str, '%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                last_roll_date = None
        else:
            last_roll_date = None
    else:
        await update.message.reply_text("You haven't registered yet. Please register your Ergo wallet address first using /register.")
        return

    # Check if the user has reached the roll limit and is within the cooldown period
    if roll_count >= ROLLS_BEFORE_COOLDOWN and last_roll_date and now < last_roll_date + datetime.timedelta(minutes=ROLL_COOLDOWN_MINUTES):
        # Calculate remaining cooldown time
        remaining_time = (last_roll_date + datetime.timedelta(minutes=ROLL_COOLDOWN_MINUTES)) - now
        minutes = max(remaining_time.seconds // 60, 1)  # Ensure at least 1 minute remaining
        await update.message.reply_text(f"You can roll again in {minutes} minute{'s' if minutes > 1 else ''}.")
        return

    # Roll the dice
    roll_result = random.randint(1, DICE_SIDES)

    # Increment the roll count
    roll_count += 1

    # Set response based on roll result
    if roll_result in WINNING_NUMBERS:
        aliens = random.randint(1, 100) if roll_result == 6 else random.randint(100, 1000)
        await update.message.reply_text(f"You rolled a {roll_result}, so you've won: {aliens} 👽!")
        # Send tokens using subprocess
        process = subprocess.Popen(['ewc', 'wallet-send', '-e', '0.0001', '-t', TOKEN_ID, '-u', str(aliens), '-a', wallet_address, 'alien', '1234', '--sign', '--send'], stdin=subprocess.PIPE)
        process.communicate(input=b'y\n')
        # Add sleep for 3 minutes after a winner rolls
        await update.message.reply_text(f"Rolling has been disabled for everyone for 5 minutes to allow the winners transaction to confirm. This aliens does not know how chained transactions work yet...")
        await asyncio.sleep(300)
    else:
        await update.message.reply_text(f"You rolled a {roll_result}, loser!")

    # Update user info in the database
    c.execute("INSERT OR REPLACE INTO users (user_id, wallet_address, roll_count, last_roll_date) VALUES (?, ?, ?, ?)",
                (user_id, wallet_address, roll_count, now))
    conn.commit()

async def register(update: Update, context: CallbackContext) -> None:
    if not context.args:
        await update.message.reply_text("Please enter your Ergo wallet address after the /register command.")
        return
    
    wallet_address = context.args[0]
    user_id = update.effective_user.id

    # Save the user info and wallet address to the database
    c.execute("INSERT OR REPLACE INTO users (user_id, wallet_address) VALUES (?, ?)", (user_id, wallet_address))
    conn.commit()
    
    await update.message.reply_text(f"Your Ergo wallet address has been registered: {wallet_address}")

async def list_wallet(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    c_wallets.execute("SELECT wallet_address FROM wallets WHERE user_id=?", (user_id,))
    wallet_address = c_wallets.fetchone()

    if wallet_address:
        await update.message.reply_text(f"Your registered Ergo wallet address is: {wallet_address[0]}")
    else:
        await update.message.reply_text("You have not registered a wallet address yet.")

async def update_wallet(update: Update, context: CallbackContext) -> None:
    if not context.args:
        await update.message.reply_text("Please enter your new Ergo wallet address after the /update command.")
        return
    
    new_wallet_address = context.args[0]
    user_id = update.effective_user.id

    c_wallets.execute("UPDATE wallets SET wallet_address=? WHERE user_id=?", (new_wallet_address, user_id))
    conn_wallets.commit()

    await update.message.reply_text(f"Your Ergo wallet address has been updated to: {new_wallet_address}")

async def delete_wallet(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    c_wallets.execute("DELETE FROM wallets WHERE user_id=?", (user_id,))
    conn_wallets.commit()

    await update.message.reply_text("Your registered Ergo wallet address has been deleted.")

if __name__ == '__main__':
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    start_handler = CommandHandler('alien', start)
    roll_handler = CommandHandler('roll', roll)
    register_handler = CommandHandler('register', register)
    list_wallet_handler = CommandHandler('list', list_wallet)
    update_wallet_handler = CommandHandler('update', update_wallet)
    delete_wallet_handler = CommandHandler('delete', delete_wallet)

    application.add_handler(start_handler)
    application.add_handler(roll_handler)
    application.add_handler(register_handler)
    application.add_handler(list_wallet_handler)
    application.add_handler(update_wallet_handler)
    application.add_handler(delete_wallet_handler)
    
    application.run_polling()
