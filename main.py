#!/usr/bin/env python3
"""
🤖 Telegram Bot Price Analyzer - Professional Version
Version: 16.0 - Fixed Event Loop
"""

import os
import re
import sys
import json
import time
import asyncio
import logging
import threading
from typing import Dict, List, Any
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# ==================== LOGGING ====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ==================== CONFIG ====================
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
    logger.error(f"❌ Import error: {e}")
    sys.exit(1)

# ==================== HTTP SERVER ====================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ['/', '/health', '/ping']:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = json.dumps({
                "status": "online",
                "service": "bot-price-analyzer",
                "version": "16.0",
                "time": datetime.now().strftime("%H:%M:%S")
            })
            self.wfile.write(response.encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Disable HTTP logs

def run_http_server():
    """اجرای HTTP Server در thread جداگانه"""
    try:
        server = HTTPServer(('0.0.0.0', PORT), HealthHandler)
        logger.info(f"✅ HTTP Server running on port {PORT}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"❌ HTTP Server error: {e}")

# ==================== PROFESSIONAL ANALYZER ====================
class ProfessionalAnalyzer:
    """تحلیل‌گر حرفه‌ای"""
    
    BOT_TYPES = [
        {
            "name": "👑 مدیریت گروه",
            "description": "ربات مدیریت و ادمین گروه‌های تلگرام",
            "keywords": ["group", "admin", "مدیریت", "گروه", "kick", "ban", "filter", "welcome"],
            "price_range": (1_500_000, 4_000_000)
        },
        {
            "name": "🛍️ فروشگاه آنلاین", 
            "description": "ربات فروش محصولات و خدمات با درگاه پرداخت",
            "keywords": ["shop", "store", "فروش", "خرید", "محصول", "سبد خرید", "payment"],
            "price_range": (3_000_000, 10_000_000)
        },
        {
            "name": "📚 آموزشی و درسی",
            "description": "ربات آموزش، آزمون و محتوای آموزشی",
            "keywords": ["course", "lesson", "آموزش", "درس", "آزمون", "سوال", "quiz"],
            "price_range": (2_500_000, 8_000_000)
        },
        {
            "name": "🎮 سرگرمی و بازی",
            "description": "ربات بازی، مسابقه و سرگرمی",
            "keywords": ["game", "play", "بازی", "سرگرمی", "مسابقه", "score", "level"],
            "price_range": (1_800_000, 5_000_000)
        },
        {
            "name": "📰 اخبار و اطلاع‌رسانی",
            "description": "ربات ارسال اخبار، اعلان‌ها و اطلاعیه‌ها",
            "keywords": ["news", "اخبار", "اطلاعیه", "اعلان", "broadcast", "پخش"],
            "price_range": (2_000_000, 6_000_000)
        },
        {
            "name": "⚙️ سرویس و ابزار",
            "description": "ربات ارائه خدمات کاربردی و ابزار",
            "keywords": ["tool", "service", "ابزار", "سرویس", "تبدیل", "دانلود", "search"],
            "price_range": (2_000_000, 7_000_000)
        }
    ]
    
    @staticmethod
    def analyze(code: str) -> Dict[str, Any]:
        """تحلیل کامل کد"""
        lines = code.split('\n')
        total_lines = len(lines)
        code_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
        comment_lines = [l for l in lines if l.strip().startswith('#')]
        
        analysis = {
            "file_info": {
                "total_lines": total_lines,
                "code_lines": len(code_lines),
                "comment_lines": len(comment_lines),
                "comment_ratio": len(comment_lines) / max(len(code_lines), 1)
            },
            "detected_type": ProfessionalAnalyzer._detect_type(code),
            "features": ProfessionalAnalyzer._extract_features(code),
            "score": 0
        }
        
        # محاسبه امتیاز
        analysis["score"] = ProfessionalAnalyzer._calculate_score(analysis)
        
        return analysis
    
    @staticmethod
    def _detect_type(code: str) -> Dict[str, Any]:
        """تشخیص نوع ربات"""
        code_lower = code.lower()
        best_match = None
        best_score = 0
        
        for bot_type in ProfessionalAnalyzer.BOT_TYPES:
            score = 0
            for keyword in bot_type["keywords"]:
                if keyword in code_lower:
                    score += 10
                    score += min(code_lower.count(keyword) * 2, 10)
            
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
        
        return {
            "name": "⚙️ سفارشی",
            "description": "ربات با قابلیت‌های خاص و اختصاصی",
            "confidence": 0.3,
            "price_range": (2_000_000, 8_000_000)
        }
    
    @staticmethod
    def _extract_features(code: str) -> List[str]:
        """استخراج ویژگی‌ها"""
        features = []
        code_lower = code.lower()
        
        # UI Features
        if 'InlineKeyboardMarkup' in code:
            features.append("کیبورد اینلاین")
        if 'InlineKeyboardButton' in code:
            features.append("دکمه‌های اینلاین")
        if 'ReplyKeyboardMarkup' in code:
            features.append("کیبورد معمولی")
        if 'CallbackQueryHandler' in code:
            features.append("دکمه‌های تعاملی")
        
        # Functionality
        if 'CommandHandler' in code:
            features.append("دستورات سفارشی")
        if 'ConversationHandler' in code:
            features.append("مکالمه چندمرحله‌ای")
        
        # Technical
        if 'async def' in code:
            features.append("Async Programming")
        if 'class ' in code:
            features.append("برنامه‌نویسی شی‌گرا")
        if 'try:' in code and 'except:' in code:
            features.append("مدیریت خطا")
        
        # Integrations
        if any(db in code_lower for db in ['sqlite', 'mysql', 'postgres', 'database']):
            features.append("دیتابیس")
        if any(pay in code_lower for pay in ['zarinpal', 'idpay', 'nextpay', 'payment', 'پرداخت']):
            features.append("درگاه پرداخت")
        
        return list(set(features))
    
    @staticmethod
    def _calculate_score(analysis: Dict[str, Any]) -> int:
        """محاسبه امتیاز"""
        score = 0
        
        # Size (up to 25)
        loc = analysis["file_info"]["code_lines"]
        if loc > 500:
            score += 25
        elif loc > 300:
            score += 20
        elif loc > 200:
            score += 15
        elif loc > 100:
            score += 10
        elif loc > 50:
            score += 5
        
        # Type confidence (up to 15)
        score += int(analysis["detected_type"]["confidence"] * 15)
        
        # Features (up to 30)
        score += min(len(analysis["features"]) * 3, 30)
        
        # Quality (up to 20)
        if analysis["file_info"]["comment_ratio"] > 0.1:
            score += 10
        elif analysis["file_info"]["comment_ratio"] > 0.05:
            score += 5
        
        # Structure (up to 10)
        if 'برنامه‌نویسی شی‌گرا' in analysis["features"]:
            score += 5
        if 'مدیریت خطا' in analysis["features"]:
            score += 5
        
        return min(score, 100)

# ==================== PRICE CALCULATOR ====================
class PriceCalculator:
    """ماشین حساب قیمت"""
    
    @staticmethod
    def calculate(analysis: Dict[str, Any]) -> Dict[str, Any]:
        """محاسبه قیمت نهایی"""
        score = analysis["score"]
        bot_type = analysis["detected_type"]
        
        # قیمت پایه
        type_min, type_max = bot_type["price_range"]
        type_base = (type_min + type_max) // 2
        
        # ضریب امتیاز
        score_factor = 0.5 + (score / 100) * 1.5
        
        # ضریب پیچیدگی
        tech_factor = 1.0
        if 'مدیریت خطا' in analysis["features"]:
            tech_factor += 0.1
        if 'دیتابیس' in analysis["features"]:
            tech_factor += 0.15
        if 'درگاه پرداخت' in analysis["features"]:
            tech_factor += 0.2
        
        # ضریب اندازه
        loc = analysis["file_info"]["code_lines"]
        size_factor = 1.0
        if loc > 500:
            size_factor = 1.3
        elif loc > 300:
            size_factor = 1.2
        elif loc > 200:
            size_factor = 1.1
        
        # محاسبه نهایی
        raw_price = type_base * score_factor * tech_factor * size_factor
        
        # محدودیت‌ها
        min_price = 500_000
        max_price = 15_000_000
        price_rials = max(min_price, min(int(raw_price), max_price))
        
        # تبدیل ارز
        dollar_rate = 50_000
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
            "type_name": bot_type["name"],
            "confidence": bot_type["confidence"],
            "price_range": bot_type["price_range"]
        }

# ==================== REPORT GENERATOR ====================
class ReportGenerator:
    """تولید گزارش"""
    
    @staticmethod
    def generate(filename: str, analysis: Dict[str, Any], price: Dict[str, Any]) -> str:
        """تولید گزارش نهایی"""
        now = datetime.now().strftime("%Y/%m/%d %H:%M")
        file_info = analysis["file_info"]
        bot_type = analysis["detected_type"]
        
        # بخش نوع ربات
        type_text = f"""
🎯 **تشخیص نوع ربات:**
• نام: {bot_type['name']}
• توضیحات: {bot_type['description']}
• اعتماد به تشخیص: {bot_type['confidence']*100:.0f}%
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
• کل خطوط: {file_info['total_lines']} خط
• خطوط کد: {file_info['code_lines']} خط
• خطوط کامنت: {file_info['comment_lines']} خط
• نسبت کامنت: {file_info['comment_ratio']*100:.1f}%
        """
        
        # بخش قیمت
        price_text = f"""
💰 **تحلیل قیمت:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏆 امتیاز کلی: **{price['score']}/100**
🎯 سطح: **{price['level']}**
🎯 نوع: {price['type_name'].split()[-1]}

💎 **قیمت نهایی:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💵 ریال: **{price['price_rials']:,} ریال**
💳 تومان: **{price['price_tomans']:,} تومان**
💲 دلار: **${price['price_usd']:,}**

📈 **محدوده قیمت برای این نوع:**
• حداقل: {price['price_range'][0]:,} ریال
• حداکثر: {price['price_range'][1]:,} ریال
        """
        
        # گزارش نهایی
        report = f"""
📄 **گزارش تحلیل حرفه‌ای ربات تلگرام**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 فایل: {filename}
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
🤖 ربات تحلیل‌گر قیمت - نسخه ۱۶.۰
        """
        
        return report

# ==================== BOT HANDLERS ====================
class BotHandler:
    """Handler اصلی ربات"""
    
    def __init__(self):
        self.analyzer = ProfessionalAnalyzer()
        self.calculator = PriceCalculator()
        self.reporter = ReportGenerator()
        self.processing = set()
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دستور /start"""
        text = """
🤖 **ربات تحلیل‌گر حرفه‌ای قیمت ربات تلگرام**

✨ **ویژگی‌ها:**
• تحلیل کامل کد Python
• تشخیص هوشمند نوع ربات
• گزارش حرفه‌ای با فرمت زیبا
• قیمت‌گذاری منصفانه و شفاف

📊 **نحوه استفاده:**
۱. فایل `.py` ربات خود را ارسال کنید
۲. منتظر تحلیل باشید (۱۰-۲۰ ثانیه)
۳. گزارش کامل را دریافت کنید

👇 **فایل ربات خود را همین حالا ارسال کنید!**
        """
        
        keyboard = [
            [InlineKeyboardButton("📋 نمونه گزارش", callback_data="sample")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش فایل"""
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
            
            # دانلود
            file = await doc.get_file()
            content_bytes = await file.download_as_bytearray()
            
            if len(content_bytes) > 3 * 1024 * 1024:  # 3MB
                await status_msg.edit_text("❌ فایل بسیار بزرگ است! (حداکثر 3MB)")
                return
            
            content = content_bytes.decode('utf-8', errors='ignore')
            
            await status_msg.edit_text("🔍 تحلیل کد...")
            
            # تحلیل
            analysis = self.analyzer.analyze(content)
            
            await status_msg.edit_text("💰 محاسبه قیمت...")
            
            # قیمت
            price_result = self.calculator.calculate(analysis)
            
            # گزارش
            report = self.reporter.generate(file_name, analysis, price_result)
            
            # حذف پیام وضعیت
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=status_msg.message_id
            )
            
            # ارسال گزارش
            await update.message.reply_text(report, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error: {e}")
            await update.message.reply_text("❌ خطا در پردازش فایل")
        
        finally:
            self.processing.discard(user_id)
    
    async def sample(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمونه گزارش"""
        query = update.callback_query
        await query.answer()
        
        text = """
📋 **نمونه گزارش:**

🎯 **تشخیص:** 👑 مدیریت گروه
✨ **ویژگی‌ها:**
• ✅ کیبورد اینلاین
• ✅ دستورات سفارشی
• ✅ مدیریت خطا
• ✅ دیتابیس

💰 **قیمت:** ۳,۸۰۰,۰۰۰ ریال

👇 **ربات خود را تحلیل کنید!**
        """
        
        keyboard = [
            [InlineKeyboardButton("📤 ارسال فایل ربات", callback_data="send")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

# ==================== MAIN ASYNC FUNCTION ====================
async def run_bot():
    """اجرای اصلی ربات"""
    logger.info("=" * 60)
    logger.info("🤖 Telegram Bot Price Analyzer - Professional v16.0")
    logger.info("=" * 60)
    
    try:
        # پاکسازی قبل از شروع
        from telegram import Bot
        temp_bot = Bot(token=TOKEN)
        await temp_bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook cleared")
        await asyncio.sleep(2)
        
        # ایجاد اپلیکیشن
        app = Application.builder().token(TOKEN).build()
        
        # ایجاد هندلر
        handler = BotHandler()
        
        # ثبت هندلرها
        app.add_handler(CommandHandler("start", handler.start))
        app.add_handler(CommandHandler("help", handler.start))
        app.add_handler(MessageHandler(filters.Document.ALL, handler.handle_document))
        app.add_handler(CallbackQueryHandler(handler.sample, pattern="^sample$"))
        app.add_handler(CallbackQueryHandler(handler.start, pattern="^send$"))
        
        logger.info("✅ Bot setup completed")
        
        # شروع polling
        await app.initialize()
        await app.start()
        await app.updater.start_polling(
            drop_pending_updates=True,
            timeout=30,
            poll_interval=0.5,
            allowed_updates=["message", "callback_query"]
        )
        
        logger.info("✅ Bot is RUNNING and ready!")
        logger.info("🎯 Waiting for files...")
        
        # نگه داشتن برنامه
        await asyncio.Event().wait()
        
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")

# ==================== MAIN FUNCTION ====================
def main():
    """تابع اصلی"""
    # شروع HTTP Server در thread جداگانه
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    logger.info(f"✅ HTTP Server started on port {PORT}")
    
    # اجرای ربات
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Main error: {e}")

if __name__ == "__main__":
    main()
