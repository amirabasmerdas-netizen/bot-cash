#!/usr/bin/env python3
"""
🤖 Telegram Bot Price Analyzer - با تشخیص نوع ربات
Version: 10.0 - Bot Type Detection
"""

import os
import re
import sys
import json
import asyncio
import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime
from dataclasses import dataclass, field

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
HOST = "0.0.0.0"

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
    logger.error("Please install: pip install python-telegram-bot[job-queue]==21.7")
    sys.exit(1)

# ==================== BOT TYPE DETECTION ====================
@dataclass
class BotType:
    """انواع ربات‌های تلگرام"""
    name: str
    description: str
    keywords: List[str]
    features: List[str]
    price_range: Tuple[int, int]  # (min, max) in Rials
    
    def match_score(self, code: str) -> int:
        """امتیاز تطابق با این نوع ربات"""
        score = 0
        code_lower = code.lower()
        
        for keyword in self.keywords:
            if keyword in code_lower:
                score += 10
                # اگر کلمه کلیدی چندبار تکرار شده
                score += min(code_lower.count(keyword) * 2, 10)
        
        return score

# لیست انواع ربات‌ها
BOT_TYPES = [
    BotType(
        name="فروشگاه آنلاین",
        description="ربات فروش محصولات و خدمات با درگاه پرداخت",
        keywords=[
            "shop", "store", "فروش", "فروشگاه", "محصول", "کالا", "سبد خرید",
            "cart", "خرید", "سفارش", "order", "price", "قیمت", "تخفیف"
        ],
        features=[
            "📦 نمایش محصولات",
            "🛒 سبد خرید",
            "💳 درگاه پرداخت",
            "📊 مدیریت سفارشات",
            "👤 پنل کاربری"
        ],
        price_range=(3000000, 10000000)
    ),
    
    BotType(
        name="آموزشی و درسی",
        description="ربات آموزش، آزمون و محتوای آموزشی",
        keywords=[
            "course", "lesson", "آموزش", "درس", "آزمون", "سوال", "جواب",
            "exam", "test", "quiz", "تمرین", "مدرسه", "دانشگاه", "کتاب"
        ],
        features=[
            "📚 ارائه محتوا",
            "📝 آزمون و تمرین",
            "📊 نمره‌دهی",
            "👨‍🏫 مدیریت کلاس",
            "📅 برنامه زمانبندی"
        ],
        price_range=(2500000, 8000000)
    ),
    
    BotType(
        name="اخبار و اطلاع‌رسانی",
        description="ربات ارسال اخبار، اعلان‌ها و اطلاعیه‌ها",
        keywords=[
            "news", "آخرین اخبار", "اطلاعیه", "اعلان", "notification",
            "خبر", "روزنامه", "media", "رسانه", "broadcast", "پخش"
        ],
        features=[
            "📰 دریافت اخبار",
            "🔔 اعلان‌های خودکار",
            "📡 RSS/API",
            "👥 مدیریت مخاطبین",
            "📊 آمار بازدید"
        ],
        price_range=(2000000, 6000000)
    ),
    
    BotType(
        name="سرگرمی و بازی",
        description="ربات بازی، مسابقه و سرگرمی",
        keywords=[
            "game", "play", "بازی", "سرگرمی", "مسابقه", "قرعه کشی",
            "lottery", "جایزه", "امتیاز", "score", "level", "لول"
        ],
        features=[
            "🎮 بازی تعاملی",
            "🏆 سیستم امتیازدهی",
            "📊 رتبه‌بندی",
            "🎁 جوایز و هدایا",
            "👥 بازی چندنفره"
        ],
        price_range=(1800000, 5000000)
    ),
    
    BotType(
        name="مدیریت گروه",
        description="ربات مدیریت و ادمین گروه‌های تلگرام",
        keywords=[
            "group", "admin", "مدیریت", "گروه", "ایدمین", "عضویت",
            "welcome", "خوش آمد", "kick", "ban", "filter", "فیلتر"
        ],
        features=[
            "👑 مدیریت اعضا",
            "🛡️ فیلتر اسپم",
            "👋 خوشآمدگویی",
            "📝 تنظیم قوانین",
            "📊 آمار گروه"
        ],
        price_range=(1500000, 4000000)
    ),
    
    BotType(
        name="خدمات و ابزار",
        description="ربات ارائه خدمات کاربردی و ابزار",
        keywords=[
            "tool", "service", "ابزار", "سرویس", "تبدیل", "download",
            "دانلود", "convert", "جستجو", "search", "calculator", "ماشین حساب"
        ],
        features=[
            "🔧 ابزارهای کاربردی",
            "📁 مدیریت فایل",
            "🔍 جستجوی پیشرفته",
            "📊 تحلیل داده",
            "⚙️ تنظیمات سفارشی"
        ],
        price_range=(2000000, 7000000)
    ),
    
    BotType(
        name="پشتیبانی و چت",
        description="ربات پشتیبانی، پاسخگویی و چت هوشمند",
        keywords=[
            "support", "help", "پشتیبانی", "چت", "سوال", "پاسخ",
            "ticket", "تیکت", "contact", "تماس", "faq", "سوالات متداول"
        ],
        features=[
            "💬 چت هوشمند",
            "🎫 سیستم تیکت",
            "🤖 پاسخ خودکار",
            "📞 تماس با پشتیبانی",
            "📚 پایگاه دانش"
        ],
        price_range=(2500000, 7500000)
    ),
    
    BotType(
        name="مالی و حسابداری",
        description="ربات مدیریت مالی، حسابداری و تراکنش‌ها",
        keywords=[
            "finance", "accounting", "مالی", "حسابداری", "تراکنش",
            "transaction", "wallet", "کیف پول", "حساب", "balance", "موجودی"
        ],
        features=[
            "💰 مدیریت کیف پول",
            "📊 گزارش مالی",
            "💸 تراکنش‌ها",
            "📈 نمودارهای تحلیلی",
            "🔒 امنیت بالا"
        ],
        price_range=(3000000, 9000000)
    ),
    
    BotType(
        name="سلامت و تناسب اندام",
        description="ربات ورزش، رژیم و سلامت",
        keywords=[
            "health", "fitness", "سلامت", "ورزش", "رژیم", "diet",
            "exercise", "تمرین", "food", "غذا", "calorie", "کالری"
        ],
        features=[
            "🏃‍♂️ برنامه ورزشی",
            "🥗 رژیم غذایی",
            "📊 پیگیری پیشرفت",
            "⏰ یادآورها",
            "📈 نمودار تغییرات"
        ],
        price_range=(2000000, 6000000)
    ),
    
    BotType(
        name="سفارشی (Custom)",
        description="ربات سفارشی با قابلیت‌های خاص",
        keywords=[],
        features=[
            "⚡ منطق سفارشی",
            "🔗 API اختصاصی",
            "📊 دیتابیس پیچیده",
            "🎨 UI اختصاصی",
            "🔐 سیستم امنیتی"
        ],
        price_range=(4000000, 15000000)
    )
]

# ==================== ADVANCED CODE ANALYZER ====================
class AdvancedBotAnalyzer:
    """تحلیل‌گر پیشرفته کد ربات"""
    
    def __init__(self):
        self.bot_types = BOT_TYPES
        
    def analyze_code(self, code: str) -> Dict[str, Any]:
        """تحلیل کامل کد ربات"""
        analysis = {
            "basic_info": self._get_basic_info(code),
            "bot_type": self._detect_bot_type(code),
            "features": self._extract_features(code),
            "technical": self._analyze_technical(code),
            "score": 0
        }
        
        # محاسبه امتیاز
        analysis["score"] = self._calculate_score(analysis)
        
        return analysis
    
    def _get_basic_info(self, code: str) -> Dict[str, Any]:
        """اطلاعات پایه کد"""
        lines = code.split('\n')
        code_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
        comment_lines = [l for l in lines if l.strip().startswith('#')]
        
        return {
            "total_lines": len(lines),
            "code_lines": len(code_lines),
            "comment_lines": len(comment_lines),
            "comment_ratio": len(comment_lines) / max(len(code_lines), 1),
            "file_size_kb": len(code.encode('utf-8')) / 1024
        }
    
    def _detect_bot_type(self, code: str) -> Dict[str, Any]:
        """تشخیص نوع ربات"""
        code_lower = code.lower()
        
        # محاسبه امتیاز برای هر نوع
        type_scores = []
        for bot_type in self.bot_types:
            score = bot_type.match_score(code)
            if score > 0:
                type_scores.append((bot_type, score))
        
        # مرتب‌سازی بر اساس امتیاز
        type_scores.sort(key=lambda x: x[1], reverse=True)
        
        if type_scores:
            main_type, main_score = type_scores[0]
            secondary_types = []
            
            # انواع ثانویه (با امتیاز بالای ۵۰٪ امتیاز اصلی)
            for bot_type, score in type_scores[1:]:
                if score > main_score * 0.5:
                    secondary_types.append({
                        "name": bot_type.name,
                        "score": score
                    })
            
            return {
                "name": main_type.name,
                "description": main_type.description,
                "confidence": min(main_score / 100, 1.0),
                "secondary_types": secondary_types[:2],  # حداکثر ۲ نوع ثانویه
                "features": main_type.features,
                "price_range": main_type.price_range
            }
        else:
            # اگر نوعی تشخیص داده نشد
            custom_type = self.bot_types[-1]  # سفارشی
            return {
                "name": custom_type.name,
                "description": custom_type.description,
                "confidence": 0.3,
                "secondary_types": [],
                "features": custom_type.features,
                "price_range": custom_type.price_range
            }
    
    def _extract_features(self, code: str) -> Dict[str, List[str]]:
        """استخراج ویژگی‌های ربات"""
        code_lower = code.lower()
        
        features = {
            "user_interface": [],
            "functionality": [],
            "technical": [],
            "integrations": []
        }
        
        # UI Features
        ui_patterns = {
            "ReplyKeyboardMarkup": "کیبورد معمولی",
            "InlineKeyboardMarkup": "کیبورد اینلاین",
            "ForceReply": "فورس ریپلای",
            "ReplyKeyboardRemove": "حذف کیبورد"
        }
        
        for pattern, name in ui_patterns.items():
            if pattern in code:
                features["user_interface"].append(name)
        
        # Functionality Features
        func_patterns = {
            "CommandHandler": "دستورات سفارشی",
            "CallbackQueryHandler": "دکمه‌های اینلاین",
            "ConversationHandler": "مکالمه چندمرحله‌ای",
            "JobQueue": "زمان‌بندی خودکار",
            "filters.TEXT": "پردازش متن",
            "filters.PHOTO": "پردازش عکس",
            "filters.Document.ALL": "پردازش فایل"
        }
        
        for pattern, name in func_patterns.items():
            if pattern in code:
                features["functionality"].append(name)
        
        # Technical Features
        tech_patterns = {
            "async def": "برنامه‌نویسی Async",
            "asyncio": "مدیریت همزمانی",
            "try:.*except": "مدیریت خطا",
            "logging": "سیستم لاگ‌گیری",
            "class.*:": "برنامه‌نویسی شی‌گرا"
        }
        
        for pattern, name in tech_patterns.items():
            if re.search(pattern, code, re.DOTALL):
                features["technical"].append(name)
        
        # Integrations
        int_patterns = {
            "sqlite3": "SQLite Database",
            "mysql": "MySQL Database",
            "postgresql": "PostgreSQL",
            "redis": "Redis Cache",
            "requests": "API Calls",
            "httpx": "Async HTTP",
            "aiohttp": "Async Web"
        }
        
        for pattern, name in int_patterns.items():
            if pattern in code_lower:
                features["integrations"].append(name)
        
        return features
    
    def _analyze_technical(self, code: str) -> Dict[str, Any]:
        """تحلیل فنی کد"""
        # تحلیل ساختار کد
        class_count = len(re.findall(r'class\s+\w+', code))
        function_count = len(re.findall(r'(async\s+)?def\s+\w+', code))
        
        # تحلیل imports
        imports = re.findall(r'from\s+(\S+)\s+import|import\s+(\S+)', code)
        import_count = len(imports)
        
        # کیفیت کد
        has_error_handling = len(re.findall(r'try:', code)) > 0
        has_logging = 'logging' in code.lower()
        has_comments = len(re.findall(r'#.*', code)) > 10
        
        return {
            "class_count": class_count,
            "function_count": function_count,
            "import_count": import_count,
            "has_error_handling": has_error_handling,
            "has_logging": has_logging,
            "has_comments": has_comments,
            "code_quality": self._calculate_code_quality(code)
        }
    
    def _calculate_code_quality(self, code: str) -> float:
        """محاسبه کیفیت کد (0-1)"""
        quality = 0.0
        
        # 1. ساختار
        if 'class ' in code:
            quality += 0.2
        
        # 2. مدیریت خطا
        if 'try:' in code:
            quality += 0.2
        
        # 3. لاگ‌گیری
        if 'logging' in code.lower():
            quality += 0.1
        
        # 4. کامنت
        comment_lines = len([l for l in code.split('\n') if l.strip().startswith('#')])
        total_lines = len(code.split('\n'))
        if total_lines > 0:
            comment_ratio = comment_lines / total_lines
            if comment_ratio > 0.1:
                quality += 0.2
            elif comment_ratio > 0.05:
                quality += 0.1
        
        # 5. async
        if 'async def' in code:
            quality += 0.1
        
        # 6. organization
        if '__name__' in code and '__main__' in code:
            quality += 0.1
        
        # 7. پیچیدگی کم (خطوط کوتاه)
        lines = code.split('\n')
        avg_line_len = sum(len(l) for l in lines) / len(lines) if lines else 0
        if avg_line_len < 80:
            quality += 0.1
        
        return min(quality, 1.0)
    
    def _calculate_score(self, analysis: Dict[str, Any]) -> int:
        """محاسبه امتیاز کلی (0-100)"""
        score = 0
        
        # 1. اندازه پروژه (تا 20 امتیاز)
        loc = analysis["basic_info"]["code_lines"]
        if loc > 500:
            score += 20
        elif loc > 200:
            score += 15
        elif loc > 100:
            score += 10
        elif loc > 50:
            score += 5
        
        # 2. نوع ربات (تا 15 امتیاز)
        confidence = analysis["bot_type"]["confidence"]
        score += int(confidence * 15)
        
        # 3. ویژگی‌ها (تا 30 امتیاز)
        features = analysis["features"]
        feature_count = sum(len(f) for f in features.values())
        score += min(feature_count * 2, 30)
        
        # 4. فنی (تا 25 امتیاز)
        tech = analysis["technical"]
        if tech["has_error_handling"]:
            score += 5
        if tech["has_logging"]:
            score += 5
        if tech["has_comments"]:
            score += 5
        score += min(tech["class_count"] * 2, 5)
        score += min(tech["function_count"], 5)
        
        # 5. کیفیت کد (تا 10 امتیاز)
        score += int(tech["code_quality"] * 10)
        
        return min(score, 100)

# ==================== PRICE CALCULATOR ====================
class SmartPriceCalculator:
    """ماشین حساب هوشمند قیمت"""
    
    def calculate_price(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """محاسبه قیمت هوشمند"""
        score = analysis["score"]
        bot_type = analysis["bot_type"]
        tech_info = analysis["technical"]
        basic_info = analysis["basic_info"]
        
        # قیمت پایه بر اساس نوع ربات
        type_min, type_max = bot_type["price_range"]
        type_base = (type_min + type_max) // 2
        
        # ضریب امتیاز
        score_factor = 0.5 + (score / 100) * 1.5  # 0.5 تا 2
        
        # ضریب پیچیدگی فنی
        tech_factor = 1.0
        if tech_info["has_error_handling"]:
            tech_factor += 0.1
        if tech_info["has_logging"]:
            tech_factor += 0.1
        if tech_info["code_quality"] > 0.7:
            tech_factor += 0.2
        elif tech_info["code_quality"] > 0.4:
            tech_factor += 0.1
        
        # ضریب اندازه پروژه
        size_factor = 1.0
        loc = basic_info["code_lines"]
        if loc > 500:
            size_factor = 1.3
        elif loc > 200:
            size_factor = 1.2
        elif loc > 100:
            size_factor = 1.1
        
        # محاسبه قیمت نهایی
        raw_price = type_base * score_factor * tech_factor * size_factor
        
        # اعمال محدودیت‌ها
        min_price = 500000  # 500 هزار ریال
        max_price = 15000000  # 15 میلیون ریال
        price_rials = max(min_price, min(int(raw_price), max_price))
        
        # تبدیل به سایر ارزها
        dollar_rate = 50000
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
            "confidence": bot_type["confidence"],
            "price_breakdown": {
                "type_base": type_base,
                "score_factor": round(score_factor, 2),
                "tech_factor": round(tech_factor, 2),
                "size_factor": round(size_factor, 2)
            }
        }

# ==================== BOT HANDLERS ====================
class EnhancedBotHandlers:
    """Handlerهای پیشرفته ربات"""
    
    def __init__(self):
        self.analyzer = AdvancedBotAnalyzer()
        self.calculator = SmartPriceCalculator()
        self.processing_users = set()
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دستور /start"""
        text = """
🤖 **ربات تحلیل‌گر حرفه‌ای قیمت ربات تلگرام**

✨ **ویژگی‌های جدید:**
• تشخیص نوع ربات (فروشگاهی، آموزشی، مدیریتی و...)
• تحلیل دقیق قابلیت‌ها
• گزارش کامل فنی
• قیمت‌گذاری هوشمند

📊 **نحوه کار:**
۱. فایل `.py` ربات را ارسال کنید
۲. منتظر تحلیل پیشرفته باشید
۳. گزارش کامل دریافت کنید

🎯 **آنالیز می‌شود:**
• نوع و کاربرد ربات
• ویژگی‌های شناسایی شده
• کیفیت کد و ساختار فنی
• قیمت منصفانه

👇 **فایل ربات خود را ارسال کنید:**
        """
        
        await update.message.reply_text(text, parse_mode='Markdown')
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش فایل ارسالی"""
        user_id = update.effective_user.id
        
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
            status_msg = await update.message.reply_text("📥 در حال دریافت فایل...")
            
            # دانلود فایل
            file = await doc.get_file()
            file_bytes = await file.download_as_bytearray()
            
            if len(file_bytes) > 3 * 1024 * 1024:  # 3MB
                await status_msg.edit_text("❌ فایل بسیار بزرگ است! (حداکثر 3MB)")
                return
            
            content = file_bytes.decode('utf-8', errors='ignore')
            
            await status_msg.edit_text("🔍 تحلیل نوع ربات...")
            analysis = self.analyzer.analyze_code(content)
            
            await status_msg.edit_text("💰 محاسبه قیمت...")
            price_result = self.calculator.calculate_price(analysis)
            
            # گزارش
            report = self._create_detailed_report(file_name, analysis, price_result)
            
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=status_msg.message_id
            )
            
            await update.message.reply_text(report, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error: {e}")
            await update.message.reply_text("❌ خطا در پردازش. لطفا دوباره تلاش کنید.")
        
        finally:
            self.processing_users.discard(user_id)
    
    def _create_detailed_report(self, filename: str, analysis: Dict, price: Dict) -> str:
        """ایجاد گزارش کامل"""
        now = datetime.now().strftime('%Y/%m/%d %H:%M')
        bot_type = analysis["bot_type"]
        basic_info = analysis["basic_info"]
        features = analysis["features"]
        tech_info = analysis["technical"]
        
        # بخش نوع ربات
        type_text = f"""
🎯 **تشخیص نوع ربات:**
• **نام:** {bot_type['name']}
• **توضیحات:** {bot_type['description']}
• **اعتماد به تشخیص:** {bot_type['confidence']*100:.0f}%
"""
        
        if bot_type["secondary_types"]:
            type_text += "• **نوع‌های مرتبط:**\n"
            for sec in bot_type["secondary_types"]:
                type_text += f"  └ {sec['name']} ({sec['score']} امتیاز)\n"
        
        # بخش ویژگی‌ها
        features_text = "✨ **ویژگی‌های شناسایی شده:**\n"
        for category, items in features.items():
            if items:
                persian_category = {
                    "user_interface": "رابط کاربری",
                    "functionality": "قابلیت‌ها",
                    "technical": "فنی",
                    "integrations": "ادغام‌ها"
                }.get(category, category)
                
                features_text += f"\n**{persian_category}:**\n"
                for item in items[:5]:  # حداکثر ۵ آیتم
                    features_text += f"• ✅ {item}\n"
                if len(items) > 5:
                    features_text += f"• ... و {len(items)-5} مورد دیگر\n"
        
        # بخش فنی
        tech_text = f"""
⚙️ **تحلیل فنی:**
• خطوط کد: {basic_info['code_lines']} خط
• کامنت: {basic_info['comment_lines']} خط ({basic_info['comment_ratio']*100:.1f}%)
• کلاس‌ها: {tech_info['class_count']} کلاس
• توابع: {tech_info['function_count']} تابع
• کتابخانه‌ها: {tech_info['import_count']} import
• کیفیت کد: {tech_info['code_quality']*100:.0f}/100
• مدیریت خطا: {'✅ دارد' if tech_info['has_error_handling'] else '❌ ندارد'}
• سیستم لاگ: {'✅ دارد' if tech_info['has_logging'] else '❌ ندارد'}
"""
        
        # بخش قیمت
        breakdown = price.get("price_breakdown", {})
        price_text = f"""
💰 **تحلیل قیمت:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏆 امتیاز کلی: **{price['score']}/100**
🎯 سطح: **{price['level']}**

📊 **جزئیات محاسبه:**
• قیمت پایه نوع: {breakdown.get('type_base', 0):,} ریال
• ضریب امتیاز: {breakdown.get('score_factor', 1):.2f}x
• ضریب فنی: {breakdown.get('tech_factor', 1):.2f}x
• ضریب اندازه: {breakdown.get('size_factor', 1):.2f}x

💎 **قیمت نهایی:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💵 ریال: **{price['price_rials']:,} ریال**
💳 تومان: **{price['price_tomans']:,} تومان**
💲 دلار: **${price['price_usd']:,}**

📈 **محدوده قیمت بازار:**
• حداقل: {bot_type['price_range'][0]:,} ریال
• حداکثر: {bot_type['price_range'][1]:,} ریال
"""
        
        # جمع‌بندی
        summary = f"""
📄 **گزارش تحلیل حرفه‌ای ربات تلگرام**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 فایل: `{filename}`
⏰ زمان تحلیل: {now}
🔍 روش: تشخیص الگو + تحلیل کد

{type_text}
{features_text}
{tech_text}
{price_text}

💡 **نکات مهم:**
• این تحلیل بر اساس کد فعلی ربات است
• قیمت بر اساس کیفیت و قابلیت‌ها محاسبه شده
• برای سفارش توسعه با @username تماس بگیرید

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 ربات تحلیل‌گر حرفه‌ای - نسخه ۱۰.۰
        """
        
        return summary

# ==================== APPLICATION SETUP ====================
class BotApplication:
    """مدیریت اپلیکیشن"""
    
    def __init__(self):
        self.app = None
        self.handlers = EnhancedBotHandlers()
    
    async def setup(self):
        """تنظیم ربات"""
        logger.info("🔧 در حال تنظیم ربات تحلیل‌گر...")
        
        self.app = Application.builder().token(TOKEN).build()
        
        # ثبت handlerها
        self.app.add_handler(CommandHandler("start", self.handlers.start))
        self.app.add_handler(CommandHandler("help", self.handlers.start))
        self.app.add_handler(MessageHandler(filters.Document.ALL, self.handlers.handle_document))
        
        logger.info("✅ تنظیمات کامل شد")
    
    async def run_webhook(self):
        """اجرا با webhook"""
        logger.info(f"🌐 راه‌اندازی Webhook...")
        
        await self.app.bot.delete_webhook()
        
        webhook_url = f"{WEBHOOK_URL}/{TOKEN}"
        await self.app.bot.set_webhook(
            url=webhook_url,
            allowed_updates=Update.ALL_TYPES
        )
        
        logger.info(f"✅ Webhook تنظیم شد: {webhook_url}")
        logger.info("🟢 ربات فعال و آماده است!")
        
        await asyncio.Event().wait()
    
    async def shutdown(self):
        """خاموش کردن"""
        if self.app:
            logger.info("🧹 خاموش کردن ربات...")
            await self.app.bot.delete_webhook()
            await self.app.stop()
            await self.app.shutdown()

# ==================== MAIN ====================
async def main():
    """برنامه اصلی"""
    logger.info("=" * 60)
    logger.info("🤖 ربات تحلیل‌گر قیمت با تشخیص نوع - نسخه ۱۰.۰")
    logger.info("=" * 60)
    
    bot_app = BotApplication()
    
    try:
        await bot_app.setup()
        
        if WEBHOOK_URL:
            await bot_app.run_webhook()
        else:
            logger.warning("⚠️ WEBHOOK_URL not set")
            logger.info("🔵 خروج...")
        
    except KeyboardInterrupt:
        logger.info("👋 دریافت سیگنال توقف")
    except Exception as e:
        logger.error(f"❌ خطا: {e}")
    finally:
        await bot_app.shutdown()

if __name__ == "__main__":
    # بررسی تنظیمات
    if not TOKEN:
        logger.error("❌ BOT_TOKEN تنظیم نشده!")
        logger.error("در Render: Environment → Add BOT_TOKEN")
        sys.exit(1)
    
    # اجرا
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 برنامه متوقف شد")
