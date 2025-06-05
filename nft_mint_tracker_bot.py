
import os
import json
import logging
import requests
from web3 import Web3
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEB3_PROVIDER = os.getenv("WEB3_PROVIDER")
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID"))
CONTRACT_ADDRESS = "0x33df1aeb441456dd1257c1011c6d776e8464ebf5"
ABI_PATH = "abi.json"

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Connect to Web3
w3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER))
if not w3.is_connected():
    raise Exception("Web3 connection failed")

# Load ABI
with open(ABI_PATH, 'r') as f:
    abi = json.load(f)

contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=abi)

# Telegram command: /mintcount
def mintcount(update: Update, context: CallbackContext) -> None:
    try:
        total_minted = contract.functions.totalMinted().call()
        remaining = contract.functions.remainingSupply().call()
        msg = f"🧮 Mint Count\nTotal Minted: {total_minted}\nRemaining Supply: {remaining}"
    except Exception as e:
        msg = f"Error fetching mint count: {e}"
    update.message.reply_text(msg)

# Fetch metadata and send Telegram message
def send_mint_alert(bot: Bot, chat_id, token_id, to_address):
    try:
        token_uri = contract.functions.tokenURI(token_id).call()
        metadata = requests.get(token_uri).json()
        name = metadata.get("name", f"Token #{token_id}")
        image = metadata.get("image", "")
        text = f"🔥 New Mint Alert!\nToken ID: #{token_id}\nOwner: {to_address}\nName: {name}"
        bot.send_photo(chat_id=chat_id, photo=image, caption=text)
    except Exception as e:
        logger.error(f"Metadata fetch failed: {e}")

# Poll for Transfer events
def watch_events(bot: Bot, chat_id):
    latest_block = w3.eth.block_number
    logger.info("Starting event watch loop")
    while True:
        try:
            new_block = w3.eth.block_number
            if new_block > latest_block:
                events = contract.events.Transfer().createFilter(
                    fromBlock=latest_block + 1, toBlock=new_block
                ).get_all_entries()

                for event in events:
                    from_addr = event["args"]["from"]
                    to_addr = event["args"]["to"]
                    token_id = event["args"]["tokenId"]
                    if from_addr == "0x0000000000000000000000000000000000000000":
                        send_mint_alert(bot, chat_id, token_id, to_addr)

                latest_block = new_block
        except Exception as e:
            logger.error(f"Error polling events: {e}")

# Main bot runner
def main():
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("mintcount", mintcount))
    updater.start_polling()
    logger.info("Bot started")

    # Start watching events
    watch_events(updater.bot, chat_id=os.getenv("TELEGRAM_CHAT_ID"))

if __name__ == "__main__":
    main()
