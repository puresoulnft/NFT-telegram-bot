
import os
import json
import logging
import requests
from web3 import Web3
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEB3_PROVIDER = os.getenv("WEB3_PROVIDER")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
ABI_PATH = "abi.json"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

w3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER))
if not w3.is_connected():
    raise Exception("Web3 connection failed")

with open(ABI_PATH, 'r') as f:
    abi = json.load(f)

contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=abi)

def mintcount(update: Update, context: CallbackContext) -> None:
    try:
        total_minted = contract.functions.totalMinted().call()
        remaining = contract.functions.remainingSupply().call()
        msg = f"🧱 Mint Count\nTotal Minted: {total_minted}\nRemaining Supply: {remaining}"
    except Exception as e:
        msg = f"⚠️ Error fetching mint count: {e}"
    update.message.reply_text(msg)

def latest(update: Update, context: CallbackContext) -> None:
    try:
        supply = contract.functions.totalMinted().call()
        token_id = supply - 1
        uri = contract.functions.tokenURI(token_id).call()
        msg = f"🆕 Latest NFT Minted\nToken ID: {token_id}\nURI: {uri}"
    except Exception as e:
        msg = f"⚠️ Error fetching latest token: {e}"
    update.message.reply_text(msg)

def preview(update: Update, context: CallbackContext) -> None:
    try:
        token_id = int(context.args[0])
        uri = contract.functions.tokenURI(token_id).call()
        msg = f"🖼️ Preview Token\nToken ID: {token_id}\nURI: {uri}"
    except Exception as e:
        msg = f"⚠️ Error fetching token URI: {e}"
    update.message.reply_text(msg)

def owner(update: Update, context: CallbackContext) -> None:
    try:
        token_id = int(context.args[0])
        wallet = contract.functions.ownerOf(token_id).call()
        msg = f"👛 Owner of Token {token_id}: {wallet}"
    except Exception as e:
        msg = f"⚠️ Error fetching owner: {e}"
    update.message.reply_text(msg)

def rarity(update: Update, context: CallbackContext) -> None:
    try:
        token_id = int(context.args[0])
        traits = contract.functions.getTokenDetails(token_id).call()
        msg = f"🔍 Rarity/Traits of Token {token_id}:\n{traits}"
    except Exception as e:
        msg = f"⚠️ Error fetching rarity: {e}"
    update.message.reply_text(msg)

def mytokens(update: Update, context: CallbackContext) -> None:
    try:
        address = context.args[0]
        balance = contract.functions.balanceOf(address).call()
        tokens = []
        for i in range(balance):
            token = contract.functions.tokenOfOwnerByIndex(address, i).call()
            tokens.append(str(token))
        msg = f"📦 Tokens owned by {address}:\n" + ", ".join(tokens)
    except Exception as e:
        msg = f"⚠️ Error fetching tokens: {e}"
    update.message.reply_text(msg)

def transfers(update: Update, context: CallbackContext) -> None:
    try:
        from_block = w3.eth.block_number - 5000
        event_signature_hash = w3.keccak(text="Transfer(address,address,uint256)").hex()
        logs = w3.eth.get_logs({
            "fromBlock": from_block,
            "toBlock": "latest",
            "address": Web3.to_checksum_address(CONTRACT_ADDRESS),
            "topics": [event_signature_hash]
        })
        msg = f"📤 Last {len(logs)} NFT Transfers\n(Decoded logs not shown)"
    except Exception as e:
        msg = f"⚠️ Error fetching transfers: {e}"
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
