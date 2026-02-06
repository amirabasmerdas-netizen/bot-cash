#!/usr/bin/env python3
"""
🤖 Telegram Bot Price Analyzer - Render Ready
Version: 8.0 - Webhook Mode for Render
"""

import os
import re
import asyncio
import logging
from typing import Dict, Any
from datetime import datetime
from http import HTTPStatus

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Import telegram library
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        Application, CommandHandler, MessageHandler,
        CallbackQueryHandler, ContextTypes, filters
    )
except ImportError:
    print("لطفا ابتدا کتابخانه را نصب کنید:")
    print("pip install python-telegram-bot[job-queue]==21.7")
    exit(1)

# ==================== CONFIGURATION ====================
TOKEN = os.environ.get("BOT_TOKEN", "")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
PORT = int(os.environ.get("PORT", 8443))
HOST = "0.0.0.0"

if not TOKEN:
    logger.error("❌ BOT_TOKEN not set!")
    logger.error("در Render: Environment → Add Environment Variable → BOT_TOKEN")
    exit(1)

# ==================== CODE ANALYZER ====================
class BotAnalyzer:
    """کلاس تحلیل کد ربات"""
    
    @staticmethod
    def analyze(code: str) -> Dict[str, Any]:
        """تحلیل کد پایتون"""
        lines = code.split('\n')
        code_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
        
        code_lower = code.lower()
        
        # محاسبه امتیازها
        score = 0
        features = []
        
        # 1. اندازه پروژه
        loc = len(code_lines)
        if loc > 500:
            score += 25
            features.append("پروژه بزرگ")
        elif loc > 200:
            score += 15
            features.append("پروژه متوسط")
        elif loc > 50:
            score += 5
            features.append("پروژه کوچک")
        
        # 2. دستورات
        if 'commandhandler' in code_lower:
            score += 15
            features.append("دستورات سفارشی")
        
        # 3. کیبوردها
        keyboards = code_lower.count('replykeyboard') + code_lower.count('keyboardmarkup')
        if keyboards > 0:
            score += keyboards * 3
            features.append(f"{keyboards} کیبورد")
        
        # 4. دکمه‌های اینلاین
        inline_buttons = code_lower.count('inlinekeyboard')
        if inline_buttons > 0:
            score += inline_buttons * 2
            features.append(f"{inline_buttons} دکمه اینلاین")
        
        # 5. دیتابیس
        if any(x in code_lower for x in ['sqlite', 'mysql', 'postgres', 'database']):
            score += 20
            features.append("دیتابیس")
        
        # 6. پرداخت
        if any(x in code_lower for x in ['payment', 'zarinpal', 'idpay', 'پرداخت']):
            score += 25
            features.append("درگاه پرداخت")
        
        # 7. Async
        if 'async def' in code_lower:
            score += 10
            features.append("Async")
        
        # 8. Webhook
        if 'webhook' in code_lower:
            score += 5
            features.append("Webhook")
        
        # محدود به 100
        score = min(score, 100)
        
        return {
            'lines': loc,
            'score': score,
            'features': features,
            'keyboards': keyboards,
            'inline_buttons': inline_buttons,
            'has_database': 'دیتابیس' in features,
            'has_payment': 'درگاه پرداخت' in features
        }
    
    @staticmethod
    def calculate_price(analysis: Dict[str, Any]) -> Dict[str, Any]:
        """محاسبه قیمت"""
        score = analysis['score']
        
        # قیمت پایه
        base_price = 2000000  # 2 میلیون ریال
        
        # ضریب امتیاز
        score_factor = 0.5 + (score / 100) * 1.5  # 0.5 تا 2
        
        # نرخ دلار
        dollar_rate = 50000
        
        # محاسبه قیمت
        price_rials = int(base_price * score_factor)
        price_tomans = price_rials // 10
        price_usd = price_rials / dollar_rate
        
        # سطح
        if score >= 80:
            level = "🏆 حرفه‌ای"
        elif score >= 60:
            level = "⭐ متوسط"
        elif score >= 40:
            level = "📱 استاندارد"
        else:
            level = "🛠️ ساده"
        
        return {
            'price_rials': price_rials,
            'price_tomans': price_tomans,
            'price_usd': round(price_usd, 2),
            'level': level,
            'score': score
        }

# ==================== BOT HANDLERS ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور /start"""
    user = update.effective_user
    
    text = f"""
👋 سلام {user.first_name if user else 'کاربر'}!

🤖 **ربات تحلیل‌گر قیمت ربات تلگرام**

📊 **من چکار می‌کنم؟**
• کد Python ربات شما را تحلیل می‌کنم
• قابلیت‌ها را شناسایی می‌کنم  
• قیمت منصفانه پیشنهاد می‌دهم

📁 **نحوه استفاده:**
۱. فایل `.py` ربات خود را ارسال کنید
۲. منتظر تحلیل بمانید
۳. گزارش کامل را دریافت کنید

💰 **قیمت بر اساس:**
• تعداد قابلیت‌ها
• پیچیدگی کد  
• ویژگی‌های فنی

👇 **فایل ربات خود را همین حالا ارسال کنید!**
    """
    
    keyboard = [
        [InlineKeyboardButton("📋 نمونه گزارش", callback_data="sample")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش فایل ارسالی"""
    if not update.message.document:
        await update.message.reply_text("⚠️ لطفا یک فایل ارسال کنید.")
        return
    
    doc = update.message.document
    file_name = doc.file_name or "unknown.py"
    
    if not file_name.endswith('.py'):
        await update.message.reply_text("❌ فقط فایل‌های Python با پسوند `.py`")
        return
    
    # پیام وضعیت
    msg = await update.message.reply_text("📥 در حال دریافت فایل...")
    
    try:
        # دانلود فایل
        file = await doc.get_file()
        content_bytes = await file.download_as_bytearray()
        
        if len(content_bytes) > 1024 * 1024:  # 1MB
            await msg.edit_text("❌ فایل بسیار بزرگ است! (حداکثر 1MB)")
            return
        
        content = content_bytes.decode('utf-8', errors='ignore')
        
        await msg.edit_text("🔍 در حال تحلیل کد...")
        
        # تحلیل
        analyzer = BotAnalyzer()
        analysis = analyzer.analyze(content)
        price = analyzer.calculate_price(analysis)
        
        # گزارش
        report = create_report(file_name, analysis, price)
        
        await context.bot.delete_message(chat_id=msg.chat_id, message_id=msg.message_id)
        await update.message.reply_text(report, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("❌ خطا در پردازش فایل")

def create_report(filename: str, analysis: Dict, price: Dict) -> str:
    """ایجاد گزارش"""
    now = datetime.now().strftime('%Y/%m/%d %H:%M')
    
    features_text = "\n".join([f"• ✅ {f}" for f in analysis['features']])
    if not features_text:
        features_text = "• ❌ ویژگی خاصی شناسایی نشد"
    
    return f"""
📄 **گزارش تحلیل ربات تلگرام**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 فایل: `{filename}`
⏰ زمان: {now}

📊 **نتایج تحلیل:**
• خطوط کد: {analysis['lines']} خط
• امتیاز کلی: {price['score']}/100
• سطح: {price['level']}

🎯 **ویژگی‌های شناسایی شده:**
{features_text}

💰 **قیمت پیشنهادی:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💵 ریال: **{price['price_rials']:,} ریال**
💳 تومان: **{price['price_tomans']:,} تومان**
💲 دلار: **${price['price_usd']:,}**

📝 **توضیح:**
این قیمت بر اساس تحلیل خودکار کد محاسبه شده است.
برای سفارش توسعه: @username

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 ربات تحلیل‌گر قیمت
    """

async def sample(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمونه گزارش"""
    query = update.callback_query
    await query.answer()
    
    text = """
📋 **نمونه تحلیل:**

🤖 **ربات: فروشگاه آنلاین**
📊 **ویژگی‌ها:**
• ۲۰۰ خط کد
• ۵ دستور مختلف  
• ۳ کیبورد اینلاین
• دیتابیس SQLite
• درگاه پرداخت

🎯 **امتیاز: ۷۵/۱۰۰**
💰 **قیمت: ۳,۵۰۰,۰۰۰ ریال**

👇 **برای تحلیل ربات خود:**
فایل Python ربات را ارسال کنید!
    """
    
    keyboard = [
        [InlineKeyboardButton("📤 ارسال فایل", callback_data="send")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """برگشت"""
    query = update.callback_query
    await query.answer()
    await start(update, context)

# ==================== WEB SERVER FOR RENDER ====================
async def health_check(request):
    """Health check endpoint for Render"""
    return {"status": "ok", "service": "telegram-bot-analyzer"}

async def setup_web_server():
    """راه‌اندازی سرور وب برای Render"""
    try:
        from aiohttp import web
        
        app = web.Application()
        app.router.add_get('/health', health_check)
        app.router.add_get('/', health_check)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, HOST, PORT)
        await site.start()
        
        logger.info(f"🌐 Web server running on http://{HOST}:{PORT}")
        return runner
    except ImportError:
        logger.warning("aiohttp not installed, web server not available")
        return None

# ==================== MAIN APPLICATION ====================
async def main():
    """تابع اصلی"""
    logger.info("🤖 در حال راه‌اندازی ربات تحلیل‌گر قیمت...")
    logger.info(f"🔑 BOT_TOKEN: {'✅' if TOKEN else '❌'}")
    logger.info(f"🌐 WEBHOOK_URL: {WEBHOOK_URL or 'Not set'}")
    logger.info(f"🚪 PORT: {PORT}")
    
    # ایجاد اپلیکیشن تلگرام
    application = Application.builder().token(TOKEN).build()
    
    # ثبت هندلرها
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(CallbackQueryHandler(sample, pattern="^sample$"))
    application.add_handler(CallbackQueryHandler(back, pattern="^send$"))
    
    # راه‌اندازی وب سرور برای Render
    web_runner = await setup_web_server()
    
    if WEBHOOK_URL:
        # حالت Webhook
        logger.info(f"🌐 تنظیم Webhook: {WEBHOOK_URL}")
        
        await application.initialize()
        await application.start()
        
        # تنظیم webhook
        webhook_url = f"{WEBHOOK_URL}/{TOKEN}"
        await application.bot.set_webhook(webhook_url)
        
        logger.info(f"✅ Webhook تنظیم شد: {webhook_url}")
        logger.info("🟢 ربات فعال و آماده است!")
        
    else:
        # حالت Polling (برای توسعه)
        logger.info("🔵 استفاده از حالت Polling (توسعه)")
        
        # شروع polling
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        
        logger.info("🟢 ربات در حال Polling...")
    
    # نگه داشتن برنامه
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("👋 دریافت سیگنال توقف...")
    finally:
        # تمیزکاری
        logger.info("🧹 در حال توقف ربات...")
        
        if WEBHOOK_URL:
            await application.bot.delete_webhook()
        
        await application.stop()
        await application.shutdown()
        
        if web_runner:
            await web_runner.cleanup()
        
        logger.info("✅ ربات متوقف شد")

if __name__ == "__main__":
    # اجرای برنامه
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 برنامه متوقف شد")
    except Exception as e:
        logger.error(f"❌ خطای غیرمنتظره: {e}")
        import traceback
        logger.error(traceback.format_exc())
