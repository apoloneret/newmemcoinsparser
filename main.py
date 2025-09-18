import asyncio
from aiogram import Dispatcher, F, Bot
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from scraper import scrape
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from huggingface_hub import InferenceClient
import re
import os
import sqlite3
import logging

logging.basicConfig(
    level=logging.INFO,  
    format="%(asctime)s | %(levelname)s | %(message)s"
)
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_scraped_data = {}
awaiting_wallet = {}

async def telegrambot():
    @dp.message(CommandStart())
    async def command_start_handler(message: Message) -> None:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Start Research", callback_data="start_research")],
            [InlineKeyboardButton(text="📋 See List", callback_data="see_list")],
            [InlineKeyboardButton(text="Connect your wallet", callback_data="connect_wallet")],
            [InlineKeyboardButton(text="My wallets", callback_data="walletslist")]
        ])
        await message.answer("👋 Hello! This bot tracks **new coin launches**. Please choose an option below:", reply_markup=kb)

    @dp.callback_query(F.data == "connect_wallet")
    async def ask_wallet(callback: CallbackQuery):
        awaiting_wallet[callback.from_user.id] = True
        await callback.message.answer("💳 Please send me your wallet address (ETH format 0x...)")
        await callback.answer()

    @dp.message()
    async def save_wallet(message: Message):
        userid = message.from_user.id
        if not awaiting_wallet.get(userid):
            return
        match = re.search(r"0x[a-fA-F0-9]{40}", message.text or "")
        if not match:
            await message.answer("⚠️ Invalid wallet address. Please try again.")
            return
        user_address = match.group(0)
        conn = sqlite3.connect("telegramusers.db")
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (userid INT, userwallet TEXT)''')
        c.execute("INSERT INTO users (userid, userwallet) VALUES (?, ?)", (userid, user_address))
        conn.commit()
        conn.close()
        awaiting_wallet[userid] = False
        await message.answer(f"✅ Your wallet {user_address} has been saved!")

    @dp.callback_query(F.data == "walletslist")
    async def walletsdb(callback: CallbackQuery):
        userid = callback.from_user.id
        conn = sqlite3.connect("telegramusers.db")
        c = conn.cursor()
        c.execute("SELECT userwallet FROM users WHERE userid=?", (userid,))
        rows = c.fetchall()
        conn.close()
        if rows:
            wallets = "\n".join([row[0] for row in rows])
            await callback.message.answer(f"💼 Your wallets:\n{wallets}")
        else:
            await callback.message.answer("⚠️ You don’t have any wallets yet.")
        await callback.answer()

    @dp.callback_query(F.data == "start_research")
    async def start_research(callback: CallbackQuery):
        await callback.message.edit_text("🔎 Starting research...")
        try:
            data = await scrape()
            user_id = callback.from_user.id
            user_scraped_data[user_id] = {'data': data, 'page': 0}
            success_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📋 See List", callback_data="see_list")]
            ])
            await callback.message.edit_text("✅ Research complete!", reply_markup=success_kb)
        except Exception as e:
            await callback.message.edit_text(f"❌ Error during scraping: {str(e)}")
        await callback.answer()

    @dp.callback_query(F.data == "see_list")
    async def see_list(callback: CallbackQuery):
        user_id = callback.from_user.id
        stored = user_scraped_data.get(user_id, {})
        if not stored.get('data'):
            await callback.answer("⚠️ No data available. Start research first.")
            return
        stored['page'] = 0
        await show_page(callback, stored['page'])
        await callback.answer()

    @dp.callback_query(F.data.startswith("page_"))
    async def page_handler(callback: CallbackQuery):
        try:
            page = int(callback.data.split("_")[1])
            await show_page(callback, page)
            await callback.answer()
        except ValueError:
            await callback.answer("⚠️ Invalid page.")

    @dp.callback_query(F.data == "deep_research")
    async def deep_research_handler(callback: CallbackQuery):
        user_id = callback.from_user.id
        stored = user_scraped_data.get(user_id, {})
        if not stored.get('data'):
            await callback.answer("⚠️ No data available.")
            return
        current_page = stored['page']
        token_data = stored['data'][current_page]
        await deep_research(user_id, token_data)
        await callback.answer("🔬 Starting deep research...")

    @dp.callback_query(F.data == "buy")
    async def buy_handler(callback: CallbackQuery):
        user_id = callback.from_user.id
        stored = user_scraped_data.get(user_id, {})
        if not stored.get('data'):
            await callback.answer("⚠️ No token selected.")
            return
        token = stored['data'][stored['page']]
        link = f"https://dexscreener.com{token.get('href', '')}"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Buy on Dexscreener", url=link)]
        ])
        await callback.message.answer(f"To buy **{token.get('trading_name', 'N/A')}**, use the link below:", reply_markup=kb)
        await callback.answer()

async def show_page(callback: CallbackQuery, page: int):
    user_id = callback.from_user.id
    stored = user_scraped_data[user_id]
    data = stored['data']
    total = len(data)
    if page >= total:
        page = total - 1
    elif page < 0:
        page = 0
    token = data[page]
    text = f"📊 Token {page + 1}/{total}\n\n"
    text += f"🪙 Name: {token.get('name', 'N/A')}\n"
    text += f"💱 Trading Name: {token.get('trading_name', 'N/A')}\n"
    text += f"💵 Price: {token.get('price', 'N/A')}\n"
    text += f"⏳ Age: {token.get('age', 'N/A')}\n"
    text += f"📈 Volume: {token.get('volume', 'N/A')}\n"
    text += f"📜 Contract Address: {token.get('contract_address', 'N/A')}\n"
    text += f"🟢 Buys: {token.get('buys', 'N/A')}\n"
    text += f"🔴 Sells: {token.get('sells', 'N/A')}\n"
    text += f"🔗 Link: https://dexscreener.com{token.get('href', 'N/A')}\n" 
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    row = []
    if page > 0:
        row.append(InlineKeyboardButton(text="⬅️ Back", callback_data=f"page_{page - 1}"))
    if page < total - 1:
        row.append(InlineKeyboardButton(text="➡️ Next", callback_data=f"page_{page + 1}"))
    if row:
        kb.inline_keyboard.append(row)
    kb.inline_keyboard.append([InlineKeyboardButton(text="🔬 Make Deep Research", callback_data="deep_research")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="Buy token", callback_data="buy")])
    stored['page'] = page
    await callback.message.edit_text(text, reply_markup=kb)

async def deep_research(user_id: int, token_data: dict):
    try:
        chain = token_data.get('href', '').split('/')[1] if token_data.get('href') and len(token_data.get('href').split('/')) > 1 else 'unknown chain'
        prompt = f"""
Perform a deep analysis of the cryptocurrency token with the following details:
- Name: {token_data.get('name', 'N/A')}
- Trading Name: {token_data.get('trading_name', 'N/A')}
- Price: {token_data.get('price', 'N/A')}
- Age: {token_data.get('age', 'N/A')}
- Volume: {token_data.get('volume', 'N/A')}
- Contract Address: {token_data.get('contract_address', 'N/A')}
- Buys: {token_data.get('buys', 'N/A')}
- Sells: {token_data.get('sells', 'N/A')}
- Link: https://dexscreener.com{token_data.get('href', 'N/A')}
- Blockchain: {chain}
"""
        client = InferenceClient(token=os.getenv("HF_TOKEN", "YOUR_HF_TOKEN_HERE"))
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
            temperature=0.6,
            top_p=0.95
        )
        reply = response.choices[0].message["content"]
        #strips out the thinking and send user directly an answer
        if "</think>" in reply:
            reply = reply.split("</think>", 1)[1].strip()

        full_response = f"🔬 Deep Research Result for {token_data.get('name', 'N/A')}:\n\n{reply}"
        if len(full_response) > 4000:
            full_response = full_response[:4000] + "\n\n... (truncated)"
        await bot.send_message(user_id, full_response)
    except Exception as e:
        await bot.send_message(user_id, f"❌ Error in deep research: {str(e)}")

async def main():
    await telegrambot()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
