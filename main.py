#!/usr/bin/env python3
"""
🤖 Telegram Bot Price Analyzer - Professional Version
"""

import os
import re
import sys
import json
import time
import asyncio
import logging
import threading
from typing import Dict, Any, List, Tuple
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
                "version": "1.0",
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

# ==================== BOT TYPE DETECTION ====================
class BotTypeDetector:
    """تشخیص نوع ربات"""
    
    BOT_TYPES = [
        {
            "name": "سرگرمی و بازی",
            "description": "ربات بازی، مسابقه و سرگرمی",
            "keywords": ["game", "play", "بازی", "سرگرمی", "مسابقه", "امتیاز", "لول", "جایزه"],
            "price_range": (1800000, 5000000),
            "emoji": "🎮"
        },
        {
            "name": "فروشگاه آنلاین",
            "description": "ربات فروش محصولات و خدمات با درگاه پرداخت",
            "keywords": ["shop", "store", "فروش", "محصول", "کالا", "سبد خرید", "خرید", "قیمت"],
            "price_range": (3000000, 10000000),
            "emoji": "🛍️"
        },
        {
            "name": "آموزشی و درسی",
            "description": "ربات آموزش، آزمون و محتوای آموزشی",
            "keywords": ["course", "lesson", "آموزش", "درس", "آزمون", "سوال", "دانشگاه"],
            "price_range": (2500000, 8000000),
            "emoji": "📚"
        },
        {
            "name": "مدیریت گروه",
            "description": "ربات مدیریت و ادمین گروه‌های تلگرام",
            "keywords": ["group", "admin", "مدیریت", "گروه", "عضویت", "kick", "ban", "welcome"],
            "price_range": (1500000, 4000000),
            "emoji": "👑"
        },
        {
            "name": "اخبار و اطلاع‌رسانی",
            "description": "ربات ارسال اخبار، اعلان‌ها و اطلاعیه‌ها",
            "keywords": ["news", "اخبار", "اطلاعیه", "اعلان", "خبر", "broadcast", "پخش"],
            "price_range": (2000000, 6000000),
            "emoji": "📰"
        },
        {
            "name": "سرویس و ابزار",
            "description": "ربات ارائه خدمات کاربردی و ابزار",
            "keywords": ["tool", "service", "ابزار", "سرویس", "تبدیل", "دانلود", "جستجو"],
            "price_range": (2000000, 7000000),
            "emoji": "🔧"
        },
        {
            "name": "پشتیبانی و چت",
            "description": "ربات پشتیبانی، پاسخگویی و چت هوشمند",
            "keywords": ["support", "help", "پشتیبانی", "چت", "سوال", "پاسخ", "ticket"],
            "price_range": (2500000, 7500000),
            "emoji": "💬"
        },
        {
            "name": "مالی و حسابداری",
            "description": "ربات مدیریت مالی، حسابداری و تراکنش‌ها",
            "keywords": ["finance", "accounting", "مالی", "حسابداری", "تراکنش", "wallet"],
            "price_range": (3000000, 9000000),
            "emoji": "💰"
        },
        {
            "name": "سفارشی",
            "description": "ربات با قابلیت‌های خاص و اختصاصی",
            "keywords": [],
            "price_range": (2000000, 8000000),
            "emoji": "⚡"
        }
    ]
    
    @staticmethod
    def detect_type(code: str) -> Dict[str, Any]:
        """تشخیص نوع ربات"""
        code_lower = code.lower()
        
        best_match = None
        best_score = 0
        
        for bot_type in BotTypeDetector.BOT_TYPES:
            score = 0
            for keyword in bot_type["keywords"]:
                if keyword in code_lower:
                    score += 10 + min(code_lower.count(keyword) * 2, 10)
            
            if score > best_score:
                best_score = score
                best_match = bot_type
        
        if best_match and best_score > 0:
            confidence = min(best_score / 100, 1.0)
            return {
                "name": f"{best_match['emoji']} {best_match['name']}",
                "description": best_match["description"],
                "confidence": confidence,
                "price_range": best_match["price_range"]
            }
        
        # اگر نوعی تشخیص داده نشد
        return {
            "name": "⚡ سفارشی",
            "description": "ربات با قابلیت‌های خاص و اختصاصی",
            "confidence": 0.3,
            "price_range": (2000000, 8000000)
        }

# ==================== ADVANCED CODE ANALYZER ====================
class AdvancedBotAnalyzer:
    """تحلیل‌گر پیشرفته کد"""
    
    @staticmethod
    def analyze(code: str) -> Dict[str, Any]:
        """تحلیل کامل کد"""
        lines = code.split('\n')
        code_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
        comment_lines = [l for l in lines if l.strip().startswith('#')]
        
        analysis = {
            "total_lines": len(lines),
            "code_lines": len(code_lines),
            "comment_lines": len(comment_lines),
            "features": [],
            "score": 0
        }
        
        # محاسبه نسبت کامنت
        if analysis["code_lines"] > 0:
            analysis["comment_ratio"] = analysis["comment_lines"] / analysis["code_lines"]
        else:
            analysis["comment_ratio"] = 0
        
        code_lower = code.lower()
        
        # تشخیص نوع ربات
        analysis["bot_type"] = BotTypeDetector.detect_type(code)
        
        # استخراج ویژگی‌ها
        features = []
        
        # رابط کاربری
        if "InlineKeyboardMarkup" in code:
            features.append("کیبورد اینلاین")
        if "InlineKeyboardButton" in code:
            features.append("دکمه‌های تعاملی")
        if "ReplyKeyboardMarkup" in code:
            features.append("کیبورد معمولی")
        
        # قابلیت‌ها
        if "CommandHandler" in code:
            features.append("دستورات سفارشی")
        if "CallbackQueryHandler" in code:
            features.append("دکمه‌های اینلاین")
        if "ConversationHandler" in code:
            features.append("مکالمه چندمرحله‌ای")
        
        # فنی
        if "async def" in code:
            features.append("Async Programming")
        if "asyncio" in code_lower:
            features.append("مدیریت همزمانی")
        if 'try:' in code and 'except:' in code:
            features.append("مدیریت خطا")
        if "logging" in code_lower:
            features.append("سیستم لاگ‌گیری")
        if "class " in code:
            features.append("برنامه‌نویسی شی‌گرا")
        
        # ادغام‌ها
        if any(x in code_lower for x in ["sqlite", "mysql", "postgres", "database"]):
            features.append("دیتابیس")
        if any(x in code_lower for x in ["zarinpal", "idpay", "nextpay", "payment", "پرداخت"]):
            features.append("درگاه پرداخت")
        if "requests" in code_lower or "httpx" in code_lower or "aiohttp" in code_lower:
            features.append("API خارجی")
        
        analysis["features"] = features
        
        # محاسبه امتیاز
        analysis["score"] = AdvancedBotAnalyzer._calculate_score(analysis, code_lower)
        
        return analysis
    
    @staticmethod
    def _calculate_score(analysis: Dict[str, Any], code_lower: str) -> int:
        """محاسبه امتیاز (0-100)"""
        score = 0
        
        # اندازه پروژه (تا 20 امتیاز)
        loc = analysis["code_lines"]
        if loc > 500:
            score += 20
        elif loc > 300:
            score += 16
        elif loc > 200:
            score += 12
        elif loc > 100:
            score += 8
        elif loc > 50:
            score += 4
        
        # نوع ربات (تا 15 امتیاز)
        confidence = analysis["bot_type"]["confidence"]
        score += int(confidence * 15)
        
        # ویژگی‌ها (تا 35 امتیاز)
        feature_count = len(analysis["features"])
        score += min(feature_count * 3, 35)
        
        # کیفیت کد (تا 20 امتیاز)
        if analysis["comment_ratio"] > 0.15:
            score += 15
        elif analysis["comment_ratio"] > 0.10:
            score += 10
        elif analysis["comment_ratio"] > 0.05:
            score += 5
        
        # پیچیدگی فنی (تا 10 امتیاز)
        if "async def" in code_lower:
            score += 3
        if "class " in code_lower:
            score += 3
        if 'try:' in code_lower:
            score += 2
        if "logging" in code_lower:
            score += 2
        
        return min(score, 100)

# ==================== PRICE CALCULATOR ====================
class ProfessionalPriceCalculator:
    """ماشین حساب قیمت حرفه‌ای"""
    
    @staticmethod
    def calculate(analysis: Dict[str, Any]) -> Dict[str, Any]:
        """محاسبه قیمت نهایی"""
        score = analysis["score"]
        bot_type = analysis["bot_type"]
        
        # قیمت پایه از محدوده نوع ربات
        type_min, type_max = bot_type["price_range"]
        type_base = (type_min + type_max) // 2
        
        # ضریب امتیاز (0.5 تا 2)
        score_factor = 0.5 + (score / 100) * 1.5
        
        # ضریب پیچیدگی فنی
        tech_factor = 1.0
        features = analysis["features"]
        
        if "مدیریت خطا" in features:
            tech_factor += 0.1
        if "سیستم لاگ‌گیری" in features:
            tech_factor += 0.1
        if "Async Programming" in features:
            tech_factor += 0.15
        if "دیتابیس" in features:
            tech_factor += 0.2
        if "درگاه پرداخت" in features:
            tech_factor += 0.25
        
        # ضریب اندازه پروژه
        loc = analysis["code_lines"]
        size_factor = 1.0
        if loc > 500:
            size_factor = 1.3
        elif loc > 300:
            size_factor = 1.2
        elif loc > 200:
            size_factor = 1.1
        elif loc > 100:
            size_factor = 1.05
        
        # محاسبه قیمت
        raw_price = type_base * score_factor * tech_factor * size_factor
        
        # محدودیت‌ها
        min_price = 500000    # 500 هزار ریال
        max_price = 15000000  # 15 میلیون ریال
        price_rials = max(min_price, min(int(raw_price), max_price))
        
        # تبدیل ارز
        dollar_rate = 50000   # نرخ دلار
        price_tomans = price_rials // 10
        price_usd = price_rials / dollar_rate
        
        # سطح ربات
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
            "confidence": round(bot_type["confidence"] * 100),
            "bot_type_name": bot_type["name"].split(" ", 1)[-1],  # حذف emoji
            "type_min": type_min,
            "type_max": type_max,
            "raw_calculation": int(raw_price)
        }

# ==================== BOT HANDLERS ====================
class ProfessionalBotHandlers:
    """Handlerهای حرفه‌ای ربات"""
    
    def __init__(self):
        self.analyzer = AdvancedBotAnalyzer()
        self.calculator = ProfessionalPriceCalculator()
        self.processing = set()
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دستور /start"""
        user = update.effective_user
        # حذف فاصله بین حروف نام کاربر
        user_name = user.first_name if user else "کاربر"
        formatted_name = " ".join(list(user_name)) if user_name else "کاربر"
        
        text = f"""
👋 سلام **{formatted_name}**!

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
        
        await update.message.reply_text(text, parse_mode='Markdown')
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش فایل ارسالی"""
        user_id = update.effective_user.id
        
        if user_id in self.processing:
            await update.message.reply_text("⏳ در حال پردازش درخواست قبلی...")
            return
        
        if not update.message.document:
            await update.message.reply_text("⚠️ لطفا یک فایل ارسال کنید.")
            return
        
        doc = update.message.document
        file_name = doc.file_name or "unknown.py"
        
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
            if len(content_bytes) > 3 * 1024 * 1024:  # 3MB
                await status_msg.edit_text("❌ فایل بسیار بزرگ است! (حداکثر 3MB)")
                return
            
            content = content_bytes.decode('utf-8', errors='ignore')
            
            await status_msg.edit_text("🔍 تشخیص نوع ربات...")
            analysis = self.analyzer.analyze(content)
            
            await status_msg.edit_text("💰 محاسبه قیمت...")
            price_result = self.calculator.calculate(analysis)
            
            # گزارش
            report = self._create_professional_report(file_name, analysis, price_result)
            
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
    
    def _create_professional_report(self, filename: str, analysis: Dict, price: Dict) -> str:
        """ایجاد گزارش حرفه‌ای"""
        now = datetime.now().strftime('%Y/%m/%d %H:%M')
        bot_type = analysis["bot_type"]
        
        # بخش تشخیص نوع ربات
        type_text = f"""
🎯 **تشخیص نوع ربات:**
• نام: {bot_type['name']}
• توضیحات: {bot_type['description']}
• اعتماد به تشخیص: {price['confidence']}%
        """
        
        # بخش ویژگی‌ها
        features = analysis["features"]
        features_text = "✨ **ویژگی‌های شناسایی شده:**\n"
        if features:
            for feature in features:
                features_text += f"• ✅ {feature}\n"
        else:
            features_text += "• ❌ ویژگی خاصی شناسایی نشد\n"
        
        # بخش تحلیل فنی
        tech_text = f"""
⚙️ **تحلیل فنی:**
• کل خطوط: {analysis['total_lines']} خط
• خطوط کد: {analysis['code_lines']} خط
• خطوط کامنت: {analysis['comment_lines']} خط
• نسبت کامنت: {analysis['comment_ratio']*100:.1f}%
        """
        
        # بخش قیمت
        price_text = f"""
💰 **تحلیل قیمت:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏆 امتیاز کلی: **{price['score']}/100**
🎯 سطح: **{price['level']}**
🎯 نوع: {price['bot_type_name']}

💎 **قیمت نهایی:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💵 ریال: **{price['price_rials']:,} ریال**
💳 تومان: **{price['price_tomans']:,} تومان**
💲 دلار: **${price['price_usd']:,}**

📈 **محدوده قیمت برای این نوع:**
• حداقل: {price['type_min']:,} ریال
• حداکثر: {price['type_max']:,} ریال
        """
        
        # گزارش نهایی
        report = f"""
📄 **گزارش تحلیل حرفه‌ای ربات تلگرام**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 فایل: `{filename}`
⏰ زمان تحلیل: {now}

{type_text}

{features_text}

{tech_text}

{price_text}

💡 **نکات مهم:**
• این تحلیل بر اساس کد فعلی ربات است
• قیمت بر اساس کیفیت و قابلیت‌ها محاسبه شده
• برای سفارش توسعه با @username تماس بگیرید

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 ربات تحلیل‌گر قیمت - نسخه ۱۱.۰
        """
        
        return report

# ==================== MAIN APPLICATION ====================
async def setup_bot():
    """تنظیم ربات"""
    logger.info("🤖 راه‌اندازی ربات تحلیل‌گر حرفه‌ای...")
    
    # ایجاد اپلیکیشن
    application = Application.builder().token(TOKEN).build()
    
    # ایجاد هندلرها
    handlers = ProfessionalBotHandlers()
    
    # ثبت هندلرها
    application.add_handler(CommandHandler("start", handlers.start))
    application.add_handler(CommandHandler("help", handlers.start))
    application.add_handler(MessageHandler(filters.Document.ALL, handlers.handle_document))
    
    logger.info("✅ تنظیمات ربات کامل شد")
    return application

async def run_bot():
    """اجرای ربات"""
    try:
        # پاکسازی قبل از شروع
        try:
            from telegram import Bot
            bot = Bot(token=TOKEN)
            await bot.delete_webhook(drop_pending_updates=True)
            logger.info("✅ Webhook قبلی حذف شد")
            await asyncio.sleep(2)
        except:
            pass
        
        # تنظیم ربات
        app = await setup_bot()
        
        # شروع polling
        await app.initialize()
        await app.start()
        await app.updater.start_polling(
            drop_pending_updates=True,
            timeout=30,
            poll_interval=1.0,
            allowed_updates=["message", "callback_query"]
        )
        
        logger.info("✅ ربات فعال و آماده است!")
        
        # نگه داشتن برنامه
        await asyncio.Event().wait()
        
    except KeyboardInterrupt:
        logger.info("👋 دریافت سیگنال توقف")
    except Exception as e:
        logger.error(f"❌ خطا در اجرای ربات: {e}")

def main():
    """برنامه اصلی"""
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
