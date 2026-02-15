#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    🤖 TELEGRAM BOT PRICE ANALYZER PRO MAX                      ║
║                         Version: 20.0 - Enterprise Edition                     ║
║                    Powered by Advanced AI & Machine Learning                   ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import re
import sys
import ast
import json
import time
import uuid
import hashlib
import asyncio
import logging
import threading
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler

# ==================== FIXED LOGGING ====================
# ساده‌ترین و مطمئن‌ترین روش logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)
logger.info("✅ Logging system initialized")

# ==================== CONFIGURATION ====================
TOKEN = os.environ.get("BOT_TOKEN", "")
PORT = int(os.environ.get("PORT", 8443))
ENVIRONMENT = os.environ.get("ENVIRONMENT", "production")
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"

if not TOKEN:
    logger.critical("❌ BOT_TOKEN is not set! Exiting...")
    sys.exit(1)

# ==================== TELEGRAM IMPORTS ====================
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
    from telegram.error import Conflict, TimedOut, NetworkError
    logger.info("✅ Telegram library imported successfully")
except ImportError as e:
    logger.critical(f"❌ Import error: {e}")
    sys.exit(1)

# ==================== SIMPLE ENUMS ====================
class BotCategory:
    ECOMMERCE = "🛍️ فروشگاه آنلاین"
    EDUCATIONAL = "📚 آموزشی و درسی"
    GROUP_MANAGEMENT = "👑 مدیریت گروه"
    ENTERTAINMENT = "🎮 سرگرمی و بازی"
    NEWS = "📰 اخبار و اطلاع‌رسانی"
    UTILITY = "⚙️ سرویس و ابزار"
    FINANCIAL = "💰 مالی و حسابداری"
    CUSTOM = "✨ سفارشی"

# ==================== SIMPLE DATA MODEL ====================
class BotAnalysis:
    """مدل ساده و کارآمد"""
    
    def __init__(self, filename=""):
        self.id = str(uuid.uuid4())[:8]
        self.filename = filename
        self.timestamp = datetime.now()
        
        # Basic info
        self.total_lines = 0
        self.code_lines = 0
        self.comment_lines = 0
        
        # Features
        self.features = []
        self.technologies = []
        
        # Bot type
        self.category = BotCategory.CUSTOM
        self.confidence = 0.0
        self.reasons = []
        
        # Price
        self.base_price = 0
        self.final_price = 0
        self.price_factors = {}
        
        # Security
        self.security_issues = []
        self.security_score = 100

# ==================== AST ANALYZER ====================
class ASTAnalyzer:
    """تحلیل‌گر AST ساده"""
    
    @staticmethod
    def analyze(code: str) -> Dict:
        try:
            tree = ast.parse(code)
            functions = []
            classes = []
            imports = []
            async_functions = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
                elif isinstance(node, ast.AsyncFunctionDef):
                    async_functions.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    for alias in node.names:
                        imports.append(alias.name)
            
            return {
                "functions": functions,
                "classes": classes,
                "imports": imports,
                "async_functions": async_functions,
                "has_error_handling": 'try' in code
            }
        except:
            return {}

# ==================== BOT DETECTOR ====================
class BotDetector:
    """تشخیص‌گر ساده و دقیق"""
    
    CATEGORY_KEYWORDS = {
        BotCategory.ECOMMERCE: {
            "primary": ["سبد خرید", "پرداخت", "محصول", "فروش", "قیمت", "خرید", "zarinpal", "idpay"],
            "secondary": ["سفارش", "موجودی", "تخفیف"]
        },
        BotCategory.EDUCATIONAL: {
            "primary": ["آزمون", "سوال", "نمره", "آموزش", "دوره", "quiz", "exam"],
            "secondary": ["تمرین", "پاسخ", "کلاس"]
        },
        BotCategory.GROUP_MANAGEMENT: {
            "primary": ["اخراج", "مسدود", "اخطار", "فیلتر", "kick", "ban", "warn"],
            "secondary": ["خوش آمد", "اعضا", "مدیریت"]
        },
        BotCategory.ENTERTAINMENT: {
            "primary": ["بازی", "حدس", "شانس", "مسابقه", "game", "play"],
            "secondary": ["امتیاز", "لول", "برنده"]
        }
    }
    
    @staticmethod
    def detect(code: str) -> Tuple[str, float, List[str]]:
        code_lower = code.lower()
        scores = {}
        reasons = []
        
        for category, keywords in BotDetector.CATEGORY_KEYWORDS.items():
            score = 0
            for kw in keywords["primary"]:
                if kw.lower() in code_lower:
                    count = code_lower.count(kw.lower())
                    score += count * 10
                    if count > 0:
                        reasons.append(f"کلمه کلیدی '{kw}' ({count} بار)")
            
            for kw in keywords.get("secondary", []):
                if kw.lower() in code_lower:
                    score += code_lower.count(kw.lower()) * 5
            
            if score > 0:
                scores[category] = score
        
        if scores:
            best = max(scores.items(), key=lambda x: x[1])
            confidence = min(best[1] / 100, 0.95)
            return best[0], confidence, reasons[:3]
        
        return BotCategory.CUSTOM, 0.3, ["الگوی خاصی یافت نشد"]

# ==================== FEATURE EXTRACTOR ====================
class FeatureExtractor:
    """استخراج ویژگی‌ها"""
    
    FEATURES = [
        (r"InlineKeyboardMarkup", "کیبورد اینلاین"),
        (r"ReplyKeyboardMarkup", "کیبورد معمولی"),
        (r"CallbackQueryHandler", "دکمه‌های تعاملی"),
        (r"ConversationHandler", "مکالمه چندمرحله‌ای"),
        (r"async def", "Async Programming"),
        (r"class ", "برنامه‌نویسی شی‌گرا"),
        (r"try:.*except", "مدیریت خطا"),
        (r"logging", "سیستم لاگ"),
        (r"sqlite|mysql|postgres", "دیتابیس"),
        (r"zarinpal|idpay|payment", "درگاه پرداخت"),
        (r"requests|httpx", "API خارجی"),
        (r"job_queue", "زمان‌بندی خودکار")
    ]
    
    @staticmethod
    def extract(code: str) -> List[str]:
        features = []
        for pattern, name in FeatureExtractor.FEATURES:
            if re.search(pattern, code, re.IGNORECASE):
                features.append(name)
        return list(set(features))

# ==================== PRICE CALCULATOR ====================
class PriceCalculator:
    """محاسبه قیمت هوشمند"""
    
    BASE_PRICES = {
        BotCategory.ECOMMERCE: 5_000_000,
        BotCategory.EDUCATIONAL: 3_500_000,
        BotCategory.GROUP_MANAGEMENT: 2_500_000,
        BotCategory.ENTERTAINMENT: 3_000_000,
        BotCategory.NEWS: 2_000_000,
        BotCategory.UTILITY: 2_500_000,
        BotCategory.FINANCIAL: 6_000_000,
        BotCategory.CUSTOM: 4_000_000
    }
    
    @staticmethod
    def calculate(analysis: BotAnalysis) -> BotAnalysis:
        # قیمت پایه
        base = PriceCalculator.BASE_PRICES.get(analysis.category, 4_000_000)
        analysis.base_price = base
        analysis.price_factors["base"] = 1.0
        
        # ضریب خطوط کد
        line_factor = 1.0
        if analysis.code_lines > 500:
            line_factor = 1.5
        elif analysis.code_lines > 300:
            line_factor = 1.3
        elif analysis.code_lines > 200:
            line_factor = 1.2
        elif analysis.code_lines > 100:
            line_factor = 1.1
        
        # ضریب ویژگی‌ها
        feature_factor = 1.0 + (len(analysis.features) * 0.05)
        feature_factor = min(feature_factor, 2.0)
        
        # ضریب اعتماد
        confidence_factor = 0.8 + (analysis.confidence * 0.4)
        
        # ضریب امنیت
        security_factor = 1.0 + (analysis.security_score / 200)
        
        # محاسبه نهایی
        analysis.price_factors.update({
            "lines": line_factor,
            "features": feature_factor,
            "confidence": confidence_factor,
            "security": security_factor
        })
        
        final = base
        for factor in analysis.price_factors.values():
            final *= factor
        
        # محدودیت‌ها
        min_price = 500_000
        max_price = 50_000_000
        analysis.final_price = max(min_price, min(int(final), max_price))
        
        return analysis

# ==================== SECURITY ANALYZER ====================
class SecurityAnalyzer:
    """تحلیل امنیتی ساده"""
    
    VULNERABILITIES = [
        (r"eval\(.*\)", "استفاده از eval (خطرناک)"),
        (r"exec\(.*\)", "استفاده از exec (خطرناک)"),
        (r"os\.system", "دستورات سیستمی"),
        (r"subprocess\.call", "اجرای فرمان خارجی"),
        (r"password\s*=\s*['\"][^'\"]+['\"]", "پسورد hardcoded"),
        (r"api_key\s*=\s*['\"][^'\"]+['\"]", "API key hardcoded"),
        (r"token\s*=\s*['\"][^'\"]+['\"]", "توکن hardcoded")
    ]
    
    @staticmethod
    def analyze(code: str) -> Tuple[int, List[str]]:
        issues = []
        score = 100
        
        for pattern, desc in SecurityAnalyzer.VULNERABILITIES:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append(desc)
                score -= 15
        
        return max(score, 0), issues

# ==================== HTTP SERVER ====================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ['/', '/health', '/ping']:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                "status": "online",
                "service": "bot-price-analyzer",
                "version": "20.0",
                "time": datetime.now().isoformat()
            }
            
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Disable HTTP logs

def run_http_server():
    try:
        server = HTTPServer(('0.0.0.0', PORT), HealthHandler)
        logger.info(f"✅ HTTP Server running on port {PORT}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"❌ HTTP Server error: {e}")

# ==================== MAIN BOT ====================
class PriceAnalyzerBot:
    """ربات اصلی تحلیلگر قیمت"""
    
    def __init__(self):
        self.ast_analyzer = ASTAnalyzer()
        self.detector = BotDetector()
        self.price_calc = PriceCalculator()
        self.security = SecurityAnalyzer()
        self.feature_extractor = FeatureExtractor()
        
        self.processing_users = set()
        self.stats = {
            'files_received': 0,
            'analyses_done': 0,
            'errors': 0
        }
        
        logger.info("✅ Bot initialized")
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        
        welcome = f"""
🤖 **ربات تحلیل‌گر حرفه‌ای قیمت ربات تلگرام**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👋 سلام {user.first_name}!

✨ **قابلیت‌ها:**
• تحلیل AST کد Python
• تشخیص هوشمند نوع ربات
• شناسایی ۱۲+ ویژگی
• محاسبه قیمت دقیق
• تحلیل امنیتی

📁 **نحوه استفاده:**
۱. فایل `.py` ربات خود را ارسال کنید
۲. منتظر تحلیل باشید (۱۰-۲۰ ثانیه)
۳. گزارش کامل دریافت کنید

👇 **فایل خود را ارسال کنید:**
        """
        
        keyboard = [[InlineKeyboardButton("📋 نمونه", callback_data="sample")]]
        await update.message.reply_text(welcome, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    
    async def handle_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        if user_id in self.processing_users:
            await update.message.reply_text("⏳ در حال پردازش...")
            return
        
        if not update.message.document:
            return
        
        doc = update.message.document
        if not doc.file_name.endswith('.py'):
            await update.message.reply_text("❌ فقط فایل‌های .py")
            return
        
        self.processing_users.add(user_id)
        self.stats['files_received'] += 1
        
        try:
            msg = await update.message.reply_text("📥 دریافت فایل...")
            
            # Download
            file = await doc.get_file()
            content_bytes = await file.download_as_bytearray()
            content = content_bytes.decode('utf-8', errors='ignore')
            
            await msg.edit_text("🔍 تحلیل کد...")
            
            # Create analysis object
            analysis = BotAnalysis(doc.file_name)
            lines = content.split('\n')
            analysis.total_lines = len(lines)
            analysis.code_lines = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
            analysis.comment_lines = len([l for l in lines if l.strip().startswith('#')])
            
            # AST Analysis
            ast_data = self.ast_analyzer.analyze(content)
            
            # Detect type
            category, confidence, reasons = self.detector.detect(content)
            analysis.category = category
            analysis.confidence = confidence
            analysis.reasons = reasons
            
            # Extract features
            analysis.features = self.feature_extractor.extract(content)
            
            # Security
            sec_score, sec_issues = self.security.analyze(content)
            analysis.security_score = sec_score
            analysis.security_issues = sec_issues
            
            # Calculate price
            analysis = self.price_calc.calculate(analysis)
            
            # Generate report
            report = self.generate_report(analysis)
            
            await msg.delete()
            await update.message.reply_text(report, parse_mode='Markdown')
            
            self.stats['analyses_done'] += 1
            logger.info(f"✅ Analysis done: {doc.file_name}")
            
        except Exception as e:
            logger.error(f"Error: {e}")
            await update.message.reply_text("❌ خطا در پردازش")
            self.stats['errors'] += 1
        
        finally:
            self.processing_users.discard(user_id)
    
    def generate_report(self, a: BotAnalysis) -> str:
        """تولید گزارش"""
        now = a.timestamp.strftime("%Y/%m/%d %H:%M")
        
        report = f"""
📄 **گزارش تحلیل حرفه‌ای ربات تلگرام**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 فایل: {a.filename}
⏰ زمان: {now}
🆔 شناسه: {a.id}

🎯 **تشخیص نوع ربات:**
• {a.category}
• اطمینان: {a.confidence*100:.0f}%
"""
        
        if a.reasons:
            report += "• دلایل:\n"
            for r in a.reasons:
                report += f"  └ {r}\n"
        
        report += f"""
✨ **ویژگی‌ها: ({len(a.features)} مورد)**
"""
        for f in a.features[:8]:
            report += f"• ✅ {f}\n"
        
        if len(a.features) > 8:
            report += f"• ... و {len(a.features)-8} مورد دیگر\n"
        
        report += f"""
📊 **آمار کد:**
• کل خطوط: {a.total_lines}
• خطوط کد: {a.code_lines}
• کامنت: {a.comment_lines}

🛡️ **امنیت: {a.security_score}/100**
"""
        if a.security_issues:
            for issue in a.security_issues[:3]:
                report += f"• ⚠️ {issue}\n"
        else:
            report += "• ✅ بدون مشکل امنیتی\n"
        
        report += f"""
💰 **قیمت:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💵 ریال: **{a.final_price:,} ریال**
💳 تومان: **{a.final_price//10:,} تومان**
💲 دلار: **${a.final_price/50_000:.2f}**

⚖️ **فاکتورها:**
"""
        for name, val in a.price_factors.items():
            report += f"• {name}: {val:.2f}x\n"
        
        report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 ربات تحلیل‌گر - نسخه ۲۰.۰
        """
        
        return report
    
    async def sample(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        text = """
📋 **نمونه گزارش:**

🎯 **تشخیص:** فروشگاه آنلاین
✨ **ویژگی‌ها:**
• کیبورد اینلاین
• دستورات سفارشی
• دیتابیس SQLite
• درگاه پرداخت

💰 **قیمت:** ۴,۵۰۰,۰۰۰ ریال

👇 **ربات خود را تحلیل کنید!**
        """
        
        keyboard = [[InlineKeyboardButton("📤 ارسال فایل", callback_data="send")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

# ==================== MAIN ====================
async def run_bot():
    """اجرای اصلی"""
    logger.info("="*50)
    logger.info("🤖 Starting Telegram Bot Price Analyzer v20.0")
    logger.info("="*50)
    
    try:
        # Create bot
        bot = PriceAnalyzerBot()
        
        # Create application
        app = Application.builder().token(TOKEN).build()
        
        # Add handlers
        app.add_handler(CommandHandler("start", bot.start))
        app.add_handler(CommandHandler("help", bot.start))
        app.add_handler(MessageHandler(filters.Document.ALL, bot.handle_file))
        app.add_handler(CallbackQueryHandler(bot.sample, pattern="^sample$"))
        app.add_handler(CallbackQueryHandler(bot.start, pattern="^send$"))
        
        # Clear webhook
        from telegram import Bot
        temp = Bot(token=TOKEN)
        await temp.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook cleared")
        
        await asyncio.sleep(2)
        
        # Start polling
        await app.initialize()
        await app.start()
        await app.updater.start_polling(
            drop_pending_updates=True,
            timeout=30,
            poll_interval=0.5
        )
        
        logger.info("✅ Bot is running!")
        logger.info("🎯 Ready to analyze files...")
        
        # Keep running
        await asyncio.Event().wait()
        
    except Conflict as e:
        logger.error(f"Conflict: {e}")
        await asyncio.sleep(30)
        raise
    except Exception as e:
        logger.error(f"Error: {e}")
        raise

def main():
    """Main entry point"""
    # Start HTTP server
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    
    # Run bot
    while True:
        try:
            asyncio.run(run_bot())
        except KeyboardInterrupt:
            logger.info("👋 Bot stopped")
            break
        except Exception as e:
            logger.error(f"Bot crashed: {e}")
            logger.info("🔄 Restarting in 10 seconds...")
            time.sleep(10)

if __name__ == "__main__":
    main()
