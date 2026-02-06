#!/usr/bin/env python3
"""
🤖 Telegram Bot Price Analyzer - Professional Edition
Version: 3.0 - Optimized for Render
Author: AI Assistant
Deploy: Render + Webhook (Fast & Stable)
"""

import os
import re
import ast
import json
import asyncio
import logging
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from io import BytesIO

import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ContextTypes, filters
)

# ==================== CONFIGURATION ====================
TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
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
    """مدل ویژگی‌های استخراج شده از کد"""
    commands: List[str] = field(default_factory=list)
    keyboards: int = 0
    inline_buttons: int = 0
    admin_tools: List[str] = field(default_factory=list)
    games: List[str] = field(default_factory=list)
    user_management: bool = False
    lines_of_code: int = 0
    async_code: bool = False
    error_handling: bool = False
    modular: bool = False
    integrations: List[str] = field(default_factory=list)
    database_used: bool = False
    payment_gateway: bool = False
    external_apis: List[str] = field(default_factory=list)
    comments_ratio: float = 0.0
    code_quality: float = 0.0
    has_webhook: bool = False
    has_scheduler: bool = False

@dataclass
class ScoringResult:
    """نتیجه امتیازدهی"""
    feature_scores: Dict[str, float] = field(default_factory=dict)
    total_score: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PriceCalculation:
    """محاسبه قیمت"""
    base_price: int = 2_000_000  # 2,000,000 Rials
    dollar_rate: float = 50_000.0  # Default
    score_multiplier: float = 1.0
    final_price: int = 0
    breakdown: Dict[str, Any] = field(default_factory=dict)

# ==================== CODE ANALYZER ====================
class TelegramCodeAnalyzer:
    """تحلیل‌گر هوشمند کد ربات تلگرام"""
    
    def __init__(self):
        self.features = CodeFeature()
        
    async def analyze_file(self, file_content: str) -> CodeFeature:
        """تحلیل کامل کد پایتون"""
        
        # تحلیل اولیه
        self._quick_analysis(file_content)
        
        # تحلیل عمیق
        await self._deep_analysis(file_content)
        
        return self.features
    
    def _quick_analysis(self, content: str):
        """تحلیل سریع با regex"""
        
        # تعداد خطوط کد
        lines = content.split('\n')
        code_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
        self.features.lines_of_code = len(code_lines)
        
        # نسبت کامنت
        comment_lines = len([l for l in lines if l.strip().startswith('#')])
        if self.features.lines_of_code > 0:
            self.features.comments_ratio = comment_lines / self.features.lines_of_code
        
        # تشخیص async
        self.features.async_code = any(
            re.search(pattern, content, re.IGNORECASE) 
            for pattern in [r'async def', r'asyncio', r'await']
        )
        
        # تشخیص دستورات
        command_patterns = [
            (r'CommandHandler\("(\w+)"', 'standard'),
            (r'@app\.command\("(\w+)"', 'decorator'),
            (r'async def (\w+).*update.*context', 'function')
        ]
        
        for pattern, _ in command_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, str) and match not in self.features.commands:
                    self.features.commands.append(match)
    
    async def _deep_analysis(self, content: str):
        """تحلیل عمیق کد"""
        
        # تشخیص کیبوردها
        keyboard_patterns = [
            (r'ReplyKeyboardMarkup', 'keyboard'),
            (r'InlineKeyboardMarkup', 'inline_keyboard'),
            (r'KeyboardButton', 'button'),
            (r'InlineKeyboardButton', 'inline_button')
        ]
        
        for pattern, key in keyboard_patterns:
            matches = re.findall(pattern, content)
            if key == 'inline_button':
                self.features.inline_buttons += len(matches)
            elif key == 'keyboard':
                self.features.keyboards += 1
        
        # تشخیص دیتابیس
        db_patterns = [
            r'sqlite3', r'psycopg2', r'mysql', r'pymongo',
            r'peewee', r'sqlalchemy', r'redis', r'PostgreSQL'
        ]
        
        for pattern in db_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                self.features.database_used = True
                self.features.integrations.append('database')
                break
        
        # تشخیص پرداخت
        payment_patterns = [
            r'zarinpal', r'idpay', r'nextpay', r'پرداخت',
            r'payment.*gateway', r'درگاه.*پرداخت'
        ]
        
        for pattern in payment_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                self.features.payment_gateway = True
                self.features.integrations.append('payment')
                break
        
        # تشخیص API خارجی
        api_patterns = [
            r'requests\.(get|post|put|delete)',
            r'httpx\.', r'aiohttp\.',
            r'api\.', r'\.com/api'
        ]
        
        for pattern in api_patterns:
            if re.search(pattern, content):
                self.features.external_apis.append('external_api')
        
        # تشخیص وب‌هوک
        self.features.has_webhook = any(
            re.search(pattern, content, re.IGNORECASE)
            for pattern in [r'webhook', r'run_webhook', r'setWebhook']
        )
        
        # تشخیص زمان‌بند
        self.features.has_scheduler = any(
            re.search(pattern, content, re.IGNORECASE)
            for pattern in [r'job_queue', r'run_repeating', r'JobQueue']
        )
        
        # تشخیص مدیریت خطا
        self.features.error_handling = any(
            re.search(pattern, content, re.IGNORECASE)
            for pattern in [r'try.*except', r'except.*:', r'error.*handling']
        )
        
        # محاسبه کیفیت کد
        self._calculate_code_quality(content)
    
    def _calculate_code_quality(self, content: str):
        """محاسبه کیفیت کد"""
        quality_score = 0.0
        
        # 1. ساختار
        if 'class ' in content:
            quality_score += 0.2
        
        # 2. کامنت
        if self.features.comments_ratio > 0.1:
            quality_score += 0.3
        elif self.features.comments_ratio > 0.05:
            quality_score += 0.1
        
        # 3. مدیریت خطا
        if self.features.error_handling:
            quality_score += 0.2
        
        # 4. async
        if self.features.async_code:
            quality_score += 0.1
        
        # 5. webhook
        if self.features.has_webhook:
            quality_score += 0.1
        
        # 6. نام‌گذاری
        if re.search(r'def get_|def handle_|def process_', content):
            quality_score += 0.1
        
        self.features.code_quality = min(quality_score, 1.0)

# ==================== SCORING SYSTEM ====================
class PriceScoringEngine:
    """موتور امتیازدهی و قیمت‌گذاری"""
    
    def __init__(self, dollar_rate: float = 50000.0):
        self.dollar_rate = dollar_rate
        
    async def calculate_score(self, features: CodeFeature) -> ScoringResult:
        """محاسبه امتیاز کلی"""
        
        scores = {}
        details = {}
        
        # 1. امتیاز دستورات
        cmd_count = len(features.commands)
        cmd_score = min(cmd_count * 2, 15)
        scores['commands'] = cmd_score
        details['commands'] = {
            'count': cmd_count,
            'score': cmd_score
        }
        
        # 2. امتیاز کیبوردها
        kb_score = min(features.keyboards * 2 + features.inline_buttons * 0.5, 10)
        scores['keyboards'] = kb_score
        details['keyboards'] = {
            'regular': features.keyboards,
            'inline': features.inline_buttons,
            'score': kb_score
        }
        
        # 3. امتیاز ابزار ادمین
        admin_score = 0
        if 'admin' in [c.lower() for c in features.commands]:
            admin_score += 4
        if features.database_used:
            admin_score += 4
        if any(cmd in features.commands for cmd in ['stats', 'report', 'آمار']):
            admin_score += 4
        admin_score = min(admin_score, 12)
        scores['admin_tools'] = admin_score
        
        # 4. امتیاز بازی‌ها
        game_score = 0
        if any(word in str(features.commands).lower() for word in ['game', 'play', 'بازی']):
            game_score = min(features.lines_of_code / 1000 * 8, 8)
        scores['games'] = game_score
        
        # 5. امتیاز مدیریت کاربران
        user_score = 0
        if features.database_used:
            user_score += 6
        if any(cmd in features.commands for cmd in ['profile', 'user', 'پروفایل']):
            user_score += 4
        scores['user_management'] = min(user_score, 10)
        
        # 6. امتیاز پیچیدگی فنی
        tech_score = 0
        if features.async_code:
            tech_score += 5
        if features.lines_of_code > 300:
            tech_score += 8
        elif features.lines_of_code > 100:
            tech_score += 4
        if features.error_handling:
            tech_score += 4
        if features.has_webhook:
            tech_score += 3
        scores['technical'] = min(tech_score, 20)
        
        # 7. امتیاز ادغام‌ها
        int_score = 0
        if features.database_used:
            int_score += 5
        if features.payment_gateway:
            int_score += 5
        if features.external_apis:
            int_score += 5
        scores['integrations'] = min(int_score, 15)
        
        # 8. امتیاز کیفیت کد
        quality_score = features.code_quality * 10
        scores['code_quality'] = quality_score
        
        # امتیاز کل
        total_score = sum(scores.values())
        
        return ScoringResult(
            feature_scores=scores,
            total_score=total_score,
            details=details
        )
    
    async def calculate_price(self, score: float) -> PriceCalculation:
        """محاسبه قیمت بر اساس امتیاز"""
        
        # قیمت پایه
        base_price = 2_000_000
        
        # دریافت نرخ لحظه‌ای دلار
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(EXCHANGE_RATE_API, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.dollar_rate = data['rates']['IRR'] / 10
        except:
            pass  # استفاده از نرخ پیش‌فرض
        
        # ضریب دلار
        dollar_multiplier = self.dollar_rate / 50000.0
        
        # ضریب امتیاز
        score_multiplier = score / 50.0
        
        # محاسبه قیمت
        raw_price = base_price * score_multiplier * dollar_multiplier
        
        # اعمال محدودیت‌ها
        final_price = max(500_000, min(int(raw_price), 10_000_000))
        
        # جزئیات محاسبه
        breakdown = {
            'base_price': f"{base_price:,} ریال",
            'dollar_rate': f"{self.dollar_rate:,.0f} ریال",
            'dollar_multiplier': f"{dollar_multiplier:.2f}",
            'score_multiplier': f"{score_multiplier:.2f}",
            'raw_calculation': f"{raw_price:,.0f} ریال",
            'final_price': f"{final_price:,} ریال"
        }
        
        return PriceCalculation(
            base_price=base_price,
            dollar_rate=self.dollar_rate,
            score_multiplier=score_multiplier,
            final_price=final_price,
            breakdown=breakdown
        )

# ==================== BOT HANDLERS ====================
class BotPriceAnalyzerBot:
    """ربات اصلی تحلیل قیمت"""
    
    def __init__(self):
        self.analyzer = TelegramCodeAnalyzer()
        self.scoring_engine = PriceScoringEngine()
        self.user_sessions = {}
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دستور /start"""
        user_id = update.effective_user.id
        
        welcome_text = """
🎯 **ربات تحلیل‌گر قیمت ربات‌های تلگرام**

📊 **چگونه کار می‌کند؟**
1️⃣ فایل Python ربات خود را ارسال کنید
2️⃣ ربات کد شما را تحلیل می‌کند
3️⃣ قیمت واقعی ربات محاسبه می‌شود
4️⃣ گزارش کامل دریافت کنید

💰 **فرمول قیمت‌گذاری:**
• قیمت پایه: ۲,۰۰۰,۰۰۰ ریال
• ضریب کیفیت کد: ۰ تا ۲ برابر
• ضریب نرخ دلار: لحظه‌ای

📈 **معیارهای تحلیل:**
✓ تعداد دستورات و قابلیت‌ها
✓ کیبوردها و رابط کاربری
✓ ابزارهای مدیریتی
✓ پیچیدگی فنی و کیفیت کد
✓ ادغام با سرویس‌های خارجی

👇 **فایل Python ربات خود را همین حالا ارسال کنید**
        """
        
        keyboard = [
            [InlineKeyboardButton("📋 نمونه گزارش", callback_data="sample")],
            [InlineKeyboardButton("❓ راهنمای کامل", callback_data="help")],
            [InlineKeyboardButton("💬 پشتیبانی", url="https://t.me/username")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش فایل ارسالی"""
        user_id = update.effective_user.id
        
        if not update.message.document:
            await update.message.reply_text("⚠️ لطفا یک فایل Python (.py) ارسال کنید.")
            return
        
        document = update.message.document
        file_name = document.file_name
        
        if not file_name.endswith('.py'):
            await update.message.reply_text("❌ فقط فایل‌های Python با پسوند .py قابل تحلیل هستند.")
            return
        
        # وضعیت پردازش
        status_msg = await update.message.reply_text("🔍 در حال دانلود و تحلیل فایل...")
        
        try:
            # دانلود فایل
            file = await document.get_file()
            file_content_bytes = await file.download_as_bytearray()
            file_content = file_content_bytes.decode('utf-8', errors='ignore')
            
            # به‌روزرسانی وضعیت
            await status_msg.edit_text("📊 در حال تحلیل ساختار کد...")
            
            # تحلیل کد
            features = await self.analyzer.analyze_file(file_content)
            
            await status_msg.edit_text("🧮 در حال محاسبه امتیاز و قیمت...")
            
            # محاسبه امتیاز
            scoring_result = await self.scoring_engine.calculate_score(features)
            
            # محاسبه قیمت
            price_calc = await self.scoring_engine.calculate_price(scoring_result.total_score)
            
            # تولید گزارش
            report = await self._generate_report(features, scoring_result, price_calc, file_name)
            
            # حذف پیام وضعیت و ارسال گزارش
            await context.bot.delete_message(
                chat_id=status_msg.chat_id,
                message_id=status_msg.message_id
            )
            
            # ارسال گزارش در چند بخش اگر طولانی باشد
            await self._send_report(update, context, report)
            
        except Exception as e:
            logger.error(f"Error: {e}")
            await update.message.reply_text(f"❌ خطا در پردازش: {str(e)[:200]}")
    
    async def _generate_report(self, features: CodeFeature, 
                              scoring: ScoringResult, 
                              price: PriceCalculation,
                              filename: str) -> str:
        """تولید گزارش نهایی"""
        
        # هدر گزارش
        report = f"""
📄 **گزارش تحلیل قیمت ربات تلگرام**
📁 فایل: `{filename}`
⏰ زمان تحلیل: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 **خلاصه فنی:**
┌ تعداد دستورات: {len(features.commands)} مورد
├ خطوط کد: {features.lines_of_code:,} خط
├ کیبوردها: {features.keyboards} معمولی + {features.inline_buttons} اینلاین
├ دیتابیس: {'✅ دارد' if features.database_used else '❌ ندارد'}
├ درگاه پرداخت: {'✅ دارد' if features.payment_gateway else '❌ ندارد'}
├ API خارجی: {'✅ دارد' if features.external_apis else '❌ ندارد'}
├ مدیریت خطا: {'✅ دارد' if features.error_handling else '❌ ندارد'}
├ معماری: {'✅ Async' if features.async_code else '❌ Sync'}
└ کیفیت کد: {self._get_quality_stars(features.code_quality)}

📊 **امتیازدهی (از ۱۰۰):**
"""
        
        # جدول امتیازها
        categories = {
            'commands': 'دستورات',
            'keyboards': 'کیبوردها',
            'admin_tools': 'ابزار ادمین',
            'games': 'بازی‌ها',
            'user_management': 'مدیریت کاربران',
            'technical': 'پیچیدگی فنی',
            'integrations': 'ادغام‌ها',
            'code_quality': 'کیفیت کد'
        }
        
        for eng, pers in categories.items():
            score = scoring.feature_scores.get(eng, 0)
            max_score = 15 if eng in ['commands', 'integrations'] else \
                       12 if eng == 'admin_tools' else \
                       10 if eng in ['keyboards', 'user_management', 'code_quality'] else \
                       8 if eng == 'games' else 20
            bar = self._create_progress_bar(score, max_score)
            report += f"┌ {pers}: {score:.1f}/{max_score} {bar}\n"
        
        report += f"└ {'─' * 40}\n"
        report += f"   🏆 **امتیاز کل: {scoring.total_score:.1f}/100**\n\n"
        
        # قیمت‌گذاری
        price_in_usd = price.final_price / price.dollar_rate
        price_in_toman = price.final_price / 10
        
        report += f"""
💰 **تحلیل قیمت:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
قیمت پایه: {price.base_price:,} ریال
نرخ دلار: {price.dollar_rate:,.0f} ریال
ضریب کیفیت: {price.score_multiplier:.2f}x

💎 **قیمت نهایی پیشنهادی:**
┌ ریال: **{price.final_price:,} ریال**
├ تومان: **{price_in_toman:,.0f} تومان**
└ دلار: **{price_in_usd:,.0f} دلار**

📈 **سطح ربات:**
"""
        
        if scoring.total_score >= 80:
            report += "🏆 **سطح حرفه‌ای** - ربات کامل با امکانات پیشرفته\n"
        elif scoring.total_score >= 60:
            report += "⭐ **سطح متوسط** - ربات کاربردی با قابلیت‌های خوب\n"
        elif scoring.total_score >= 40:
            report += "📱 **سطح استاندارد** - ربات پایه با امکانات ضروری\n"
        else:
            report += "🛠️ **سطح ساده** - ربات مقدماتی\n"
        
        # پیشنهادات بهبود
        report += "\n🎯 **پیشنهادات برای افزایش قیمت:**\n"
        suggestions = await self._get_improvement_suggestions(scoring, features)
        report += suggestions
        
        # نکات نهایی
        report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 **نکات مهم:**
• این قیمت بر اساس تحلیل خودکار کد محاسبه شده
• قیمت‌های بازار ممکن است متفاوت باشند
• کیفیت طراحی UI/UX در این تحلیل لحاظ نشده
• زمان توسعه و پیچیدگی منطق تجاری محاسبه شده

🤝 **برای سفارش توسعه یا مشاوره بیشتر:**
@username
        """
        
        return report
    
    def _get_quality_stars(self, quality: float) -> str:
        """نمایش کیفیت با ستاره"""
        stars = int(quality * 5)
        return "⭐" * stars + "☆" * (5 - stars)
    
    def _create_progress_bar(self, value: float, max_value: float, length: int = 10) -> str:
        """ایجاد نوار پیشرفت"""
        filled = int(value / max_value * length)
        return "█" * filled + "░" * (length - filled)
    
    async def _get_improvement_suggestions(self, scoring: ScoringResult, features: CodeFeature) -> str:
        """پیشنهادات بهبود"""
        suggestions = []
        
        if scoring.feature_scores.get('code_quality', 0) < 5:
            suggestions.append("• ✅ افزودن کامنت و docstring به توابع")
        
        if not features.error_handling:
            suggestions.append("• ✅ پیاده‌سازی try/except برای مدیریت خطا")
        
        if not features.database_used:
            suggestions.append("• ✅ اضافه کردن دیتابیس برای ذخیره‌سازی داده")
        
        if scoring.feature_scores.get('integrations', 0) < 5:
            suggestions.append("• ✅ اتصال به یک API خارجی یا سرویس وب")
        
        if scoring.feature_scores.get('admin_tools', 0) < 4:
            suggestions.append("• ✅ ایجاد پنل مدیریت با دستورات ادمین")
        
        if not features.async_code:
            suggestions.append("• ✅ استفاده از Async برای کارایی بهتر")
        
        if not suggestions:
            suggestions.append("• 🎉 ربات شما از کیفیت خوبی برخوردار است!")
        
        return "\n".join(suggestions) + "\n"
    
    async def _send_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE, report: str):
        """ارسال گزارش (تقسیم شده اگر طولانی باشد)"""
        # تلگرام محدودیت 4096 کاراکتر دارد
        if len(report) <= 4000:
            await update.message.reply_text(report, parse_mode='Markdown')
        else:
            # تقسیم به بخش‌های کوچک‌تر
            parts = self._split_report(report)
            for i, part in enumerate(parts, 1):
                if i == 1:
                    await update.message.reply_text(part, parse_mode='Markdown')
                else:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=part,
                        parse_mode='Markdown'
                    )
    
    def _split_report(self, report: str, max_length: int = 4000) -> List[str]:
        """تقسیم گزارش به بخش‌های کوچک"""
        parts = []
        current_part = ""
        
        for line in report.split('\n'):
            if len(current_part) + len(line) + 1 > max_length:
                parts.append(current_part)
                current_part = line + '\n'
            else:
                current_part += line + '\n'
        
        if current_part:
            parts.append(current_part)
        
        return parts
    
    async def handle_sample(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمونه تحلیل"""
        query = update.callback_query
        await query.answer()
        
        sample_text = """
📋 **نمونه گزارش تحلیل:**

🎯 **ربات: ربات فروشگاه آنلاین**
📊 **امتیاز: ۷۸/۱۰۰**
💰 **قیمت: ۴,۵۰۰,۰۰۰ ریال**

✅ **قابلیت‌های اصلی:**
• ۱۵ دستور مختلف
• کیبوردهای اینلاین پویا
• سیستم سبد خرید
• درگاه پرداخت زرین‌پال
• پنل مدیریت پیشرفته
• دیتابیس SQLite

📈 **برای دریافت تحلیل ربات خود:**
فایل Python ربات را ارسال کنید!
        """
        
        keyboard = [
            [InlineKeyboardButton("📤 ارسال فایل ربات", callback_data="send_file")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=sample_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """راهنما"""
        query = update.callback_query
        await query.answer()
        
        help_text = """
📚 **راهنمای کامل ربات تحلیل قیمت**

🎯 **هدف ربات:**
تحلیل خودکار کد ربات‌های تلگرام و محاسبه قیمت منصفانه

📁 **نحوه استفاده:**
1. فایل Python ربات خود را ارسال کنید
2. صبر کنید تا تحلیل انجام شود (۱۰-۳۰ ثانیه)
3. گزارش کامل را دریافت کنید

⚙️ **معیارهای تحلیل:**
• **دستورات:** تعداد و پیچیدگی دستورات
• **رابط کاربری:** کیبوردها و دکمه‌ها
• **مدیریت:** ابزارهای ادمین و مدیریت کاربران
• **فنی:** کیفیت کد، مدیریت خطا، معماری
• **ادغام:** دیتابیس، API، پرداخت

💰 **فرمول قیمت:**
قیمت = (قیمت پایه) × (ضریب کیفیت) × (ضریب دلار)

⚠️ **محدودیت‌ها:**
• فقط فایل‌های .py پشتیبانی می‌شوند
• حداکثر حجم: ۱ مگابایت
• تحلیل بر اساس کد موجود است

❓ **سوالات متداول:**
Q: آیا کد من ذخیره می‌شود؟
A: خیر، تحلیل در لحظه انجام می‌شود.

Q: دقت تحلیل چقدر است؟
A: حدود ۸۵-۹۵% برای ربات‌های استاندارد

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

# ==================== MAIN APPLICATION ====================
async def main():
    """تابع اصلی اجرای ربات"""
    
    # ایجاد اپلیکیشن
    app = Application.builder().token(TOKEN).build()
    
    # ایجاد نمونه ربات
    bot_analyzer = BotPriceAnalyzerBot()
    
    # ثبت هندلرها
    app.add_handler(CommandHandler("start", bot_analyzer.start))
    app.add_handler(CommandHandler("help", bot_analyzer.handle_help))
    app.add_handler(MessageHandler(filters.Document.ALL, bot_analyzer.handle_document))
    app.add_handler(CallbackQueryHandler(bot_analyzer.handle_sample, pattern="^sample$"))
    app.add_handler(CallbackQueryHandler(bot_analyzer.handle_help, pattern="^help$"))
    
    # راه‌اندازی
    if WEBHOOK_URL:
        # Webhook برای Render
        await app.initialize()
        await app.start()
        
        # تنظیم webhook
        await app.bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")
        
        # نگه‌داشتن ربات فعال
        print(f"🤖 Bot is running with webhook at {WEBHOOK_URL}")
        await asyncio.Event().wait()
    else:
        # Polling برای توسعه
        print("🤖 Bot is running in polling mode...")
        await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
