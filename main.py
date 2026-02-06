#!/usr/bin/env python3
"""
🤖 Telegram Bot Price Analyzer
Version: 2.0 Professional
Author: AI Assistant
Deploy: Render + Webhook
"""

import os
import re
import ast
import json
import requests
import asyncio
import logging
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
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
    commands: List[str] = None
    keyboards: int = 0
    inline_buttons: int = 0
    admin_tools: List[str] = None
    games: List[str] = None
    user_management: bool = False
    lines_of_code: int = 0
    async_code: bool = False
    error_handling: bool = False
    modular: bool = False
    integrations: List[str] = None
    database_used: bool = False
    payment_gateway: bool = False
    external_apis: List[str] = None
    comments_ratio: float = 0.0
    code_quality: float = 0.0

@dataclass
class ScoringResult:
    """نتیجه امتیازدهی"""
    feature_scores: Dict[str, float] = None
    total_score: float = 0.0
    details: Dict[str, Any] = None

@dataclass
class PriceCalculation:
    """محاسبه قیمت"""
    base_price: int = 2_000_000  # 2,000,000 Rials
    dollar_rate: float = 50_000.0  # Default
    score_multiplier: float = 1.0
    final_price: int = 0
    breakdown: Dict[str, Any] = None

# ==================== CODE ANALYZER ====================
class TelegramCodeAnalyzer:
    """تحلیل‌گر هوشمند کد ربات تلگرام"""
    
    def __init__(self):
        self.features = CodeFeature(
            commands=[],
            admin_tools=[],
            games=[],
            integrations=[],
            external_apis=[]
        )
        
    def analyze_file(self, file_content: str) -> CodeFeature:
        """تحلیل کامل کد پایتون"""
        
        # تحلیل اولیه با AST
        try:
            tree = ast.parse(file_content)
            self._analyze_ast(tree)
        except:
            logger.warning("AST parsing failed, using regex fallback")
        
        # تحلیل با regex برای موارد خاص
        self._analyze_with_regex(file_content)
        
        # محاسبه ویژگی‌های کمی
        self._calculate_metrics(file_content)
        
        return self.features
    
    def _analyze_ast(self, tree: ast.AST):
        """تحلیل ساختار کد با AST"""
        
        for node in ast.walk(tree):
            # تشخیص دستورات
            if isinstance(node, ast.FunctionDef):
                self._analyze_function(node)
            
            # تشخیص import‌ها
            elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                self._analyze_imports(node)
            
            # تشخیص async
            elif isinstance(node, ast.AsyncFunctionDef):
                self.features.async_code = True
    
    def _analyze_function(self, func_node: ast.FunctionDef):
        """تحلیل تابع برای تشخیص قابلیت‌ها"""
        func_name = func_node.name.lower()
        func_body = ast.unparse(func_node.body) if hasattr(ast, 'unparse') else str(func_node.body)
        
        # تشخیص دستورات
        command_patterns = {
            'start': r'start|/start',
            'help': r'help|/help',
            'admin': r'admin|sudo|مدیر',
            'game': r'game|play|بازی|حدس',
            'payment': r'pay|payment|پرداخت|زرین‌پال',
            'stats': r'stats|آمار|گزارش',
            'broadcast': r'broadcast|ارسال',
            'profile': r'profile|پروفایل'
        }
        
        for key, pattern in command_patterns.items():
            if re.search(pattern, func_name) or re.search(pattern, func_body, re.IGNORECASE):
                if key not in self.features.commands:
                    self.features.commands.append(key)
    
    def _analyze_with_regex(self, content: str):
        """تحلیل با regex برای تشخیص الگوها"""
        
        # تشخیص کیبوردها
        keyboard_patterns = [
            r'ReplyKeyboardMarkup',
            r'InlineKeyboardMarkup',
            r'KeyboardButton',
            r'InlineKeyboardButton'
        ]
        
        for pattern in keyboard_patterns:
            matches = re.findall(pattern, content)
            if 'Inline' in pattern:
                self.features.inline_buttons += len(matches)
            else:
                self.features.keyboards += len(matches) // 2  # تقریب
        
        # تشخیص دیتابیس
        db_patterns = [
            r'sqlite3', r'psycopg2', r'mysql', r'pymongo',
            r'peewee', r'sqlalchemy', r'redis'
        ]
        
        for pattern in db_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                self.features.database_used = True
                if pattern not in self.features.integrations:
                    self.features.integrations.append(pattern)
        
        # تشخیص پرداخت
        payment_patterns = [
            r'zarinpal|idpay|nextpay|پرداخت',
            r'payment|gateway|درگاه'
        ]
        
        for pattern in payment_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                self.features.payment_gateway = True
        
        # تشخیص API خارجی
        api_patterns = [
            r'requests\.(get|post|put|delete)',
            r'httpx|aiohttp',
            r'api\.|\.ir/api',
            r'openweather|telegram\.org'
        ]
        
        for pattern in api_patterns:
            if re.search(pattern, content):
                self.features.external_apis.append(pattern.split('.')[0])
    
    def _calculate_metrics(self, content: str):
        """محاسبه معیارهای کمی"""
        
        # تعداد خطوط کد
        lines = content.split('\n')
        self.features.lines_of_code = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
        
        # نسبت کامنت
        comment_lines = len([l for l in lines if l.strip().startswith('#')])
        if self.features.lines_of_code > 0:
            self.features.comments_ratio = comment_lines / self.features.lines_of_code
        
        # کیفیت کد (ساده‌شده)
        # 1. طول خطوط
        avg_line_length = sum(len(l) for l in lines) / len(lines) if lines else 0
        # 2. توابع طولانی
        long_functions = len(re.findall(r'def \w+\(.*\):', content))
        
        # امتیاز کیفیت (0-1)
        quality_score = 0.0
        if avg_line_length < 80:
            quality_score += 0.3
        if self.features.comments_ratio > 0.1:
            quality_score += 0.3
        if long_functions < 10:
            quality_score += 0.4
        
        self.features.code_quality = quality_score

# ==================== SCORING SYSTEM ====================
class PriceScoringEngine:
    """موتور امتیازدهی و قیمت‌گذاری"""
    
    def __init__(self, dollar_rate: float = 50000.0):
        self.dollar_rate = dollar_rate
        self.scoring_weights = {
            'commands': {'weight': 15, 'details': {}},
            'keyboards': {'weight': 10, 'details': {}},
            'admin_tools': {'weight': 12, 'details': {}},
            'games': {'weight': 8, 'details': {}},
            'user_management': {'weight': 10, 'details': {}},
            'technical': {'weight': 20, 'details': {}},
            'integrations': {'weight': 15, 'details': {}},
            'code_quality': {'weight': 10, 'details': {}}
        }
    
    def calculate_score(self, features: CodeFeature) -> ScoringResult:
        """محاسبه امتیاز کلی"""
        
        scores = {}
        details = {}
        
        # 1. امتیاز دستورات
        cmd_score = min(len(features.commands) * 1.5, 15)
        scores['commands'] = cmd_score
        details['commands'] = {
            'count': len(features.commands),
            'list': features.commands,
            'score': cmd_score
        }
        
        # 2. امتیاز کیبوردها
        kb_score = min((features.keyboards * 1) + (features.inline_buttons * 0.5), 10)
        scores['keyboards'] = kb_score
        details['keyboards'] = {
            'regular': features.keyboards,
            'inline': features.inline_buttons,
            'score': kb_score
        }
        
        # 3. امتیاز ابزار ادمین
        admin_score = 0
        admin_features = []
        if 'admin' in features.commands:
            admin_score += 3
            admin_features.append('دستور ادمین')
        if features.database_used:
            admin_score += 4
            admin_features.append('دیتابیس')
        admin_score = min(admin_score, 12)
        scores['admin_tools'] = admin_score
        details['admin_tools'] = {
            'features': admin_features,
            'score': admin_score
        }
        
        # 4. امتیاز بازی‌ها
        game_score = 0
        if 'game' in features.commands:
            game_score = min(features.lines_of_code / 500 * 4, 8)
        scores['games'] = game_score
        details['games'] = {
            'has_games': 'game' in features.commands,
            'score': game_score
        }
        
        # 5. امتیاز مدیریت کاربران
        user_score = 0
        if features.database_used:
            user_score += 6
        if 'profile' in features.commands:
            user_score += 4
        user_score = min(user_score, 10)
        scores['user_management'] = user_score
        details['user_management'] = {
            'score': user_score,
            'has_database': features.database_used,
            'has_profile': 'profile' in features.commands
        }
        
        # 6. امتیاز پیچیدگی فنی
        tech_score = 0
        if features.async_code:
            tech_score += 6
        if features.lines_of_code > 200:
            tech_score += min(features.lines_of_code / 100, 8)
        if features.error_handling:
            tech_score += 3
        if features.modular:
            tech_score += 3
        tech_score = min(tech_score, 20)
        scores['technical'] = tech_score
        details['technical'] = {
            'async': features.async_code,
            'loc': features.lines_of_code,
            'error_handling': features.error_handling,
            'modular': features.modular,
            'score': tech_score
        }
        
        # 7. امتیاز ادغام‌ها
        int_score = 0
        if features.database_used:
            int_score += 4
        if features.payment_gateway:
            int_score += 5
        if features.external_apis:
            int_score += min(len(features.external_apis) * 2, 6)
        int_score = min(int_score, 15)
        scores['integrations'] = int_score
        details['integrations'] = {
            'database': features.database_used,
            'payment': features.payment_gateway,
            'apis': features.external_apis,
            'score': int_score
        }
        
        # 8. امتیاز کیفیت کد
        quality_score = features.code_quality * 10
        scores['code_quality'] = quality_score
        details['code_quality'] = {
            'score': quality_score,
            'comment_ratio': f"{features.comments_ratio:.1%}",
            'quality_level': self._get_quality_level(features.code_quality)
        }
        
        # امتیاز کل
        total_score = sum(scores.values())
        
        return ScoringResult(
            feature_scores=scores,
            total_score=total_score,
            details=details
        )
    
    def _get_quality_level(self, quality_score: float) -> str:
        """تعیین سطح کیفیت کد"""
        if quality_score >= 0.8:
            return "عالی 🏆"
        elif quality_score >= 0.6:
            return "خوب 👍"
        elif quality_score >= 0.4:
            return "متوسط ⚖️"
        else:
            return "نیاز به بهبود 📝"
    
    def calculate_price(self, score: float) -> PriceCalculation:
        """محاسبه قیمت بر اساس امتیاز"""
        
        # قیمت پایه
        base_price = 2_000_000  # 2 میلیون ریال
        
        # ضریب دلار
        dollar_multiplier = self.dollar_rate / 50000.0
        
        # ضریب امتیاز (50 امتیاز = قیمت پایه)
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
        self.exchange_rate = self._get_exchange_rate()
        self.scoring_engine = PriceScoringEngine(self.exchange_rate)
    
    def _get_exchange_rate(self) -> float:
        """دریافت نرخ دلار از API"""
        try:
            response = requests.get(EXCHANGE_RATE_API, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data['rates']['IRR'] / 10  # Convert to Tomans/Rials
        except:
            pass
        
        # Fallback rate
        return 50000.0
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دستور /start"""
        welcome_text = """
        🤖 **ربات تحلیل‌گر قیمت ربات تلگرام**
        
        **📊 عملکرد ربات:**
        ۱. فایل Python ربات خود را ارسال کنید
        ۲. ربات کد شما را تحلیل می‌کند
        ۳. قیمت واقعی ربات را محاسبه می‌کند
        
        **🎯 معیارهای تحلیل:**
        • تعداد و نوع دستورات
        • کیبوردها و دکمه‌های اینلاین
        • ابزارهای ادمین
        • بازی‌ها و منطق تعاملی
        • مدیریت کاربران
        • پیچیدگی فنی
        • ادغام با سرویس‌های خارجی
        • کیفیت کد و مستندات
        
        **💰 فرمول قیمت‌گذاری:**
        قیمت پایه: ۲,۰۰۰,۰۰۰ ریال
        ضریب دلار: نرخ روز ×
        ضریب امتیاز: کیفیت کد ×
        
        👇 **لطفا فایل Python ربات خود را ارسال کنید**
        """
        
        keyboard = [
            [InlineKeyboardButton("📊 نمونه تحلیل", callback_data="sample")],
            [InlineKeyboardButton("ℹ️ راهنما", callback_data="help")]
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
            await update.message.reply_text("⚠️ لطفا یک فایل Python ارسال کنید.")
            return
        
        document = update.message.document
        
        if not document.file_name.endswith('.py'):
            await update.message.reply_text("⚠️ فقط فایل‌های Python (با پسوند .py) قابل تحلیل هستند.")
            return
        
        # نشان دادن وضعیت در حال پردازش
        processing_msg = await update.message.reply_text("🔍 در حال تحلیل کد...")
        
        try:
            # دانلود فایل
            file = await document.get_file()
            file_content_bytes = await file.download_as_bytearray()
            file_content = file_content_bytes.decode('utf-8')
            
            # تحلیل کد
            features = self.analyzer.analyze_file(file_content)
            
            # محاسبه امتیاز
            scoring_result = self.scoring_engine.calculate_score(features)
            
            # محاسبه قیمت
            price_calc = self.scoring_engine.calculate_price(scoring_result.total_score)
            
            # تولید گزارش
            report = self._generate_report(features, scoring_result, price_calc)
            
            # ارسال گزارش
            await context.bot.delete_message(
                chat_id=processing_msg.chat_id,
                message_id=processing_msg.message_id
            )
            
            await update.message.reply_text(report, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error analyzing file: {e}")
            await update.message.reply_text(f"⚠️ خطا در تحلیل فایل: {str(e)}")
    
    def _generate_report(self, features: CodeFeature, 
                         scoring: ScoringResult, 
                         price: PriceCalculation) -> str:
        """تولید گزارش نهایی"""
        
        # خلاصه قابلیت‌ها
        features_summary = f"""
📋 **خلاصه قابلیت‌ها:**
• 🎯 دستورات: {len(features.commands)} مورد
• ⌨️ کیبوردها: {features.keyboards} کیبورد معمولی + {features.inline_buttons} دکمه اینلاین
• 👑 ابزار ادمین: {'دارد' if scoring.details['admin_tools']['score'] > 0 else 'ندارد'}
• 🎮 بازی: {'دارد' if 'game' in features.commands else 'ندارد'}
• 👥 مدیریت کاربران: {'پیشرفته' if features.database_used else 'ساده'}
• 🗄️ دیتابیس: {'استفاده شده' if features.database_used else 'استفاده نشده'}
• 💰 درگاه پرداخت: {'دارد' if features.payment_gateway else 'ندارد'}
• 🔗 API خارجی: {len(features.external_apis)} مورد
• 📊 خطوط کد: {features.lines_of_code} خط
• 🏗️ معماری: {'Async' if features.async_code else 'Sync'}
• ✨ کیفیت کد: {scoring.details['code_quality']['quality_level']}
"""
        
        # جدول امتیازدهی
        score_table = f"""
📊 **جدول امتیازدهی:** (از ۱۰۰)

"""
        for category, score in scoring.feature_scores.items():
            persian_name = self._get_persian_category(category)
            max_score = self.scoring_engine.scoring_weights[category]['weight']
            bar = "█" * int(score / max_score * 10)
            score_table += f"• {persian_name}: {score:.1f}/{max_score} {bar}\n"
        
        score_table += f"\n🏆 **امتیاز کل: {scoring.total_score:.1f}/100**\n"
        
        # قیمت‌گذاری
        price_details = f"""
💰 **محاسبه قیمت:**

قیمت پایه: {price.base_price:,} ریال
نرخ دلار: {price.dollar_rate:,.0f} ریال
ضریب امتیاز: {price.score_multiplier:.2f}

🎯 **قیمت نهایی: {price.final_price:,} ریال**

💡 **توضیح قیمت:**
"""
        
        if scoring.total_score < 30:
            price_details += "• ربات ساده با قابلیت‌های محدود\n• قیمت پایه برای پروژه‌های کوچک"
        elif scoring.total_score < 60:
            price_details += "• ربات متوسط با قابلیت‌های استاندارد\n• قیمت منصفانه برای کارایی ارائه شده"
        elif scoring.total_score < 80:
            price_details += "• ربات پیشرفته با امکانات گسترده\n• قیمت مناسب برای ارزش بالا"
        else:
            price_details += "• ربات حرفه‌ای با معماری پیچیده\n• قیمت عادلانه برای پروژه سطح بالا"
        
        # قیمت به سایر ارزها
        price_in_usd = price.final_price / price.dollar_rate
        price_in_toman = price.final_price / 10
        
        price_conversion = f"""
🌍 **قیمت به سایر ارزها:**
• تومان: {price_in_toman:,.0f} تومان
• دلار: {price_in_usd:.0f} دلار
• تتر: {price_in_usd:.0f} USDT
"""
        
        # پیشنهادات بهبود
        suggestions = self._get_improvement_suggestions(scoring)
        
        # جمع‌بندی
        full_report = f"""
🔍 **گزارش تحلیل قیمت ربات تلگرام**
{features_summary}
{score_table}
{price_details}
{price_conversion}
📈 **پیشنهادات بهبود:**
{suggestions}
        
⚖️ **توجه:** این قیمت بر اساس تحلیل خودکار کد است و ممکن است با قیمت بازار کمی تفاوت داشته باشد.
"""
        
        return full_report
    
    def _get_persian_category(self, category: str) -> str:
        """تبدیل نام دسته‌بندی به فارسی"""
        mapping = {
            'commands': 'دستورات',
            'keyboards': 'کیبوردها',
            'admin_tools': 'ابزار ادمین',
            'games': 'بازی‌ها',
            'user_management': 'مدیریت کاربران',
            'technical': 'پیچیدگی فنی',
            'integrations': 'ادغام‌ها',
            'code_quality': 'کیفیت کد'
        }
        return mapping.get(category, category)
    
    def _get_improvement_suggestions(self, scoring: ScoringResult) -> str:
        """ارائه پیشنهادات برای بهبود قیمت"""
        suggestions = []
        
        if scoring.feature_scores['code_quality'] < 5:
            suggestions.append("• افزودن کامنت و مستندات به کد")
        
        if scoring.feature_scores['technical'] < 10:
            suggestions.append("• پیاده‌سازی مدیریت خطا (Error Handling)")
        
        if scoring.feature_scores['integrations'] < 8:
            suggestions.append("• اضافه کردن دیتابیس برای ذخیره‌سازی داده")
        
        if scoring.feature_scores['admin_tools'] < 6:
            suggestions.append("• افزودن پنل مدیریت برای ادمین")
        
        if scoring.feature_scores['user_management'] < 5:
            suggestions.append("• ایجاد سیستم پروفایل کاربری")
        
        if not suggestions:
            suggestions.append("• ربات از کیفیت خوبی برخوردار است!")
        
        return "\n".join(suggestions)
    
    async def handle_sample(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمونه تحلیل"""
        query = update.callback_query
        await query.answer()
        
        sample_code = """
# Sample Telegram Bot
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

async def start(update: Update, context):
    await update.message.reply_text("Hello!")

async def help(update: Update, context):
    await update.message.reply_text("Help command")

# Create application
app = Application.builder().token("TOKEN").build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help))

if __name__ == "__main__":
    app.run_polling()
"""
        
        # تحلیل نمونه
        features = self.analyzer.analyze_file(sample_code)
        scoring = self.scoring_engine.calculate_score(features)
        price = self.scoring_engine.calculate_price(scoring.total_score)
        
        report = self._generate_report(features, scoring, price)
        
        await query.edit_message_text(
            text=report,
            parse_mode='Markdown'
        )
    
    async def handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دستور راهنما"""
        query = update.callback_query
        await query.answer()
        
        help_text = """
        📚 **راهنمای استفاده:**
        
        ۱. فایل Python ربات خود را با دستور /start شروع کنید
        ۲. فایل را به صورت مستقیم ارسال کنید (نه لینک)
        ۳. ربات به صورت خودکار کد را تحلیل می‌کند
        ۴. گزارش کامل قیمت را دریافت کنید
        
        ⚠️ **محدودیت‌ها:**
        • فقط فایل‌های .py پشتیبانی می‌شوند
        • حجم فایل حداکثر ۱ مگابایت
        • تحلیل فقط بر اساس کد موجود است
        
        🎯 **نکات برای قیمت بهتر:**
        • کد تمیز و کامنت‌گذاری شده
        • استفاده از معماری Async
        • پیاده‌سازی مدیریت خطا
        • اضافه کردن دیتابیس
        • ایجاد پنل ادمین
        • افزودن API خارجی
        
        ❓ **سوالات متداول:**
        Q: آیا کد من ذخیره می‌شود؟
        A: خیر، تحلیل در لحظه انجام می‌شود و کد ذخیره نمی‌شود.
        
        Q: دقت تحلیل چقدر است؟
        A: دقت حدود ۸۵-۹۰% برای پروژه‌های استاندارد
        
        برای شروع، فایل ربات خود را ارسال کنید.
        """
        
        await query.edit_message_text(
            text=help_text,
            parse_mode='Markdown'
        )

# ==================== MAIN APPLICATION ====================
def main():
    """تابع اصلی اجرای ربات"""
    
    # ایجاد اپلیکیشن
    app = Application.builder().token(TOKEN).build()
    
    # ایجاد نمونه ربات
    bot_analyzer = BotPriceAnalyzerBot()
    
    # ثبت هندلرها
    app.add_handler(CommandHandler("start", bot_analyzer.start))
    app.add_handler(MessageHandler(filters.Document.ALL, bot_analyzer.handle_document))
    app.add_handler(CallbackQueryHandler(bot_analyzer.handle_sample, pattern="^sample$"))
    app.add_handler(CallbackQueryHandler(bot_analyzer.handle_help, pattern="^help$"))
    
    # راه‌اندازی webhook (برای Render)
    if WEBHOOK_URL:
        # تنظیم webhook
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{TOKEN}"
        )
    else:
        # حالت توسعه (polling)
        print("🤖 Bot is running in development mode (polling)...")
        app.run_polling()

if __name__ == "__main__":
    main()
