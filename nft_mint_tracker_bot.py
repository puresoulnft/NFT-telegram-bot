
import os
import json
import logging
import requests
from web3 import Web3
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEB3_PROVIDER = os.getenv("WEB3_PROVIDER")
CONTRACT_ADDRESS=0x33df1aeb441456dd1257c1011c6d776e8464ebf5
ABI_PATH = "abi.json"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

w3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER))
if not w3.is_connected():
    raise Exception("Web3 connection failed")

with open(ABI_PATH, 'r') as f:
    abi = json.load(f)

contract = w3.eth.contract(address=Web3.to_checksum_address(contract_address), abi=abi)

def mintcount(update: Update, context: CallbackContext) -> None:
    try:
        total_minted = contract.functions.totalMinted().call()
        remaining = contract.functions.remainingSupply().call()
        msg = f"🧱 Mint Count\nTotal Minted: {total_minted}\nRemaining Supply: {remaining}"
    except Exception as e:
        msg = f"Error fetching mint count: {e}"
    update.message.reply_text(msg)

def latest(update: Update, context: CallbackContext) -> None:
    try:
        total = contract.functions.totalMinted().call()
        token_id = total - 1
        token_uri = contract.functions.tokenURI(token_id).call()
        metadata = requests.get(token_uri).json()
        msg = f"🆕 Latest NFT Minted\nID: {token_id}\nName: {metadata.get('name')}\n{metadata.get('image')}"
    except Exception as e:
        msg = f"Error fetching latest token: {e}"
    update.message.reply_text(msg)

def preview(update: Update, context: CallbackContext) -> None:
    try:
        token_id = int(context.args[0])
        token_uri = contract.functions.tokenURI(token_id).call()
        metadata = requests.get(token_uri).json()
        msg = f"🔍 NFT Preview\nID: {token_id}\nName: {metadata.get('name')}\n{metadata.get('image')}"
    except Exception as e:
        msg = f"Error fetching token preview: {e}"
    update.message.reply_text(msg)

def owner(update: Update, context: CallbackContext) -> None:
    try:
        token_id = int(context.args[0])
        owner_addr = contract.functions.ownerOf(token_id).call()
        msg = f"👤 Owner of Token {token_id}:\n{owner_addr}"
    except Exception as e:
        msg = f"Error fetching owner: {e}"
    update.message.reply_text(msg)

def rarity(update: Update, context: CallbackContext) -> None:
    try:
        token_id = int(context.args[0])
        details = contract.functions.getTokenDetails(token_id).call()
        msg = f"✨ Token {token_id} Traits:\n{json.dumps(details, indent=2)}"
    except Exception as e:
        msg = f"Error fetching rarity: {e}"
    update.message.reply_text(msg)

def mytokens(update: Update, context: CallbackContext) -> None:
    try:
        address = context.args[0]
        balance = contract.functions.balanceOf(address).call()
        tokens = []
        for i in range(balance):
            token_id = contract.functions.tokenOfOwnerByIndex(address, i).call()
            tokens.append(str(token_id))
        msg = f"🎒 Tokens owned by {address}:\n" + ", ".join(tokens)
    except Exception as e:
        msg = f"Error fetching tokens: {e}"
    update.message.reply_text(msg)

def transfers(update: Update, context: CallbackContext) -> None:
    try:
        latest_block = w3.eth.block_number
        logs = w3.eth.get_logs({
            "fromBlock": latest_block - 2000,
            "toBlock": "latest",
            "address": Web3.to_checksum_address(CONTRACT_ADDRESS),
            "topics": [w3.keccak(text="Transfer(address,address,uint256)").hex()]
        })
        msg = f"📦 Last {len(logs)} NFT Transfer Logs Retrieved"
    except Exception as e:
        msg = f"Error polling events: {e}"
    update.message.reply_text(msg)

def main():
    updater = Updater(TELEGRAM_TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("mintcount", mintcount))
    dp.add_handler(CommandHandler("latest", latest))
    dp.add_handler(CommandHandler("preview", preview))
    dp.add_handler(CommandHandler("owner", owner))
    dp.add_handler(CommandHandler("rarity", rarity))
    dp.add_handler(CommandHandler("mytokens", mytokens))
    dp.add_handler(CommandHandler("transfers", transfers))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
