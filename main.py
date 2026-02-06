#!/usr/bin/env python3
"""
🤖 Telegram Bot Price Analyzer - No Conflict Guaranteed
Version: 12.0 - Conflict Free
"""

import os
import re
import sys
import json
import time
import logging
import threading
from typing import Dict, Any
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# ==================== LOGGING SETUP ====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== CONFIGURATION ====================
TOKEN = os.environ.get("BOT_TOKEN", "")
PORT = int(os.environ.get("PORT", 8443))

if not TOKEN:
    logger.error("❌ BOT_TOKEN is not set!")
    sys.exit(1)

# ==================== IMPORT TELEGRAM ====================
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        Application,
        CommandHandler,
        MessageHandler,
        CallbackQueryHandler,
        ContextTypes,
        filters
    )
    from telegram.error import Conflict, TelegramError
except ImportError as e:
    logger.error(f"❌ Missing dependency: {e}")
    logger.error("Please install: pip install python-telegram-bot==21.7")
    sys.exit(1)

# ==================== HTTP SERVER FOR RENDER ====================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ['/', '/health', '/status']:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = json.dumps({
                "status": "online",
                "service": "bot-price-analyzer",
                "timestamp": datetime.now().isoformat()
            })
            self.wfile.write(response.encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Disable logging for health checks

def run_http_server():
    """راه‌اندازی سرور HTTP برای Render"""
    server = HTTPServer(('0.0.0.0', PORT), HealthHandler)
    logger.info(f"✅ HTTP Server running on port {PORT}")
    server.serve_forever()

# ==================== BOT ANALYZER ====================
class BotAnalyzer:
    """تحلیل‌گر ساده و کارآمد"""
    
    @staticmethod
    def analyze(code: str) -> Dict[str, Any]:
        """تحلیل کد"""
        lines = code.split('\n')
        code_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
        
        analysis = {
            "lines": len(code_lines),
            "features": [],
            "type": "سفارشی"
        }
        
        code_lower = code.lower()
        
        # تشخیص نوع
        if any(x in code_lower for x in ['shop', 'store', 'فروش', 'خرید', 'محصول']):
            analysis["type"] = "فروشگاه آنلاین"
        elif any(x in code_lower for x in ['course', 'lesson', 'آموزش', 'درس', 'آزمون']):
            analysis["type"] = "آموزشی"
        elif any(x in code_lower for x in ['admin', 'group', 'مدیریت', 'گروه', 'kick']):
            analysis["type"] = "مدیریت گروه"
        elif any(x in code_lower for x in ['game', 'play', 'بازی', 'سرگرمی']):
            analysis["type"] = "سرگرمی و بازی"
        
        # ویژگی‌ها
        if 'InlineKeyboardMarkup' in code:
            analysis["features"].append("کیبورد اینلاین")
        if 'ReplyKeyboardMarkup' in code:
            analysis["features"].append("کیبورد معمولی")
        if 'CommandHandler' in code:
            analysis["features"].append("دستورات سفارشی")
        if 'async def' in code:
            analysis["features"].append("برنامه‌نویسی Async")
        if any(x in code_lower for x in ['sqlite', 'mysql', 'postgres']):
            analysis["features"].append("دیتابیس")
        if any(x in code_lower for x in ['zarinpal', 'idpay', 'payment', 'پرداخت']):
            analysis["features"].append("درگاه پرداخت")
        
        # امتیاز
        score = 0
        score += min(analysis["lines"] // 10, 30)  # تا 30 امتیاز برای خطوط کد
        score += len(analysis["features"]) * 5     # 5 امتیاز برای هر ویژگی
        analysis["score"] = min(score, 100)
        
        return analysis
    
    @staticmethod
    def calculate_price(analysis: Dict[str, Any]) -> Dict[str, Any]:
        """محاسبه قیمت"""
        score = analysis["score"]
        
        # قیمت پایه بر اساس نوع
        type_prices = {
            "فروشگاه آنلاین": 3000000,
            "آموزشی": 2500000,
            "مدیریت گروه": 1500000,
            "سرگرمی و بازی": 1800000,
            "سفارشی": 2000000
        }
        
        base_price = type_prices.get(analysis["type"], 2000000)
        
        # ضریب امتیاز (0.5 تا 2)
        score_factor = 0.5 + (score / 100) * 1.5
        
        # محاسبه قیمت
        price_rials = int(base_price * score_factor)
        
        # محدودیت‌ها
        price_rials = max(500000, min(price_rials, 10000000))
        
        # تبدیل ارز
        dollar_rate = 50000
        price_tomans = price_rials // 10
        price_usd = price_rials / dollar_rate
        
        # سطح
        if score >= 80:
            level = "🏆 حرفه‌ای"
        elif score >= 60:
            level = "⭐ پیشرفته"
        elif score >= 40:
            level = "📱 استاندارد"
        else:
            level = "🛠️ ساده"
        
        return {
            "price_rials": price_rials,
            "price_tomans": price_tomans,
            "price_usd": round(price_usd, 2),
            "level": level,
            "score": score,
            "type": analysis["type"]
        }

# ==================== BOT HANDLERS ====================
class SimpleBot:
    """ربات ساده و پایدار"""
    
    def __init__(self):
        self.analyzer = BotAnalyzer()
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دستور /start"""
        text = """
🤖 **ربات تحلیل‌گر قیمت ربات تلگرام**

📊 **نحوه استفاده:**
۱. فایل `.py` ربات خود را ارسال کنید
۲. منتظر تحلیل باشید
۳. گزارش قیمت را دریافت کنید

💰 **قیمت بر اساس:**
• نوع ربات (فروشگاهی، آموزشی، مدیریتی و...)
• قابلیت‌های شناسایی شده
• پیچیدگی کد

👇 **فایل ربات خود را همین حالا ارسال کنید!**
        """
        
        await update.message.reply_text(text, parse_mode='Markdown')
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش فایل"""
        if not update.message.document:
            return
        
        doc = update.message.document
        file_name = doc.file_name or "bot.py"
        
        if not file_name.endswith('.py'):
            await update.message.reply_text("❌ فقط فایل‌های Python (.py)")
            return
        
        try:
            # پیام وضعیت
            msg = await update.message.reply_text("📥 دریافت فایل...")
            
            # دانلود
            file = await doc.get_file()
            content_bytes = await file.download_as_bytearray()
            content = content_bytes.decode('utf-8', errors='ignore')
            
            # تحلیل
            analysis = self.analyzer.analyze(content)
            price = self.analyzer.calculate_price(analysis)
            
            # گزارش
            report = self._create_report(file_name, analysis, price)
            
            await context.bot.delete_message(chat_id=msg.chat_id, message_id=msg.message_id)
            await update.message.reply_text(report, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error: {e}")
            await update.message.reply_text("❌ خطا در پردازش")
    
    def _create_report(self, filename: str, analysis: Dict, price: Dict) -> str:
        """ایجاد گزارش"""
        features_text = "\n".join([f"• ✅ {f}" for f in analysis["features"]]) or "• ❌ ویژگی خاصی شناسایی نشد"
        
        return f"""
📄 **گزارش تحلیل ربات**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 فایل: `{filename}`
⏰ زمان: {datetime.now().strftime('%H:%M')}

🎯 **نوع ربات:** {analysis['type']}
📊 **امتیاز:** {price['score']}/100
🎯 **سطح:** {price['level']}

✨ **ویژگی‌ها:**
{features_text}

💰 **قیمت پیشنهادی:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💵 ریال: **{price['price_rials']:,} ریال**
💳 تومان: **{price['price_tomans']:,} تومان**
💲 دلار: **${price['price_usd']:,}**

🤖 @BotPriceAnalyzer
        """

# ==================== CONFLICT RESOLUTION ====================
async def cleanup_bot(token: str):
    """پاکسازی کامل ربات قبل از شروع"""
    try:
        # ایجاد یک bot موقت برای پاکسازی
        from telegram import Bot
        bot = Bot(token=token)
        
        # حذف webhook (اگر وجود دارد)
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook قبلی حذف شد")
        
        # صبر برای اطمینان از بسته شدن connection قبلی
        await asyncio.sleep(2)
        
    except Exception as e:
        logger.warning(f"⚠️ در پاکسازی: {e}")

# ==================== MAIN APPLICATION ====================
async def run_bot():
    """اجرای اصلی ربات با مدیریت conflict"""
    logger.info("=" * 50)
    logger.info("🤖 Telegram Bot Price Analyzer - Version 12.0")
    logger.info("=" * 50)
    
    # 1. پاکسازی قبل از شروع
    logger.info("🧹 پاکسازی وضعیت قبلی...")
    await cleanup_bot(TOKEN)
    
    # 2. صبر برای اطمینان
    await asyncio.sleep(3)
    
    # 3. ایجاد اپلیکیشن
    app = Application.builder().token(TOKEN).build()
    
    # 4. ثبت هندلرها
    bot = SimpleBot()
    app.add_handler(CommandHandler("start", bot.start))
    app.add_handler(MessageHandler(filters.Document.ALL, bot.handle_document))
    
    # 5. شروع polling با تنظیمات مناسب
    logger.info("🔄 شروع ربات...")
    
    try:
        # استفاده از polling با تنظیمات مخصوص
        await app.initialize()
        await app.start()
        
        # شروع polling با drop_pending_updates
        await app.updater.start_polling(
            drop_pending_updates=True,
            timeout=10,
            poll_interval=0.5,
            allowed_updates=Update.ALL_TYPES
        )
        
        logger.info("✅ ربات فعال و آماده است!")
        
        # نگه داشتن برنامه
        await asyncio.Event().wait()
        
    except Conflict as e:
        logger.error(f"❌ Conflict هنوز وجود دارد: {e}")
        logger.error("لطفا 30 ثانیه صبر کنید و دوباره امتحان کنید")
        await asyncio.sleep(30)
        raise
    
    except KeyboardInterrupt:
        logger.info("👋 دریافت سیگنال توقف")
    
    except Exception as e:
        logger.error(f"❌ خطا: {e}")
    
    finally:
        # توقف ایمن
        try:
            await app.stop()
            await app.shutdown()
            logger.info("✅ ربات خاموش شد")
        except:
            pass

def main():
    """تابع اصلی"""
    # شروع HTTP Server در thread جداگانه
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    logger.info(f"🌐 HTTP Server started on port {PORT}")
    
    # اجرای ربات
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("👋 برنامه متوقف شد")
    except Exception as e:
        logger.error(f"❌ خطای اصلی: {e}")

if __name__ == "__main__":
    main()
