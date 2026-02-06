#!/usr/bin/env python3
"""
🤖 Telegram Bot Price Analyzer - Final Working Version
"""

import os
import re
import sys
import json
import time
import asyncio
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
                "version": "13.0",
                "timestamp": datetime.now().isoformat()
            })
            self.wfile.write(response.encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

def run_http_server():
    """راه‌اندازی سرور HTTP برای Render"""
    try:
        server = HTTPServer(('0.0.0.0', PORT), HealthHandler)
        logger.info(f"✅ HTTP Server running on port {PORT}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"❌ HTTP Server error: {e}")

# ==================== BOT ANALYZER ====================
class BotAnalyzer:
    """تحلیل‌گر کد ربات"""
    
    @staticmethod
    def analyze(code: str) -> Dict[str, Any]:
        """تحلیل کد پایتون"""
        lines = code.split('\n')
        code_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
        comment_lines = [l for l in lines if l.strip().startswith('#')]
        
        analysis = {
            "lines": len(code_lines),
            "comments": len(comment_lines),
            "features": [],
            "type": "سفارشی"
        }
        
        code_lower = code.lower()
        
        # تشخیص نوع ربات
        if any(x in code_lower for x in ['shop', 'store', 'فروش', 'خرید', 'محصول', 'سبد خرید']):
            analysis["type"] = "فروشگاه آنلاین 🛍️"
        elif any(x in code_lower for x in ['course', 'lesson', 'آموزش', 'درس', 'آزمون', 'سوال']):
            analysis["type"] = "آموزشی 📚"
        elif any(x in code_lower for x in ['admin', 'group', 'مدیریت', 'گروه', 'kick', 'ban']):
            analysis["type"] = "مدیریت گروه 👑"
        elif any(x in code_lower for x in ['game', 'play', 'بازی', 'سرگرمی', 'مسابقه']):
            analysis["type"] = "سرگرمی و بازی 🎮"
        elif any(x in code_lower for x in ['news', 'اخبار', 'اطلاعیه', 'اعلان']):
            analysis["type"] = "اخبار و اطلاع‌رسانی 📰"
        
        # تشخیص ویژگی‌ها
        if 'InlineKeyboardMarkup' in code:
            analysis["features"].append("کیبورد اینلاین ⌨️")
        if 'ReplyKeyboardMarkup' in code:
            analysis["features"].append("کیبورد معمولی ⌨️")
        if 'CommandHandler' in code:
            analysis["features"].append("دستورات سفارشی 📝")
        if 'CallbackQueryHandler' in code:
            analysis["features"].append("دکمه‌های تعاملی 🔘")
        if 'async def' in code:
            analysis["features"].append("برنامه‌نویسی Async ⚡")
        if any(x in code_lower for x in ['sqlite', 'mysql', 'postgres', 'database']):
            analysis["features"].append("دیتابیس 🗄️")
        if any(x in code_lower for x in ['zarinpal', 'idpay', 'nextpay', 'payment', 'پرداخت']):
            analysis["features"].append("درگاه پرداخت 💳")
        if 'requests' in code_lower or 'httpx' in code_lower or 'aiohttp' in code_lower:
            analysis["features"].append("API خارجی 🔗")
        if 'logging' in code_lower:
            analysis["features"].append("سیستم لاگ 📊")
        if 'try:' in code and 'except:' in code:
            analysis["features"].append("مدیریت خطا 🛡️")
        
        # محاسبه امتیاز
        score = 0
        score += min(analysis["lines"] // 10, 30)  # تا 30 امتیاز برای خطوط کد
        score += len(analysis["features"]) * 5     # 5 امتیاز برای هر ویژگی
        if analysis["comments"] > analysis["lines"] * 0.1:  # 10% کامنت
            score += 10
        analysis["score"] = min(score, 100)
        
        return analysis
    
    @staticmethod
    def calculate_price(analysis: Dict[str, Any]) -> Dict[str, Any]:
        """محاسبه قیمت نهایی"""
        score = analysis["score"]
        
        # قیمت پایه بر اساس نوع
        type_prices = {
            "فروشگاه آنلاین 🛍️": 3500000,
            "آموزشی 📚": 2800000,
            "مدیریت گروه 👑": 1800000,
            "سرگرمی و بازی 🎮": 2200000,
            "اخبار و اطلاع‌رسانی 📰": 2500000,
            "سفارشی": 2000000
        }
        
        base_price = type_prices.get(analysis["type"], 2000000)
        
        # ضریب امتیاز (0.5 تا 2)
        score_factor = 0.5 + (score / 100) * 1.5
        
        # محاسبه قیمت
        price_rials = int(base_price * score_factor)
        
        # محدودیت‌ها
        min_price = 500000    # 500 هزار ریال
        max_price = 10000000  # 10 میلیون ریال
        price_rials = max(min_price, min(price_rials, max_price))
        
        # تبدیل ارز
        dollar_rate = 50000   # نرخ دلار
        price_tomans = price_rials // 10
        price_usd = price_rials / dollar_rate
        
        # تعیین سطح
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
            "type": analysis["type"],
            "features_count": len(analysis["features"])
        }

# ==================== BOT HANDLERS ====================
class BotHandlers:
    """Handlerهای ربات"""
    
    def __init__(self):
        self.analyzer = BotAnalyzer()
        self.processing = set()  # کاربران در حال پردازش
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دستور /start"""
        user = update.effective_user
        
        text = f"""
👋 سلام {user.first_name if user else 'کاربر'}!

🤖 **ربات تحلیل‌گر قیمت ربات تلگرام**

✨ **ویژگی‌ها:**
• تشخیص نوع ربات (فروشگاهی، آموزشی، مدیریتی و...)
• شناسایی قابلیت‌ها و امکانات
• محاسبه قیمت منصفانه
• گزارش کامل و شفاف

📊 **نحوه استفاده:**
۱. فایل `.py` ربات خود را ارسال کنید
۲. منتظر تحلیل باشید (۵-۱۰ ثانیه)
۳. گزارش کامل را دریافت کنید

💰 **قیمت بر اساس:**
• نوع و کاربرد ربات
• قابلیت‌های شناسایی شده
• پیچیدگی و کیفیت کد

👇 **فایل ربات خود را همین حالا ارسال کنید!**
        """
        
        keyboard = [
            [InlineKeyboardButton("📋 نمونه گزارش", callback_data="sample")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش فایل ارسالی"""
        user_id = update.effective_user.id
        
        # جلوگیری از درخواست‌های همزمان
        if user_id in self.processing:
            await update.message.reply_text("⏳ در حال پردازش درخواست قبلی...")
            return
        
        if not update.message.document:
            await update.message.reply_text("⚠️ لطفا یک فایل ارسال کنید.")
            return
        
        doc = update.message.document
        file_name = doc.file_name or "bot.py"
        
        if not file_name.endswith('.py'):
            await update.message.reply_text("❌ فقط فایل‌های Python با پسوند `.py`")
            return
        
        self.processing.add(user_id)
        
        try:
            # پیام وضعیت
            status_msg = await update.message.reply_text("📥 در حال دریافت فایل...")
            
            # دانلود فایل
            file = await doc.get_file()
            content_bytes = await file.download_as_bytearray()
            
            # بررسی حجم
            if len(content_bytes) > 2 * 1024 * 1024:  # 2MB
                await status_msg.edit_text("❌ فایل بسیار بزرگ است! (حداکثر 2MB)")
                return
            
            content = content_bytes.decode('utf-8', errors='ignore')
            
            await status_msg.edit_text("🔍 در حال تحلیل کد...")
            
            # تحلیل کد
            analysis = self.analyzer.analyze(content)
            
            await status_msg.edit_text("💰 محاسبه قیمت...")
            
            # محاسبه قیمت
            price_result = self.analyzer.calculate_price(analysis)
            
            # تولید گزارش
            report = self._create_report(file_name, analysis, price_result)
            
            # حذف پیام وضعیت
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=status_msg.message_id
            )
            
            # ارسال گزارش
            await update.message.reply_text(report, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            await update.message.reply_text("❌ خطا در پردازش فایل. لطفا دوباره تلاش کنید.")
        
        finally:
            self.processing.discard(user_id)
    
    def _create_report(self, filename: str, analysis: Dict, price: Dict) -> str:
        """ایجاد گزارش کامل"""
        now = datetime.now().strftime('%Y/%m/%d %H:%M')
        
        # ویژگی‌ها
        features_text = ""
        if analysis["features"]:
            features_text = "\n".join([f"• {feature}" for feature in analysis["features"][:8]])  # حداکثر ۸ ویژگی
            if len(analysis["features"]) > 8:
                features_text += f"\n• ... و {len(analysis['features']) - 8} مورد دیگر"
        else:
            features_text = "• ❌ ویژگی خاصی شناسایی نشد"
        
        # گزارش نهایی
        report = f"""
📄 **گزارش تحلیل ربات تلگرام**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 فایل: `{filename}`
⏰ زمان تحلیل: {now}

🎯 **نوع ربات:** {analysis['type']}
📊 **امتیاز کلی:** {price['score']}/100
🎯 **سطح:** {price['level']}

📈 **تحلیل فنی:**
• خطوط کد: {analysis['lines']} خط
• خطوط کامنت: {analysis['comments']} خط
• تعداد ویژگی‌ها: {price['features_count']} مورد

✨ **ویژگی‌های شناسایی شده:**
{features_text}

💰 **قیمت پیشنهادی:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💵 ریال: **{price['price_rials']:,} ریال**
💳 تومان: **{price['price_tomans']:,} تومان**
💲 دلار: **${price['price_usd']:,}**

💡 **توضیح قیمت:**
قیمت بر اساس نوع ربات، قابلیت‌ها و کیفیت کد محاسبه شده است.

📝 **نکات مهم:**
• این تحلیل بر اساس کد فعلی ربات است
• قیمت‌های بازار ممکن است متفاوت باشند
• برای سفارش توسعه با @username تماس بگیرید

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 ربات تحلیل‌گر قیمت - نسخه ۱۳.۰
        """
        
        return report
    
    async def sample(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمونه گزارش"""
        query = update.callback_query
        await query.answer()
        
        text = """
📋 **نمونه گزارش تحلیل:**

🎯 **تشخیص:** فروشگاه آنلاین 🛍️
📊 **امتیاز:** ۷۵/۱۰۰
🎯 **سطح:** ⭐ پیشرفته

✨ **ویژگی‌ها:**
• کیبورد اینلاین ⌨️
• دستورات سفارشی 📝
• دیتابیس 🗄️
• درگاه پرداخت 💳
• مدیریت خطا 🛡️

💰 **قیمت:**
• ریال: ۴,۲۰۰,۰۰۰ ریال
• تومان: ۴۲۰,۰۰۰ تومان
• دلار: ۸۴ دلار

👇 **ربات خود را تحلیل کنید!**
        """
        
        keyboard = [
            [InlineKeyboardButton("📤 ارسال فایل ربات", callback_data="send")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def send_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """درخواست ارسال فایل"""
        query = update.callback_query
        await query.answer()
        await self.start(update, context)

# ==================== BOT SETUP ====================
async def setup_bot():
    """تنظیم و راه‌اندازی ربات"""
    logger.info("=" * 60)
    logger.info("🤖 Telegram Bot Price Analyzer - Version 13.0")
    logger.info("=" * 60)
    
    # ایجاد اپلیکیشن
    application = Application.builder().token(TOKEN).build()
    
    # ایجاد هندلرها
    handlers = BotHandlers()
    
    # ثبت هندلرها
    application.add_handler(CommandHandler("start", handlers.start))
    application.add_handler(CommandHandler("help", handlers.start))
    application.add_handler(MessageHandler(filters.Document.ALL, handlers.handle_document))
    application.add_handler(CallbackQueryHandler(handlers.sample, pattern="^sample$"))
    application.add_handler(CallbackQueryHandler(handlers.send_file, pattern="^send$"))
    
    logger.info("✅ تنظیمات ربات کامل شد")
    
    return application

async def run_bot_with_retry():
    """اجرای ربات با قابلیت retry"""
    max_retries = 3
    retry_delay = 10  # ثانیه
    
    for attempt in range(max_retries):
        try:
            logger.info(f"🔄 تلاش {attempt + 1} از {max_retries}...")
            
            # تنظیم ربات
            app = await setup_bot()
            
            # پاکسازی قبل از شروع
            try:
                await app.bot.delete_webhook(drop_pending_updates=True)
                logger.info("✅ Webhook قبلی حذف شد")
                await asyncio.sleep(2)
            except:
                pass
            
            # شروع polling
            await app.initialize()
            await app.start()
            await app.updater.start_polling(
                drop_pending_updates=True,
                timeout=20,
                poll_interval=0.5,
                allowed_updates=["message", "callback_query"]
            )
            
            logger.info("✅ ربات فعال و آماده است!")
            
            # نگه داشتن برنامه
            await asyncio.Event().wait()
            
            break
            
        except Conflict as e:
            logger.error(f"❌ Conflict error (تلاش {attempt + 1}): {e}")
            
            if attempt < max_retries - 1:
                logger.info(f"⏳ صبر {retry_delay} ثانیه برای تلاش مجدد...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error("❌ تعداد تلاش‌ها به پایان رسید")
                raise
                
        except KeyboardInterrupt:
            logger.info("👋 دریافت سیگنال توقف")
            break
            
        except Exception as e:
            logger.error(f"❌ خطای غیرمنتظره: {e}")
            break

# ==================== MAIN FUNCTION ====================
def main():
    """تابع اصلی"""
    # شروع HTTP Server در thread جداگانه
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    logger.info(f"🌐 HTTP Server started on port {PORT}")
    
    # اجرای ربات
    try:
        asyncio.run(run_bot_with_retry())
    except KeyboardInterrupt:
        logger.info("👋 برنامه متوقف شد")
    except Exception as e:
        logger.error(f"❌ خطای اصلی: {e}")

if __name__ == "__main__":
    main()
