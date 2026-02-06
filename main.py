#!/usr/bin/env python3
"""
🤖 Telegram Bot Price Analyzer - Render Ready
Version: 11.0 - Stable with Polling
"""

import os
import re
import sys
import json
import asyncio
import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# ==================== LOGGING SETUP ====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ==================== CONFIGURATION ====================
TOKEN = os.environ.get("BOT_TOKEN", "")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
PORT = int(os.environ.get("PORT", 8443))

if not TOKEN:
    logger.error("❌ BOT_TOKEN is not set!")
    logger.error("On Render: Environment → Add BOT_TOKEN variable")
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

# ==================== SIMPLE HTTP SERVER FOR RENDER ====================
class HealthHandler(BaseHTTPRequestHandler):
    """HTTP Server برای Render Health Check"""
    
    def do_GET(self):
        if self.path == '/health' or self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = json.dumps({
                "status": "ok",
                "service": "telegram-bot-analyzer",
                "version": "11.0"
            })
            self.wfile.write(response.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        logger.debug(f"HTTP: {format % args}")

def run_http_server():
    """اجرای سرور HTTP ساده"""
    try:
        server = HTTPServer(('0.0.0.0', PORT), HealthHandler)
        logger.info(f"🌐 HTTP Server running on port {PORT}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"❌ HTTP Server error: {e}")

# ==================== BOT TYPE DETECTION ====================
class BotTypeDetector:
    """تشخیص نوع ربات"""
    
    BOT_TYPES = [
        {
            "name": "فروشگاه آنلاین",
            "description": "ربات فروش محصولات و خدمات با درگاه پرداخت",
            "keywords": ["shop", "store", "فروش", "محصول", "کالا", "سبد خرید", "خرید", "قیمت"],
            "price_range": (3000000, 10000000)
        },
        {
            "name": "آموزشی و درسی",
            "description": "ربات آموزش، آزمون و محتوای آموزشی",
            "keywords": ["course", "lesson", "آموزش", "درس", "آزمون", "سوال", "دانشگاه"],
            "price_range": (2500000, 8000000)
        },
        {
            "name": "مدیریت گروه",
            "description": "ربات مدیریت و ادمین گروه‌های تلگرام",
            "keywords": ["group", "admin", "مدیریت", "گروه", "عضویت", "kick", "ban"],
            "price_range": (1500000, 4000000)
        },
        {
            "name": "سرگرمی و بازی",
            "description": "ربات بازی، مسابقه و سرگرمی",
            "keywords": ["game", "play", "بازی", "سرگرمی", "مسابقه", "امتیاز", "لول"],
            "price_range": (1800000, 5000000)
        },
        {
            "name": "اخبار و اطلاع‌رسانی",
            "description": "ربات ارسال اخبار، اعلان‌ها و اطلاعیه‌ها",
            "keywords": ["news", "اخبار", "اطلاعیه", "اعلان", "خبر", "broadcast", "پخش"],
            "price_range": (2000000, 6000000)
        },
        {
            "name": "سرویس و ابزار",
            "description": "ربات ارائه خدمات کاربردی و ابزار",
            "keywords": ["tool", "service", "ابزار", "سرویس", "تبدیل", "دانلود", "جستجو"],
            "price_range": (2000000, 7000000)
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
        
        if best_match and best_score > 5:
            confidence = min(best_score / 100, 1.0)
            return {
                "name": best_match["name"],
                "description": best_match["description"],
                "confidence": confidence,
                "price_range": best_match["price_range"]
            }
        
        # اگر نوعی تشخیص داده نشد
        return {
            "name": "سفارشی (Custom)",
            "description": "ربات با قابلیت‌های خاص و اختصاصی",
            "confidence": 0.3,
            "price_range": (2000000, 8000000)
        }

# ==================== CODE ANALYZER ====================
class CodeAnalyzer:
    """تحلیل‌گر کد ربات"""
    
    @staticmethod
    def analyze(code: str) -> Dict[str, Any]:
        """تحلیل کامل کد"""
        lines = code.split('\n')
        code_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
        comment_lines = [l for l in lines if l.strip().startswith('#')]
        
        analysis = {
            "basic": {
                "total_lines": len(lines),
                "code_lines": len(code_lines),
                "comment_lines": len(comment_lines),
                "comment_ratio": len(comment_lines) / max(len(code_lines), 1)
            },
            "features": [],
            "score": 0
        }
        
        code_lower = code.lower()
        
        # تشخیص نوع ربات
        analysis["bot_type"] = BotTypeDetector.detect_type(code)
        
        # استخراج ویژگی‌ها
        features = []
        
        # رابط کاربری
        if "ReplyKeyboardMarkup" in code:
            features.append("کیبورد معمولی")
        if "InlineKeyboardMarkup" in code:
            features.append("کیبورد اینلاین")
        
        # قابلیت‌ها
        if "CommandHandler" in code:
            features.append("دستورات سفارشی")
        if "CallbackQueryHandler" in code:
            features.append("دکمه‌های تعاملی")
        if "ConversationHandler" in code:
            features.append("مکالمه چندمرحله‌ای")
        
        # فنی
        if "async def" in code:
            features.append("Async Programming")
        if "try:" in code and "except:" in code:
            features.append("مدیریت خطا")
        if "logging" in code_lower:
            features.append("سیستم لاگ")
        
        # ادغام‌ها
        if any(x in code_lower for x in ["sqlite", "mysql", "postgres"]):
            features.append("دیتابیس")
        if any(x in code_lower for x in ["zarinpal", "idpay", "nextpay", "payment"]):
            features.append("درگاه پرداخت")
        if "requests" in code_lower or "httpx" in code_lower or "aiohttp" in code_lower:
            features.append("API خارجی")
        
        analysis["features"] = features
        
        # محاسبه امتیاز
        analysis["score"] = CodeAnalyzer._calculate_score(analysis, code_lower)
        
        return analysis
    
    @staticmethod
    def _calculate_score(analysis: Dict[str, Any], code_lower: str) -> int:
        """محاسبه امتیاز (0-100)"""
        score = 0
        
        # اندازه پروژه
        loc = analysis["basic"]["code_lines"]
        if loc > 500:
            score += 20
        elif loc > 200:
            score += 15
        elif loc > 100:
            score += 10
        elif loc > 50:
            score += 5
        
        # نوع ربات
        score += int(analysis["bot_type"]["confidence"] * 15)
        
        # ویژگی‌ها
        feature_count = len(analysis["features"])
        score += min(feature_count * 3, 30)
        
        # کیفیت کد
        if analysis["basic"]["comment_ratio"] > 0.1:
            score += 10
        elif analysis["basic"]["comment_ratio"] > 0.05:
            score += 5
        
        # پیچیدگی فنی
        if "class " in code_lower:
            score += 5
        if "async def" in code_lower:
            score += 5
        if "try:" in code_lower:
            score += 5
        
        return min(score, 100)

# ==================== PRICE CALCULATOR ====================
class PriceCalculator:
    """ماشین حساب قیمت"""
    
    @staticmethod
    def calculate(analysis: Dict[str, Any]) -> Dict[str, Any]:
        """محاسبه قیمت نهایی"""
        score = analysis["score"]
        bot_type = analysis["bot_type"]
        
        # قیمت پایه از محدوده نوع ربات
        type_min, type_max = bot_type["price_range"]
        type_base = (type_min + type_max) // 2
        
        # ضریب امتیاز
        score_factor = 0.5 + (score / 100) * 1.5  # 0.5 تا 2
        
        # ضریب پیچیدگی
        tech_factor = 1.0
        if "مدیریت خطا" in analysis["features"]:
            tech_factor += 0.1
        if "سیستم لاگ" in analysis["features"]:
            tech_factor += 0.1
        
        # ضریب اندازه
        loc = analysis["basic"]["code_lines"]
        size_factor = 1.0 + min(loc / 1000, 0.3)  # حداکثر 30% افزایش
        
        # محاسبه قیمت
        raw_price = type_base * score_factor * tech_factor * size_factor
        
        # محدودیت‌ها
        min_price = 500000  # 500 هزار ریال
        max_price = 15000000  # 15 میلیون ریال
        price_rials = max(min_price, min(int(raw_price), max_price))
        
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
            "confidence": bot_type["confidence"],
            "bot_type_name": bot_type["name"]
        }

# ==================== BOT HANDLERS ====================
class BotHandlers:
    """Handlerهای ربات"""
    
    def __init__(self):
        self.analyzer = CodeAnalyzer()
        self.calculator = PriceCalculator()
        self.processing = {}
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دستور /start"""
        user = update.effective_user
        
        text = f"""
👋 سلام {user.first_name if user else 'کاربر'}!

🤖 **ربات تحلیل‌گر قیمت ربات تلگرام**

✨ **ویژگی‌ها:**
• تشخیص نوع ربات (فروشگاهی، آموزشی، مدیریتی و...)
• تحلیل قابلیت‌ها و ویژگی‌ها
• محاسبه قیمت منصفانه
• گزارش کامل و شفاف

📊 **نحوه استفاده:**
۱. فایل `.py` ربات خود را ارسال کنید
۲. منتظر تحلیل باشید (۵-۱۰ ثانیه)
۳. گزارش کامل را دریافت کنید

🎯 **آنالیز می‌شود:**
• نوع و کاربرد ربات
• ویژگی‌های شناسایی شده
• کیفیت کد و ساختار
• قیمت پیشنهادی

👇 **فایل Python ربات خود را همین حالا ارسال کنید!**
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
        file_name = doc.file_name or "unknown.py"
        
        if not file_name.endswith('.py'):
            await update.message.reply_text("❌ فقط فایل‌های Python با پسوند `.py`")
            return
        
        self.processing[user_id] = True
        
        try:
            # پیام وضعیت
            status_msg = await update.message.reply_text("📥 در حال دریافت فایل...")
            
            # دانلود فایل
            file = await doc.get_file()
            file_bytes = await file.download_as_bytearray()
            
            if len(file_bytes) > 2 * 1024 * 1024:  # 2MB
                await status_msg.edit_text("❌ فایل بسیار بزرگ است! (حداکثر 2MB)")
                return
            
            content = file_bytes.decode('utf-8', errors='ignore')
            
            await status_msg.edit_text("🔍 تحلیل کد...")
            analysis = self.analyzer.analyze(content)
            
            await status_msg.edit_text("💰 محاسبه قیمت...")
            price_result = self.calculator.calculate(analysis)
            
            # گزارش
            report = self._create_report(file_name, analysis, price_result)
            
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=status_msg.message_id
            )
            
            await update.message.reply_text(report, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            await update.message.reply_text("❌ خطا در پردازش فایل. لطفا دوباره تلاش کنید.")
        
        finally:
            self.processing.pop(user_id, None)
    
    def _create_report(self, filename: str, analysis: Dict, price: Dict) -> str:
        """ایجاد گزارش"""
        now = datetime.now().strftime('%Y/%m/%d %H:%M')
        basic = analysis["basic"]
        bot_type = analysis["bot_type"]
        features = analysis["features"]
        
        # بخش نوع ربات
        type_text = f"""
🎯 **تشخیص نوع ربات:**
• **نام:** {bot_type['name']}
• **توضیحات:** {bot_type['description']}
• **اعتماد به تشخیص:** {bot_type['confidence']*100:.0f}%
"""
        
        # بخش ویژگی‌ها
        features_text = "✨ **ویژگی‌های شناسایی شده:**\n"
        if features:
            for feature in features[:10]:  # حداکثر ۱۰ ویژگی
                features_text += f"• ✅ {feature}\n"
            if len(features) > 10:
                features_text += f"• ... و {len(features)-10} مورد دیگر\n"
        else:
            features_text += "• ❌ ویژگی خاصی شناسایی نشد\n"
        
        # بخش فنی
        tech_text = f"""
⚙️ **تحلیل فنی:**
• کل خطوط: {basic['total_lines']} خط
• خطوط کد: {basic['code_lines']} خط
• خطوط کامنت: {basic['comment_lines']} خط
• نسبت کامنت: {basic['comment_ratio']*100:.1f}%
"""
        
        # بخش قیمت
        price_text = f"""
💰 **تحلیل قیمت:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏆 امتیاز کلی: **{price['score']}/100**
🎯 سطح: **{price['level']}**
🎯 نوع: **{price['bot_type_name']}**

💎 **قیمت نهایی:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💵 ریال: **{price['price_rials']:,} ریال**
💳 تومان: **{price['price_tomans']:,} تومان**
💲 دلار: **${price['price_usd']:,}**

📈 **محدوده قیمت برای این نوع:**
• حداقل: {bot_type['price_range'][0]:,} ریال
• حداکثر: {bot_type['price_range'][1]:,} ریال
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
    
    async def sample(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمونه گزارش"""
        query = update.callback_query
        await query.answer()
        
        text = """
📋 **نمونه گزارش تحلیل:**

🎯 **تشخیص:** فروشگاه آنلاین (۸۵٪ اطمینان)
✨ **ویژگی‌ها:**
• ✅ کیبورد اینلاین
• ✅ دستورات سفارشی  
• ✅ دیتابیس SQLite
• ✅ درگاه پرداخت زرین‌پال
• ✅ مدیریت خطا

⚙️ **تحلیل فنی:**
• ۲۵۰ خط کد
• ۲۰٪ کامنت
• کیفیت کد: خوب

💰 **قیمت:**
• ریال: ۴,۲۰۰,۰۰۰ ریال
• تومان: ۴۲۰,۰۰۰ تومان
• دلار: ۸۴ دلار

👇 **ربات خود را تحلیل کنید!**
        """
        
        keyboard = [
            [InlineKeyboardButton("📤 ارسال فایل", callback_data="send")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def send_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """ارسال فایل"""
        query = update.callback_query
        await query.answer()
        await self.start(update, context)

# ==================== MAIN APPLICATION ====================
def main():
    """برنامه اصلی - سازگار با Render"""
    logger.info("=" * 60)
    logger.info("🤖 Telegram Bot Price Analyzer - Version 11.0")
    logger.info("=" * 60)
    logger.info(f"🔑 BOT_TOKEN: {'✅' if TOKEN else '❌'}")
    logger.info(f"🌐 WEBHOOK_URL: {WEBHOOK_URL or 'Not set'}")
    logger.info(f"🚪 PORT: {PORT}")
    
    # شروع HTTP Server در background thread
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    logger.info(f"🌐 HTTP Server started on port {PORT}")
    
    try:
        # ایجاد اپلیکیشن تلگرام
        application = Application.builder().token(TOKEN).build()
        
        # ایجاد هندلر
        handlers = BotHandlers()
        
        # ثبت هندلرها
        application.add_handler(CommandHandler("start", handlers.start))
        application.add_handler(CommandHandler("help", handlers.start))
        application.add_handler(MessageHandler(filters.Document.ALL, handlers.handle_document))
        application.add_handler(CallbackQueryHandler(handlers.sample, pattern="^sample$"))
        application.add_handler(CallbackQueryHandler(handlers.send_file, pattern="^send$"))
        
        logger.info("✅ تنظیمات ربات کامل شد")
        
        # راه‌اندازی polling
        logger.info("🔄 شروع Polling...")
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
        
    except KeyboardInterrupt:
        logger.info("👋 دریافت سیگنال توقف")
    except Exception as e:
        logger.error(f"❌ خطا: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        logger.info("✅ برنامه به پایان رسید")

if __name__ == "__main__":
    # اجرای برنامه
    main()
