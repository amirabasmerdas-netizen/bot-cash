# test_bot.py - برای تست محلی
import asyncio
from bot import BotPriceAnalyzerBot

async def test():
    analyzer = BotPriceAnalyzerBot()
    
    # نمونه کد برای تست
    sample_code = """
from telegram import Update
from telegram.ext import Application, CommandHandler

async def start(update: Update, context):
    await update.message.reply_text("Hello World!")

app = Application.builder().token("TOKEN").build()
app.add_handler(CommandHandler("start", start))
app.run_polling()
    """
    
    features = await analyzer.analyzer.analyze_file(sample_code)
    print(f"Features: {features}")
    
    scoring = await analyzer.scoring_engine.calculate_score(features)
    print(f"Score: {scoring.total_score}")
    
    price = await analyzer.scoring_engine.calculate_price(scoring.total_score)
    print(f"Price: {price.final_price:,} Rials")

if __name__ == "__main__":
    asyncio.run(test())
