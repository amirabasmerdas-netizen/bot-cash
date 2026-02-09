#!/usr/bin/env python3
"""
🤖 Telegram Bot Price Analyzer - Professional Output
Version: 15.0 - Professional Report Format
"""

import os
import re
import sys
import json
import time
import asyncio
import logging
import threading
from typing import Dict, List, Any, Tuple
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# ==================== LOGGING ====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
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
                "version": "15.0"
            })
            self.wfile.write(response.encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

def run_http_server():
    """اجرای HTTP Server"""
    try:
        server = HTTPServer(('0.0.0.0', PORT), HealthHandler)
        logger.info(f"✅ HTTP Server running on port {PORT}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"❌ HTTP Server error: {e}")

# ==================== PROFESSIONAL ANALYZER ====================
class ProfessionalAnalyzer:
    """تحلیل‌گر حرفه‌ای کد"""
    
    # انواع ربات‌ها با توضیحات و محدوده قیمت
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
    def analyze_code(code: str) -> Dict[str, Any]:
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
            "detected_type": ProfessionalAnalyzer._detect_bot_type(code),
            "features": ProfessionalAnalyzer._extract_features(code),
            "technical": ProfessionalAnalyzer._analyze_technical(code),
            "score": 0
        }
        
        # محاسبه امتیاز نهایی
        analysis["score"] = ProfessionalAnalyzer._calculate_score(analysis)
        
        return analysis
    
    @staticmethod
    def _detect_bot_type(code: str) -> Dict[str, Any]:
        """تشخیص نوع ربات"""
        code_lower = code.lower()
        best_match = None
        best_score = 0
        
        for bot_type in ProfessionalAnalyzer.BOT_TYPES:
            score = 0
            for keyword in bot_type["keywords"]:
                if keyword in code_lower:
                    score += 10
                    # امتیاز اضافی برای تکرار کلمات کلیدی
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
        
        # نوع پیش‌فرض
        return {
            "name": "⚙️ سفارشی",
            "description": "ربات با قابلیت‌های خاص و اختصاصی",
            "confidence": 0.3,
            "price_range": (2_000_000, 8_000_000)
        }
    
    @staticmethod
    def _extract_features(code: str) -> List[str]:
        """استخراج ویژگی‌های ربات"""
        features = []
        code_lower = code.lower()
        
        # رابط کاربری
        if 'InlineKeyboardMarkup' in code:
            features.append("کیبورد اینلاین")
        if 'InlineKeyboardButton' in code:
            features.append("دکمه‌های اینلاین")
        if 'ReplyKeyboardMarkup' in code:
            features.append("کیبورد معمولی")
        if 'CallbackQueryHandler' in code:
            features.append("دکمه‌های تعاملی")
        
        # قابلیت‌ها
        if 'CommandHandler' in code:
            features.append("دستورات سفارشی")
        if 'ConversationHandler' in code:
            features.append("مکالمه چندمرحله‌ای")
        
        # فنی
        if 'async def' in code:
            features.append("Async Programming")
        if 'class ' in code:
            features.append("برنامه‌نویسی شی‌گرا")
        if 'try:' in code and 'except:' in code:
            features.append("مدیریت خطا")
        if 'logging' in code_lower:
            features.append("سیستم لاگ")
        
        # ادغام‌ها
        if any(db in code_lower for db in ['sqlite', 'mysql', 'postgres', 'database', 'db']):
            features.append("دیتابیس")
        if any(pay in code_lower for pay in ['zarinpal', 'idpay', 'nextpay', 'payment', 'پرداخت']):
            features.append("درگاه پرداخت")
        if 'requests' in code_lower or 'httpx' in code_lower or 'aiohttp' in code_lower:
            features.append("API خارجی")
        
        # زمان‌بندی
        if 'JobQueue' in code or 'run_repeating' in code or 'run_once' in code:
            features.append("زمان‌بندی خودکار")
        
        return list(set(features))  # حذف موارد تکراری
    
    @staticmethod
    def _analyze_technical(code: str) -> Dict[str, Any]:
        """تحلیل فنی کد"""
        # ساختار کد
        class_count = len(re.findall(r'class\s+\w+', code))
        function_count = len(re.findall(r'(async\s+)?def\s+\w+', code))
        
        # imports
        imports = re.findall(r'from\s+(\S+)\s+import|import\s+(\S+)', code)
        
        # کیفیت
        has_error_handling = len(re.findall(r'try:', code)) > 0
        has_logging = 'logging' in code.lower()
        
        return {
            "class_count": class_count,
            "function_count": function_count,
            "import_count": len(imports),
            "has_error_handling": has_error_handling,
            "has_logging": has_logging
        }
    
    @staticmethod
    def _calculate_score(analysis: Dict[str, Any]) -> int:
        """محاسبه امتیاز (0-100)"""
        score = 0
        
        # 1. اندازه پروژه (تا 25 امتیاز)
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
        
        # 2. نوع ربات (تا 15 امتیاز)
        confidence = analysis["detected_type"]["confidence"]
        score += int(confidence * 15)
        
        # 3. ویژگی‌ها (تا 30 امتیاز)
        feature_count = len(analysis["features"])
        score += min(feature_count * 3, 30)
        
        # 4. کیفیت کد (تا 20 امتیاز)
        tech = analysis["technical"]
        if tech["has_error_handling"]:
            score += 5
        if tech["has_logging"]:
            score += 5
        if analysis["file_info"]["comment_ratio"] > 0.1:
            score += 5
        elif analysis["file_info"]["comment_ratio"] > 0.05:
            score += 3
        
        # 5. ساختار (تا 10 امتیاز)
        if tech["class_count"] > 0:
            score += min(tech["class_count"] * 2, 5)
        if tech["function_count"] > 10:
            score += 5
        elif tech["function_count"] > 5:
            score += 3
        
        return min(score, 100)

# ==================== PRICE CALCULATOR ====================
class ProfessionalPriceCalculator:
    """ماشین حساب قیمت حرفه‌ای"""
    
    @staticmethod
    def calculate_price(analysis: Dict[str, Any]) -> Dict[str, Any]:
        """محاسبه قیمت نهایی"""
        score = analysis["score"]
        bot_type = analysis["detected_type"]
        
        # قیمت پایه از محدوده نوع
        type_min, type_max = bot_type["price_range"]
        type_base = (type_min + type_max) // 2
        
        # ضریب امتیاز (0.5 تا 2)
        score_factor = 0.5 + (score / 100) * 1.5
        
        # ضریب پیچیدگی
        tech_factor = 1.0
        tech = analysis["technical"]
        if tech["has_error_handling"]:
            tech_factor += 0.1
        if tech["has_logging"]:
            tech_factor += 0.1
        if len(analysis["features"]) > 5:
            tech_factor += 0.1
        
        # ضریب اندازه
        loc = analysis["file_info"]["code_lines"]
        size_factor = 1.0
        if loc > 500:
            size_factor = 1.3
        elif loc > 300:
            size_factor = 1.2
        elif loc > 200:
            size_factor = 1.1
        
        # محاسبه قیمت
        raw_price = type_base * score_factor * tech_factor * size_factor
        
        # محدودیت‌ها
        min_price = 500_000
        max_price = 15_000_000
        price_rials = max(min_price, min(int(raw_price), max_price))
        
        # تبدیل ارز
        dollar_rate = 50_000  # نرخ دلار
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
            "type_name": bot_type["name"],
            "confidence": bot_type["confidence"],
            "price_range": bot_type["price_range"]
        }

# ==================== REPORT GENERATOR ====================
class ReportGenerator:
    """تولید کننده گزارش حرفه‌ای"""
    
    @staticmethod
    def generate_report(filename: str, analysis: Dict[str, Any], price: Dict[str, Any]) -> str:
        """تولید گزارش با فرمت دلخواه"""
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
🎯 نوع: {price['type_name'].split()[-1]}  # فقط نام بدون emoji

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
🤖 ربات تحلیل‌گر قیمت - نسخه ۱۵.۰
        """
        
        return report

# ==================== BOT HANDLERS ====================
class ProfessionalBot:
    """ربات حرفه‌ای"""
    
    def __init__(self):
        self.analyzer = ProfessionalAnalyzer()
        self.calculator = ProfessionalPriceCalculator()
        self.report_gen = ReportGenerator()
        self.processing_users = set()
        self.last_activity = time.time()
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دستور /start"""
        self.last_activity = time.time()
        
        text = """
🤖 **ربات تحلیل‌گر حرفه‌ای قیمت ربات تلگرام**

✨ **ویژگی‌های جدید:**
• تحلیل کامل کد با دقت بالا
• تشخیص هوشمند نوع ربات
• گزارش حرفه‌ای با فرمت زیبا
• قیمت‌گذاری منصفانه و شفاف

📊 **نحوه استفاده:**
۱. فایل `.py` ربات خود را ارسال کنید
۲. منتظر تحلیل پیشرفته باشید (۱۰-۲۰ ثانیه)
۳. گزارش کامل حرفه‌ای را دریافت کنید

🎯 **آنالیز می‌شود:**
• نوع و کاربرد ربات
• ویژگی‌های شناسایی شده
• کیفیت کد و ساختار فنی
• قیمت دقیق و منصفانه

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
        self.last_activity = time.time()
        
        if user_id in self.processing_users:
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
        
        self.processing_users.add(user_id)
        
        try:
            # پیام وضعیت
            status_msg = await update.message.reply_text("📥 در حال دریافت فایل...")
            
            # دانلود فایل
            file = await doc.get_file()
            content_bytes = await file.download_as_bytearray()
            
            if len(content_bytes) > 3 * 1024 * 1024:  # 3MB
                await status_msg.edit_text("❌ فایل بسیار بزرگ است! (حداکثر 3MB)")
                return
            
            content = content_bytes.decode('utf-8', errors='ignore')
            
            await status_msg.edit_text("🔍 تحلیل نوع ربات و ویژگی‌ها...")
            
            # تحلیل کامل
            analysis = self.analyzer.analyze_code(content)
            
            await status_msg.edit_text("💰 محاسبه قیمت...")
            
            # محاسبه قیمت
            price_result = self.calculator.calculate_price(analysis)
            
            # تولید گزارش
            report = self.report_gen.generate_report(file_name, analysis, price_result)
            
            # حذف پیام وضعیت
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=status_msg.message_id
            )
            
            # ارسال گزارش
            await update.message.reply_text(report, parse_mode='Markdown')
            logger.info(f"✅ Report sent for {file_name}")
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            await update.message.reply_text("❌ خطا در پردازش فایل. لطفا دوباره تلاش کنید.")
        
        finally:
            self.processing_users.discard(user_id)
    
    async def sample_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمونه گزارش"""
        query = update.callback_query
        await query.answer()
        
        sample = f"""
📄 **نمونه گزارش تحلیل:**

🎯 **تشخیص:** 👑 مدیریت گروه (۸۵٪ اطمینان)
✨ **ویژگی‌ها:**
• ✅ کیبورد اینلاین
• ✅ دکمه‌های تعاملی  
• ✅ مدیریت خطا
• ✅ دیتابیس SQLite
• ✅ زمان‌بندی خودکار

💰 **قیمت:** ۳,۸۰۰,۰۰۰ ریال

👇 **برای تحلیل ربات خود:**
فایل Python ربات را ارسال کنید!
        """
        
        keyboard = [
            [InlineKeyboardButton("📤 ارسال فایل ربات", callback_data="send")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(sample, reply_markup=reply_markup, parse_mode='Markdown')

# ==================== KEEP ALIVE ====================
def activity_monitor(bot: ProfessionalBot):
    """مانیتور فعالیت برای جلوگیری از sleep"""
    while True:
        time_since_activity = time.time() - bot.last_activity
        
        if time_since_activity > 300:  # 5 دقیقه بی‌فعالی
            logger.info("🔄 Activity monitor: No activity for 5+ minutes")
            bot.last_activity = time.time()  # Reset
        
        time.sleep(60)  # هر 1 دقیقه چک کن

# ==================== MAIN ====================
def main():
    """تابع اصلی"""
    logger.info("=" * 60)
    logger.info("🤖 Telegram Bot Price Analyzer - Professional v15.0")
    logger.info("=" * 60)
    
    # شروع HTTP Server
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    logger.info(f"✅ HTTP Server started on port {PORT}")
    
    try:
        # ایجاد اپلیکیشن تلگرام
        application = Application.builder().token(TOKEN).build()
        
        # ایجاد هندلر
        bot = ProfessionalBot()
        
        # ثبت هندلرها
        application.add_handler(CommandHandler("start", bot.start))
        application.add_handler(CommandHandler("help", bot.start))
        application.add_handler(MessageHandler(filters.Document.ALL, bot.handle_document))
        application.add_handler(CallbackQueryHandler(bot.sample_report, pattern="^sample$"))
        application.add_handler(CallbackQueryHandler(bot.start, pattern="^send$"))
        
        logger.info("✅ Bot setup completed")
        
        # شروع activity monitor
        monitor_thread = threading.Thread(target=activity_monitor, args=(bot,), daemon=True)
        monitor_thread.start()
        logger.info("✅ Activity monitor started")
        
        # پاکسازی قبل از شروع
        async def cleanup():
            from telegram import Bot
            temp_bot = Bot(token=TOKEN)
            await temp_bot.delete_webhook(drop_pending_updates=True)
            await asyncio.sleep(2)
        
        asyncio.run(cleanup())
        
        # شروع polling
        logger.info("🚀 Starting bot polling...")
        application.run_polling(
            drop_pending_updates=True,
            timeout=30,
            poll_interval=0.5,
            allowed_updates=["message", "callback_query"]
        )
        
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
