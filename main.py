#!/usr/bin/env python3
"""
🤖 Telegram Bot Price Analyzer - Final Fixed Version
Version: 6.0 - Compatible with python-telegram-bot 21.7
"""

import os
import re
import asyncio
import logging
from typing import Dict, List, Any
from datetime import datetime

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
except ImportError as e:
    logger.error(f"لطفا کتابخانه را نصب کنید: pip install python-telegram-bot==21.7")
    logger.error(f"Error: {e}")
    exit(1)

# ==================== CONFIGURATION ====================
TOKEN = os.environ.get("BOT_TOKEN", "")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
PORT = int(os.environ.get("PORT", 8443))

# ==================== CODE ANALYZER ====================
class CodeAnalyzer:
    """تحلیل‌گر کد ربات تلگرام"""
    
    @staticmethod
    def analyze(code: str) -> Dict[str, Any]:
        """تحلیل کد پایتون"""
        
        result = {
            "commands": [],
            "keyboards": 0,
            "inline_buttons": 0,
            "has_database": False,
            "has_payment": False,
            "has_admin": False,
            "has_webhook": False,
            "is_async": False,
            "lines_of_code": 0,
            "features": []
        }
        
        lines = code.split('\n')
        code_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
        result["lines_of_code"] = len(code_lines)
        
        code_lower = code.lower()
        
        # تشخیص دستورات
        if 'commandhandler' in code_lower or '@app.command' in code_lower:
            result["commands"] = ['start', 'help', 'custom']
        
        # تشخیص کیبوردها
        result["keyboards"] = code_lower.count('replykeyboard')
        result["inline_buttons"] = code_lower.count('inlinekeyboard')
        
        # تشخیص ویژگی‌ها
        result["has_database"] = any(x in code_lower for x in ['sqlite', 'mysql', 'postgres', 'database', 'db'])
        result["has_payment"] = any(x in code_lower for x in ['payment', 'zarinpal', 'idpay', 'nextpay', 'پرداخت'])
        result["has_admin"] = 'admin' in code_lower or 'مدیر' in code_lower
        result["has_webhook"] = 'webhook' in code_lower
        result["is_async"] = 'async def' in code_lower
        
        # جمع‌آوری ویژگی‌ها
        features = []
        if result["has_database"]:
            features.append("دیتابیس")
        if result["has_payment"]:
            features.append("درگاه پرداخت")
        if result["has_admin"]:
            features.append("پنل ادمین")
        if result["is_async"]:
            features.append("Async")
        if result["has_webhook"]:
            features.append("Webhook")
        
        result["features"] = features
        
        return result
    
    @staticmethod
    def calculate_price(analysis: Dict[str, Any]) -> Dict[str, Any]:
        """محاسبه قیمت بر اساس تحلیل"""
        
        # امتیازدهی
        score = 0
        
        # دستورات
        score += len(analysis["commands"]) * 3
        
        # رابط کاربری
        score += analysis["keyboards"] * 2
        score += analysis["inline_buttons"] * 1
        
        # ویژگی‌های فنی
        if analysis["has_database"]:
            score += 10
        if analysis["has_payment"]:
            score += 15
        if analysis["has_admin"]:
            score += 8
        if analysis["is_async"]:
            score += 5
        if analysis["has_webhook"]:
            score += 5
        
        # اندازه پروژه
        if analysis["lines_of_code"] > 500:
            score += 20
        elif analysis["lines_of_code"] > 200:
            score += 15
        elif analysis["lines_of_code"] > 100:
            score += 10
        elif analysis["lines_of_code"] > 50:
            score += 5
        
        # محدود به 100
        score = min(score, 100)
        
        # قیمت‌گذاری
        base_price = 2000000  # 2 میلیون ریال
        dollar_rate = 50000   # نرخ دلار
        
        # ضریب امتیاز
        score_factor = 0.5 + (score / 100) * 1.5  # 0.5 تا 2
        
        # محاسبه قیمت
        price_rials = int(base_price * score_factor)
        price_tomans = price_rials // 10
        price_usd = price_rials / dollar_rate
        
        return {
            "score": score,
            "price_rials": price_rials,
            "price_tomans": price_tomans,
            "price_usd": price_usd,
            "level": CodeAnalyzer._get_level(score)
        }
    
    @staticmethod
    def _get_level(score: float) -> str:
        """تعیین سطح ربات"""
        if score >= 80:
            return "حرفه‌ای 🏆"
        elif score >= 60:
            return "متوسط ⭐"
        elif score >= 40:
            return "استاندارد 📱"
        else:
            return "ساده 🛠️"

# ==================== BOT HANDLER ====================
class BotHandler:
    """مدیریت ربات تلگرام"""
    
    def __init__(self):
        self.analyzer = CodeAnalyzer()
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دستور /start"""
        user = update.effective_user
        
        welcome_text = f"""
👋 سلام {user.first_name}!

🤖 **ربات تحلیل‌گر قیمت ربات‌های تلگرام**

📊 **من چکار می‌کنم؟**
• کد Python ربات شما را تحلیل می‌کنم
• قابلیت‌ها را شناسایی می‌کنم
• قیمت منصفانه پیشنهاد می‌دهم

📁 **نحوه استفاده:**
۱. فایل `.py` ربات خود را ارسال کنید
۲. منتظر تحلیل بمانید (۵-۱۰ ثانیه)
۳. گزارش کامل را دریافت کنید

💰 **فرمول قیمت:**
• قیمت پایه: ۲,۰۰۰,۰۰۰ ریال
• ضریب کیفیت: ۰.۵ تا ۲ برابر
• نرخ دلار: ۵۰,۰۰۰ ریال

👇 **فایل ربات خود را همین حالا ارسال کنید!**
        """
        
        keyboard = [
            [InlineKeyboardButton("📋 نمونه گزارش", callback_data="sample")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش فایل ارسالی"""
        if not update.message or not update.message.document:
            await update.message.reply_text("⚠️ لطفا یک فایل ارسال کنید.")
            return
        
        doc = update.message.document
        file_name = doc.file_name or "unknown.py"
        
        if not file_name.endswith('.py'):
            await update.message.reply_text("❌ فقط فایل‌های Python با پسوند `.py` قابل تحلیل هستند.")
            return
        
        # پیام وضعیت
        status_msg = await update.message.reply_text("📥 در حال دریافت فایل...")
        
        try:
            # دانلود فایل
            file = await doc.get_file()
            file_content_bytes = await file.download_as_bytearray()
            
            # بررسی حجم
            if len(file_content_bytes) > 1024 * 1024:  # 1MB
                await status_msg.edit_text("❌ فایل بسیار بزرگ است! (حداکثر 1MB)")
                return
            
            file_content = file_content_bytes.decode('utf-8', errors='ignore')
            
            await status_msg.edit_text("🔍 در حال تحلیل کد...")
            
            # تحلیل کد
            analysis = self.analyzer.analyze(file_content)
            
            await status_msg.edit_text("💰 در حال محاسبه قیمت...")
            
            # محاسبه قیمت
            price_result = self.analyzer.calculate_price(analysis)
            
            # تولید گزارش
            report = self._generate_report(file_name, analysis, price_result)
            
            # ارسال گزارش
            await context.bot.delete_message(
                chat_id=status_msg.chat_id,
                message_id=status_msg.message_id
            )
            
            await update.message.reply_text(report, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            await update.message.reply_text(f"❌ خطا در پردازش: {str(e)[:100]}")
    
    def _generate_report(self, filename: str, analysis: Dict, price: Dict) -> str:
        """تولید گزارش نهایی"""
        
        # ویژگی‌ها
        features_text = ""
        if analysis["features"]:
            features_text = "✅ " + "، ".join(analysis["features"])
        else:
            features_text = "❌ ویژگی خاصی شناسایی نشد"
        
        # گزارش
        report = f"""
📄 **گزارش تحلیل ربات تلگرام**
📁 فایل: `{filename}`
⏰ زمان: {datetime.now().strftime('%Y/%m/%d %H:%M')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 **ویژگی‌های شناسایی شده:**
• دستورات: {len(analysis['commands'])} مورد
• خطوط کد: {analysis['lines_of_code']} خط
• کیبوردها: {analysis['keyboards']} عدد
• دکمه‌های اینلاین: {analysis['inline_buttons']} عدد
• ویژگی‌های فنی: {features_text}

📊 **امتیازدهی:**
🏆 امتیاز کل: **{price['score']}/100**
🎯 سطح ربات: **{price['level']}**

💰 **قیمت پیشنهادی:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• ریال: **{price['price_rials']:,} ریال**
• تومان: **{price['price_tomans']:,} تومان**
• دلار: **{price['price_usd']:.0f} دلار**

💡 **توضیح قیمت:**
قیمت بر اساس کیفیت کد، قابلیت‌ها و پیچیدگی ربات محاسبه شده است.

📝 **نکات:**
• این قیمت بر اساس تحلیل خودکار است
• قیمت‌های بازار ممکن است متفاوت باشند
• برای سفارش توسعه: @username

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 @BotPriceAnalyzer
        """
        
        return report
    
    async def sample_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمونه گزارش"""
        query = update.callback_query
        await query.answer()
        
        sample = f"""
📋 **نمونه گزارش تحلیل:**

🤖 **ربات: فروشگاه آنلاین**
📊 **ویژگی‌ها:**
• ۸ دستور مختلف
• ۵ کیبورد اینلاین
• دیتابیس SQLite
• درگاه پرداخت
• پنل ادمین

🎯 **امتیاز: ۷۸/۱۰۰**
💰 **قیمت: ۳,۵۰۰,۰۰۰ ریال**

👇 **برای تحلیل ربات خود:**
فایل Python ربات را ارسال کنید!
        """
        
        keyboard = [
            [InlineKeyboardButton("📤 ارسال فایل ربات", callback_data="send_file")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            sample,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

# ==================== MAIN APPLICATION ====================
async def main():
    """تابع اصلی اجرای ربات"""
    
    if not TOKEN:
        logger.error("❌ لطفا متغیر محیطی BOT_TOKEN را تنظیم کنید")
        logger.error("   در Render: Environment → Add Environment Variable")
        return
    
    logger.info("🤖 در حال راه‌اندازی ربات تحلیل‌گر قیمت...")
    
    # ایجاد اپلیکیشن
    app = Application.builder().token(TOKEN).build()
    
    # ایجاد هندلر
    bot_handler = BotHandler()
    
    # ثبت هندلرها
    app.add_handler(CommandHandler("start", bot_handler.start))
    app.add_handler(CommandHandler("help", bot_handler.start))
    app.add_handler(MessageHandler(filters.Document.ALL, bot_handler.handle_document))
    app.add_handler(CallbackQueryHandler(bot_handler.sample_report, pattern="^sample$"))
    app.add_handler(CallbackQueryHandler(bot_handler.start, pattern="^send_file$"))
    
    # راه‌اندازی
    if WEBHOOK_URL:
        # حالت Webhook برای Render
        logger.info(f"🌐 راه‌اندازی با Webhook: {WEBHOOK_URL}")
        
        await app.initialize()
        await app.start()
        
        # تنظیم webhook
        webhook_url = f"{WEBHOOK_URL}/{TOKEN}"
        await app.bot.set_webhook(webhook_url)
        
        logger.info(f"✅ Webhook تنظیم شد: {webhook_url}")
        logger.info("🟢 ربات فعال و آماده است!")
        
        # نگه داشتن برنامه
        await asyncio.Event().wait()
        
    else:
        # حالت Polling برای توسعه
        logger.info("🔵 راه‌اندازی در حالت Polling (توسعه)")
        
        await app.run_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 ربات متوقف شد")
    except Exception as e:
        logger.error(f"❌ خطای غیرمنتظره: {e}")
