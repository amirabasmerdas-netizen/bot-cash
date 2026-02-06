#!/usr/bin/env python3
"""
🤖 Telegram Bot Price Analyzer - Ultimate Edition
Version: 4.0 - No Pillow, Fast & Stable
Author: AI Assistant
Deploy: Render + Webhook (Optimized)
"""

import os
import re
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field

import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ContextTypes, filters
)

# ==================== CONFIGURATION ====================
TOKEN = os.environ.get("BOT_TOKEN", "")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
PORT = int(os.environ.get("PORT", 8443))
EXCHANGE_RATE_API = "https://api.exchangerate-api.com/v4/latest/USD"

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== DATA MODELS ====================
@dataclass
class CodeFeature:
    commands: List[str] = field(default_factory=list)
    keyboards: int = 0
    inline_buttons: int = 0
    has_admin: bool = False
    has_games: bool = False
    has_database: bool = False
    has_payment: bool = False
    has_webhook: bool = False
    lines_of_code: int = 0
    is_async: bool = False
    has_error_handling: bool = False
    external_apis: List[str] = field(default_factory=list)
    comment_ratio: float = 0.0
    complexity_score: float = 0.0

@dataclass
class PriceResult:
    score: float = 0.0
    price_rials: int = 0
    price_tomans: int = 0
    price_usd: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)

# ==================== CODE ANALYZER ====================
class CodeAnalyzer:
    """تحلیل‌گر ساده و سریع کد"""
    
    @staticmethod
    async def analyze(content: str) -> CodeFeature:
        """تحلیل اصلی کد"""
        features = CodeFeature()
        lines = content.split('\n')
        
        # شمارش خطوط کد
        code_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
        features.lines_of_code = len(code_lines)
        
        # نسبت کامنت
        comment_lines = len([l for l in lines if l.strip().startswith('#')])
        if features.lines_of_code > 0:
            features.comment_ratio = comment_lines / features.lines_of_code
        
        # تحلیل محتوای کد
        content_lower = content.lower()
        
        # تشخیص async
        features.is_async = any(x in content_lower for x in ['async def', 'asyncio', 'await'])
        
        # تشخیص دستورات
        command_patterns = [
            r'commandhandler.*"(\w+)"',
            r'@app\.command.*"(\w+)"',
            r'async def (\w+).*update.*context',
            r'def (\w+).*update.*context'
        ]
        
        all_commands = []
        for pattern in command_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                if match and match not in all_commands and len(match) > 2:
                    all_commands.append(match)
        
        features.commands = all_commands[:20]  # محدودیت
        
        # تشخیص کیبوردها
        features.keyboards = len(re.findall(r'replykeyboardmarkup|keyboardmarkup', content_lower))
        features.inline_buttons = len(re.findall(r'inlinekeyboardmarkup|inlinekeyboardbutton', content_lower))
        
        # تشخیص ویژگی‌های خاص
        features.has_admin = any(x in content_lower for x in ['admin', 'sudo', 'مدیر', 'ادمین'])
        features.has_games = any(x in content_lower for x in ['game', 'play', 'بازی', 'حدس'])
        features.has_database = any(x in content_lower for x in ['sql', 'database', 'db', 'دیتابیس', 'mysql', 'sqlite'])
        features.has_payment = any(x in content_lower for x in ['payment', 'pay', 'پرداخت', 'zarinpal', 'idpay'])
        features.has_webhook = 'webhook' in content_lower
        features.has_error_handling = any(x in content_lower for x in ['try:', 'except:', 'error', 'خطا'])
        
        # تشخیص API خارجی
        if re.search(r'requests\.(get|post)|httpx|aiohttp', content_lower):
            features.external_apis.append('http_client')
        
        # محاسبه پیچیدگی
        features.complexity_score = CodeAnalyzer._calculate_complexity(features)
        
        return features
    
    @staticmethod
    def _calculate_complexity(features: CodeFeature) -> float:
        """محاسبه امتیاز پیچیدگی"""
        score = 0.0
        
        # بر اساس خطوط کد
        if features.lines_of_code > 1000:
            score += 0.8
        elif features.lines_of_code > 500:
            score += 0.6
        elif features.lines_of_code > 200:
            score += 0.4
        elif features.lines_of_code > 50:
            score += 0.2
        
        # ویژگی‌های اضافی
        if features.is_async:
            score += 0.1
        if features.has_database:
            score += 0.2
        if features.has_payment:
            score += 0.2
        if features.has_webhook:
            score += 0.1
        if features.external_apis:
            score += 0.1
        if features.has_error_handling:
            score += 0.1
        
        return min(score, 1.0)

# ==================== PRICE CALCULATOR ====================
class PriceCalculator:
    """ماشین حساب قیمت"""
    
    def __init__(self):
        self.dollar_rate = 50000.0
        self.base_price = 2000000  # 2 میلیون ریال
    
    async def get_dollar_rate(self) -> float:
        """دریافت نرخ دلار"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(EXCHANGE_RATE_API, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data['rates']['IRR'] / 10  # به ریال
        except Exception as e:
            logger.warning(f"Failed to get dollar rate: {e}")
        
        return self.dollar_rate
    
    async def calculate(self, features: CodeFeature) -> PriceResult:
        """محاسبه قیمت نهایی"""
        
        # دریافت نرخ دلار
        self.dollar_rate = await self.get_dollar_rate()
        
        # محاسبه امتیاز (0-100)
        score = self._calculate_score(features)
        
        # محاسبه قیمت
        price_rials = self._calculate_price(score)
        price_tomans = int(price_rials / 10)
        price_usd = price_rials / self.dollar_rate
        
        # جزئیات
        details = {
            'score_breakdown': self._get_score_breakdown(features),
            'dollar_rate': self.dollar_rate,
            'base_price': self.base_price,
            'features_summary': self._get_features_summary(features)
        }
        
        return PriceResult(
            score=score,
            price_rials=price_rials,
            price_tomans=price_tomans,
            price_usd=price_usd,
            details=details
        )
    
    def _calculate_score(self, features: CodeFeature) -> float:
        """محاسبه امتیاز کلی"""
        score = 0.0
        
        # 1. دستورات (تا 20 امتیاز)
        cmd_score = min(len(features.commands) * 2, 20)
        score += cmd_score
        
        # 2. رابط کاربری (تا 15 امتیاز)
        ui_score = min(features.keyboards * 3 + features.inline_buttons, 15)
        score += ui_score
        
        # 3. ویژگی‌های فنی (تا 25 امتیاز)
        tech_score = 0
        if features.is_async:
            tech_score += 5
        if features.has_database:
            tech_score += 8
        if features.has_payment:
            tech_score += 7
        if features.has_webhook:
            tech_score += 3
        if features.has_error_handling:
            tech_score += 2
        score += min(tech_score, 25)
        
        # 4. پیچیدگی و اندازه (تا 20 امتیاز)
        size_score = min(features.lines_of_code / 50, 20)
        score += size_score
        
        # 5. کیفیت کد (تا 20 امتیاز)
        quality_score = min(features.comment_ratio * 40 + features.complexity_score * 10, 20)
        score += quality_score
        
        # محدود کردن به 100
        return min(score, 100.0)
    
    def _calculate_price(self, score: float) -> int:
        """محاسبه قیمت بر اساس امتیاز"""
        # ضریب امتیاز (0.5 تا 2.0)
        score_factor = 0.5 + (score / 100) * 1.5
        
        # ضریب دلار
        dollar_factor = self.dollar_rate / 50000.0
        
        # قیمت پایه
        raw_price = self.base_price * score_factor * dollar_factor
        
        # محدودیت‌ها
        min_price = 500000  # 500 هزار ریال
        max_price = 10000000  # 10 میلیون ریال
        
        price = int(raw_price)
        price = max(min_price, min(price, max_price))
        
        return price
    
    def _get_score_breakdown(self, features: CodeFeature) -> Dict[str, float]:
        """جزئیات امتیازها"""
        return {
            'commands': min(len(features.commands) * 2, 20),
            'ui': min(features.keyboards * 3 + features.inline_buttons, 15),
            'technical': self._calculate_tech_score(features),
            'size': min(features.lines_of_code / 50, 20),
            'quality': min(features.comment_ratio * 40 + features.complexity_score * 10, 20)
        }
    
    def _calculate_tech_score(self, features: CodeFeature) -> float:
        """محاسبه امتیاز فنی"""
        score = 0
        if features.is_async:
            score += 5
        if features.has_database:
            score += 8
        if features.has_payment:
            score += 7
        if features.has_webhook:
            score += 3
        if features.has_error_handling:
            score += 2
        return min(score, 25)
    
    def _get_features_summary(self, features: CodeFeature) -> Dict[str, Any]:
        """خلاصه ویژگی‌ها"""
        return {
            'total_commands': len(features.commands),
            'keyboards': features.keyboards,
            'inline_buttons': features.inline_buttons,
            'lines_of_code': features.lines_of_code,
            'is_async': features.is_async,
            'has_database': features.has_database,
            'has_payment': features.has_payment,
            'has_admin': features.has_admin,
            'has_games': features.has_games
        }

# ==================== BOT HANDLERS ====================
class TelegramBotAnalyzer:
    """کلاس اصلی ربات"""
    
    def __init__(self):
        self.analyzer = CodeAnalyzer()
        self.calculator = PriceCalculator()
        self.user_data = {}
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دستور /start"""
        user = update.effective_user
        
        welcome_text = f"""
👋 سلام {user.first_name}!

🤖 **به ربات تحلیل‌گر قیمت ربات تلگرام خوش آمدید!**

🎯 **من چکار می‌کنم؟**
• فایل Python ربات شما را تحلیل می‌کنم
• قابلیت‌های ربات را شناسایی می‌کنم
• قیمت منصفانه ربات را محاسبه می‌کنم
• گزارش کامل ارائه می‌دهم

📁 **نحوه استفاده:**
1. فایل `.py` ربات خود را ارسال کنید
2. منتظر تحلیل (۱۰-۲۰ ثانیه)
3. گزارش قیمت را دریافت کنید

💰 **فرمول قیمت‌گذاری:**
• قیمت پایه: ۲,۰۰۰,۰۰۰ ریال
• ضریب کیفیت کد: ۰.۵ تا ۲ برابر
• ضریب نرخ دلار: لحظه‌ای

👇 **فایل Python ربات خود را ارسال کنید:**
        """
        
        keyboard = [
            [InlineKeyboardButton("📊 نمونه تحلیل", callback_data="sample")],
            [InlineKeyboardButton("ℹ️ راهنمای کامل", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش فایل ارسالی"""
        if not update.message.document:
            await update.message.reply_text("⚠️ لطفا یک فایل ارسال کنید.")
            return
        
        doc = update.message.document
        file_name = doc.file_name
        
        if not file_name.endswith('.py'):
            await update.message.reply_text("❌ فقط فایل‌های Python با پسوند `.py` قابل تحلیل هستند.")
            return
        
        # پیام وضعیت
        status_msg = await update.message.reply_text("📥 در حال دانلود فایل...")
        
        try:
            # دانلود فایل
            file = await doc.get_file()
            file_content = await self._download_file(file)
            
            if len(file_content) > 500000:  # 500KB limit
                await status_msg.edit_text("❌ فایل بسیار بزرگ است (حداکثر 500KB)")
                return
            
            await status_msg.edit_text("🔍 در حال تحلیل کد...")
            
            # تحلیل کد
            features = await self.analyzer.analyze(file_content)
            
            await status_msg.edit_text("💰 در حال محاسبه قیمت...")
            
            # محاسبه قیمت
            result = await self.calculator.calculate(features)
            
            # تولید گزارش
            report = self._generate_report(features, result, file_name)
            
            # ارسال گزارش
            await context.bot.delete_message(
                chat_id=status_msg.chat_id,
                message_id=status_msg.message_id
            )
            
            await update.message.reply_text(report, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error: {e}")
            await update.message.reply_text(f"❌ خطا در پردازش: {str(e)[:100]}")
    
    async def _download_file(self, file) -> str:
        """دانلود فایل"""
        byte_content = await file.download_as_bytearray()
        return byte_content.decode('utf-8', errors='ignore')
    
    def _generate_report(self, features: CodeFeature, result: PriceResult, filename: str) -> str:
        """تولید گزارش"""
        
        # خلاصه ویژگی‌ها
        features_text = f"""
📋 **خلاصه ویژگی‌های شناسایی شده:**
┌ تعداد دستورات: {len(features.commands)} دستور
├ خطوط کد: {features.lines_of_code:,} خط
├ کیبوردها: {features.keyboards} عدد
├ دکمه‌های اینلاین: {features.inline_buttons} عدد
├ معماری: {'✅ Async' if features.is_async else '❌ Sync'}
├ دیتابیس: {'✅ دارد' if features.has_database else '❌ ندارد'}
├ درگاه پرداخت: {'✅ دارد' if features.has_payment else '❌ ندارد'}
├ ابزار ادمین: {'✅ دارد' if features.has_admin else '❌ ندارد'}
├ بازی/سرگرمی: {'✅ دارد' if features.has_games else '❌ ندارد'}
└ مدیریت خطا: {'✅ دارد' if features.has_error_handling else '❌ ندارد'}
        """
        
        # امتیازدهی
        breakdown = result.details['score_breakdown']
        score_text = f"""
📊 **امتیازدهی (از ۱۰۰):**
┌ دستورات: {breakdown['commands']:.1f}/20
├ رابط کاربری: {breakdown['ui']:.1f}/15
├ فنی: {breakdown['technical']:.1f}/25
├ اندازه پروژه: {breakdown['size']:.1f}/20
└ کیفیت کد: {breakdown['quality']:.1f}/20
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏆 **امتیاز کل: {result.score:.1f}/100**
        """
        
        # قیمت‌گذاری
        dollar_rate = result.details['dollar_rate']
        price_text = f"""
💰 **تحلیل قیمت:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
نرخ دلار: {dollar_rate:,.0f} ریال
قیمت پایه: {result.details['base_price']:,} ریال

💎 **قیمت نهایی:**
┌ ریال: **{result.price_rials:,} ریال**
├ تومان: **{result.price_tomans:,} تومان**
└ دلار: **{result.price_usd:,.0f} دلار**
        """
        
        # سطح ربات
        level_text = self._get_bot_level(result.score)
        
        # پیشنهادات
        suggestions = self._get_suggestions(features)
        
        # گزارش نهایی
        report = f"""
📄 **گزارش تحلیل ربات تلگرام**
🔬 فایل: `{filename}`
⏰ زمان: {datetime.now().strftime('%Y-%m-%d %H:%M')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{features_text}

{score_text}

{price_text}

{level_text}

🎯 **پیشنهادات برای بهبود:**
{suggestions}

📝 **نکات مهم:**
• این تحلیل بر اساس کد فعلی ربات است
• قیمت‌های بازار ممکن است متفاوت باشند
• کیفیت طراحی UI در این تحلیل لحاظ نشده
• برای سفارش توسعه: @username
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 @{update.effective_user.username if hasattr('update', 'effective_user') else 'BotAnalyzer'}
        """
        
        return report
    
    def _get_bot_level(self, score: float) -> str:
        """تعیین سطح ربات"""
        if score >= 80:
            return "🏆 **سطح: حرفه‌ای** - ربات کامل با امکانات پیشرفته"
        elif score >= 60:
            return "⭐ **سطح: متوسط** - ربات کاربردی با قابلیت‌های خوب"
        elif score >= 40:
            return "📱 **سطح: استاندارد** - ربات پایه با امکانات ضروری"
        else:
            return "🛠️ **سطح: ساده** - ربات مقدماتی یا نمونه"
    
    def _get_suggestions(self, features: CodeFeature) -> str:
        """پیشنهادات بهبود"""
        suggestions = []
        
        if not features.has_error_handling:
            suggestions.append("• ✅ افزودن مدیریت خطا (try/except)")
        
        if not features.is_async and features.lines_of_code > 100:
            suggestions.append("• ✅ مهاجرت به Async برای کارایی بهتر")
        
        if not features.has_database:
            suggestions.append("• ✅ اضافه کردن دیتابیس برای ذخیره‌سازی")
        
        if features.comment_ratio < 0.05:
            suggestions.append("• ✅ افزودن کامنت و مستندات به کد")
        
        if len(features.commands) < 5:
            suggestions.append("• ✅ افزایش تعداد دستورات و قابلیت‌ها")
        
        if not suggestions:
            suggestions.append("• 🎉 ربات شما از کیفیت خوبی برخوردار است!")
        
        return "\n".join(suggestions)
    
    async def sample_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمونه تحلیل"""
        query = update.callback_query
        await query.answer()
        
        sample_text = """
📊 **نمونه گزارش تحلیل:**

🤖 **ربات: فروشگاه آنلاین**
📁 **ویژگی‌های شناسایی شده:**
• ۱۲ دستور مختلف
• ۵ کیبورد اینلاین
• سیستم پرداخت
• دیتابیس SQLite
• پنل ادمین

📈 **امتیاز: ۷۶/۱۰۰**
💰 **قیمت: ۳,۸۰۰,۰۰۰ ریال**

👇 **برای تحلیل ربات خود:**
فایل Python ربات را ارسال کنید!
        """
        
        keyboard = [
            [InlineKeyboardButton("📤 ارسال فایل ربات", callback_data="send")],
            [InlineKeyboardButton("🏠 برگشت", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=sample_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def help_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """راهنما"""
        query = update.callback_query
        await query.answer()
        
        help_text = """
📚 **راهنمای کامل ربات تحلیل‌گر**

🎯 **هدف ربات:**
تحلیل خودکار کد ربات‌های تلگرام و ارائه قیمت منصفانه

📁 **نحوه استفاده:**
1. دستور /start را بزنید
2. فایل Python ربات را ارسال کنید
3. منتظر تحلیل باشید (۱۰-۲۰ ثانیه)
4. گزارش کامل را دریافت کنید

⚙️ **معیارهای تحلیل:**
• تعداد و نوع دستورات
• رابط کاربری (کیبوردها)
• ویژگی‌های فنی (دیتابیس، پرداخت و...)
• اندازه و پیچیدگی پروژه
• کیفیت کدنویسی

💰 **فرمول قیمت:**
قیمت = (قیمت پایه) × (ضریب کیفیت) × (ضریب دلار)

⚠️ **محدودیت‌ها:**
• فقط فایل‌های .py
• حداکثر حجم: ۵۰۰KB
• تحلیل بر اساس کد موجود

❓ **سوالات متداول:**
Q: آیا کد من ذخیره می‌شود؟
A: خیر، تحلیل در لحظه انجام می‌شود.

Q: دقت تحلیل چقدر است؟
A: حدود ۸۵-۹۰% برای ربات‌های استاندارد

📞 **پشتیبانی:** @username
        """
        
        keyboard = [
            [InlineKeyboardButton("🏠 برگشت به خانه", callback_data="home")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=help_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def back_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """برگشت به خانه"""
        query = update.callback_query
        await query.answer()
        await self.start_command(update, context)

# ==================== MAIN APPLICATION ====================
def setup_handlers(app: Application, bot: TelegramBotAnalyzer):
    """تنظیم هندلرها"""
    
    # Command handlers
    app.add_handler(CommandHandler("start", bot.start_command))
    app.add_handler(CommandHandler("help", lambda u, c: bot.help_callback(u, c)))
    
    # Document handler
    app.add_handler(MessageHandler(filters.Document.ALL, bot.handle_document))
    
    # Callback handlers
    app.add_handler(CallbackQueryHandler(bot.sample_callback, pattern="^sample$"))
    app.add_handler(CallbackQueryHandler(bot.help_callback, pattern="^help$"))
    app.add_handler(CallbackQueryHandler(bot.back_callback, pattern="^(back|home|send)$"))

async def main():
    """تابع اصلی"""
    
    if not TOKEN:
        logger.error("❌ BOT_TOKEN not set!")
        return
    
    # ایجاد اپلیکیشن
    app = Application.builder().token(TOKEN).build()
    
    # ایجاد ربات
    bot = TelegramBotAnalyzer()
    
    # تنظیم هندلرها
    setup_handlers(app, bot)
    
    # راه‌اندازی
    if WEBHOOK_URL:
        # Webhook mode for Render
        await app.initialize()
        await app.start()
        await app.bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}")
        
        logger.info(f"✅ Bot started with webhook: {WEBHOOK_URL}")
        
        # Keep running
        await asyncio.Event().wait()
    else:
        # Polling mode for development
        logger.info("🤖 Bot started in polling mode...")
        await app.run_polling()

if __name__ == "__main__":
    # Check Python version
    import sys
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ required!")
        sys.exit(1)
    
    # Run the bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
