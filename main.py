#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║              🤖 TELEGRAM BOT PRICE ANALYZER - ULTIMATE EDITION                 ║
║                         Version: 21.0 - Conflict Free                          ║
║                    With Auto-Restart & Smart Recovery                          ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import re
import sys
import ast
import json
import time
import uuid
import asyncio
import logging
import threading
import signal
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler

# ==================== SIMPLE LOGGING ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ==================== CONFIGURATION ====================
TOKEN = os.environ.get("BOT_TOKEN", "")
PORT = int(os.environ.get("PORT", 8443))
MAX_RETRIES = 10
RETRY_DELAY = 10  # seconds

if not TOKEN:
    logger.critical("❌ BOT_TOKEN is not set!")
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
    logger.info("✅ Telegram library imported")
except ImportError as e:
    logger.critical(f"❌ Import error: {e}")
    sys.exit(1)

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
                "version": "21.0",
                "time": datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

def run_http_server():
    """HTTP server in separate thread"""
    try:
        server = HTTPServer(('0.0.0.0', PORT), HealthHandler)
        logger.info(f"✅ HTTP Server running on port {PORT}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"❌ HTTP Server error: {e}")

# ==================== BOT DETECTOR ====================
class BotDetector:
    """تشخیص نوع ربات"""
    
    CATEGORIES = {
        "🛍️ فروشگاه آنلاین": {
            "primary": ["سبد خرید", "پرداخت", "محصول", "فروش", "خرید", "zarinpal", "idpay"],
            "secondary": ["سفارش", "قیمت", "تخفیف"],
            "base_price": 5_000_000
        },
        "📚 آموزشی": {
            "primary": ["آزمون", "سوال", "نمره", "آموزش", "quiz", "exam"],
            "secondary": ["تمرین", "پاسخ", "کلاس"],
            "base_price": 3_500_000
        },
        "👑 مدیریت گروه": {
            "primary": ["اخراج", "مسدود", "اخطار", "فیلتر", "kick", "ban", "warn"],
            "secondary": ["خوش آمد", "اعضا"],
            "base_price": 2_500_000
        },
        "🎮 سرگرمی": {
            "primary": ["بازی", "حدس", "شانس", "مسابقه", "game"],
            "secondary": ["امتیاز", "لول", "برنده"],
            "base_price": 3_000_000
        },
        "✨ سفارشی": {
            "primary": [],
            "secondary": [],
            "base_price": 4_000_000
        }
    }
    
    @staticmethod
    def detect(code: str) -> Tuple[str, float, int]:
        code_lower = code.lower()
        scores = {}
        
        for name, data in BotDetector.CATEGORIES.items():
            score = 0
            for kw in data["primary"]:
                if kw.lower() in code_lower:
                    score += 20
            for kw in data["secondary"]:
                if kw.lower() in code_lower:
                    score += 5
            if score > 0:
                scores[name] = score
        
        if scores:
            best = max(scores.items(), key=lambda x: x[1])
            confidence = min(best[1] / 50, 0.95)
            base_price = BotDetector.CATEGORIES[best[0]]["base_price"]
            return best[0], confidence, base_price
        
        return "✨ سفارشی", 0.3, 4_000_000

# ==================== FEATURE EXTRACTOR ====================
class FeatureExtractor:
    """استخراج ویژگی‌ها"""
    
    FEATURES = [
        (r"InlineKeyboardMarkup", "کیبورد اینلاین"),
        (r"ReplyKeyboardMarkup", "کیبورد معمولی"),
        (r"CallbackQueryHandler", "دکمه‌های تعاملی"),
        (r"ConversationHandler", "مکالمه چندمرحله‌ای"),
        (r"async def", "Async Programming"),
        (r"class ", "شی‌گرایی"),
        (r"try:.*except", "مدیریت خطا"),
        (r"logging", "سیستم لاگ"),
        (r"sqlite|mysql|postgres", "دیتابیس"),
        (r"zarinpal|idpay|payment", "درگاه پرداخت"),
        (r"requests|httpx", "API خارجی")
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
    """محاسبه قیمت"""
    
    @staticmethod
    def calculate(base_price: int, features: List[str], lines: int, confidence: float) -> int:
        price = base_price
        
        # خطوط کد
        if lines > 500:
            price *= 1.5
        elif lines > 300:
            price *= 1.3
        elif lines > 200:
            price *= 1.2
        elif lines > 100:
            price *= 1.1
        
        # ویژگی‌ها
        price *= (1 + len(features) * 0.05)
        
        # اعتماد
        price *= (0.8 + confidence * 0.4)
        
        # محدودیت
        return max(500_000, min(int(price), 50_000_000))

# ==================== CONFLICT MANAGER ====================
class ConflictManager:
    """مدیریت Conflict و Restart"""
    
    def __init__(self):
        self.conflict_count = 0
        self.last_conflict = 0
        self.is_recovering = False
    
    async def handle_conflict(self):
        """مدیریت Conflict"""
        self.conflict_count += 1
        self.last_conflict = time.time()
        
        wait_time = min(30 * (2 ** (self.conflict_count - 1)), 300)
        logger.warning(f"⚠️ Conflict #{self.conflict_count} - Waiting {wait_time}s")
        
        await asyncio.sleep(wait_time)
        
        # پاکسازی کامل
        try:
            from telegram import Bot
            bot = Bot(token=TOKEN)
            await bot.delete_webhook(drop_pending_updates=True)
            logger.info("✅ Webhook cleared after conflict")
            await asyncio.sleep(5)
        except:
            pass
    
    def should_reset(self) -> bool:
        """آیا باید ریست کنیم؟"""
        if self.conflict_count > 5:
            return True
        if time.time() - self.last_conflict > 3600:  # 1 ساعت بدون Conflict
            self.conflict_count = 0
        return False

# ==================== MAIN BOT ====================
class PriceAnalyzerBot:
    """ربات اصلی"""
    
    def __init__(self):
        self.detector = BotDetector()
        self.feature_extractor = FeatureExtractor()
        self.price_calc = PriceCalculator()
        self.conflict_manager = ConflictManager()
        
        self.processing_users = set()
        self.stats = {
            'start': time.time(),
            'files': 0,
            'errors': 0,
            'conflicts': 0
        }
        
        logger.info("✅ Bot initialized")
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        
        text = f"""
🤖 **ربات تحلیل‌گر قیمت ربات تلگرام**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👋 سلام {user.first_name}!

📁 **نحوه استفاده:**
1️⃣ فایل `.py` ربات خود را ارسال کنید
2️⃣ منتظر تحلیل باشید
3️⃣ گزارش کامل دریافت کنید

💰 **قیمت بر اساس:**
• نوع ربات
• ویژگی‌ها
• پیچیدگی کد
• کیفیت کد

👇 **فایل خود را ارسال کنید:**
        """
        
        await update.message.reply_text(text, parse_mode='Markdown')
    
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
        self.stats['files'] += 1
        
        try:
            msg = await update.message.reply_text("📥 دریافت فایل...")
            
            # Download
            file = await doc.get_file()
            content = (await file.download_as_bytearray()).decode('utf-8', errors='ignore')
            lines = len([l for l in content.split('\n') if l.strip()])
            
            await msg.edit_text("🔍 تحلیل...")
            
            # Detect type
            category, confidence, base_price = self.detector.detect(content)
            
            # Extract features
            features = self.feature_extractor.extract(content)
            
            # Calculate price
            final_price = self.price_calc.calculate(base_price, features, lines, confidence)
            
            # Generate report
            report = self._generate_report(
                doc.file_name, category, confidence, 
                features, lines, final_price
            )
            
            await msg.delete()
            await update.message.reply_text(report, parse_mode='Markdown')
            
            logger.info(f"✅ Done: {doc.file_name} - {category}")
            
        except Exception as e:
            logger.error(f"Error: {e}")
            await update.message.reply_text("❌ خطا در پردازش")
            self.stats['errors'] += 1
        
        finally:
            self.processing_users.discard(user_id)
    
    def _generate_report(self, filename: str, category: str, confidence: float, 
                        features: List[str], lines: int, price: int) -> str:
        """تولید گزارش"""
        now = datetime.now().strftime("%Y/%m/%d %H:%M")
        
        report = f"""
📄 **گزارش تحلیل ربات**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 فایل: {filename}
⏰ زمان: {now}

🎯 **نوع ربات:** {category}
📊 **اطمینان:** {confidence*100:.0f}%

✨ **ویژگی‌ها:** ({len(features)})
"""
        for f in features[:8]:
            report += f"• ✅ {f}\n"
        
        if len(features) > 8:
            report += f"• ... و {len(features)-8} مورد دیگر\n"
        
        report += f"""
📈 **آمار:**
• خطوط کد: {lines}
• ویژگی‌ها: {len(features)}

💰 **قیمت:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💵 ریال: **{price:,} ریال**
💳 تومان: **{price//10:,} تومان**
💲 دلار: **${price/50_000:.2f}**

🤖 ربات تحلیل‌گر - نسخه ۲۱.۰
        """
        
        return report

# ==================== CLEANUP FUNCTIONS ====================
async def force_cleanup():
    """پاکسازی اجباری"""
    try:
        import requests
        url = f"https://api.telegram.org/bot{TOKEN}/deleteWebhook"
        response = requests.get(url, params={"drop_pending_updates": "true"})
        logger.info(f"Cleanup result: {response.json()}")
        await asyncio.sleep(5)
    except Exception as e:
        logger.error(f"Cleanup error: {e}")

# ==================== MAIN LOOP ====================
async def run_bot_with_retry():
    """اجرای ربات با قابلیت Retry"""
    
    retry_count = 0
    conflict_mgr = ConflictManager()
    
    while retry_count < MAX_RETRIES:
        try:
            logger.info("="*50)
            logger.info(f"🚀 Starting bot (attempt {retry_count + 1}/{MAX_RETRIES})")
            logger.info("="*50)
            
            # Cleanup first
            await force_cleanup()
            
            # Create bot
            bot = PriceAnalyzerBot()
            
            # Create application
            app = Application.builder().token(TOKEN).build()
            
            # Add handlers
            app.add_handler(CommandHandler("start", bot.start))
            app.add_handler(CommandHandler("help", bot.start))
            app.add_handler(MessageHandler(filters.Document.ALL, bot.handle_file))
            
            # Start
            await app.initialize()
            await app.start()
            await app.updater.start_polling(
                drop_pending_updates=True,
                timeout=30,
                poll_interval=0.5,
                allowed_updates=["message"]
            )
            
            logger.info("✅ Bot is running!")
            logger.info("🎯 Ready to analyze files...")
            
            # Reset retry counter on success
            retry_count = 0
            
            # Keep running
            await asyncio.Event().wait()
            
        except Conflict as e:
            logger.error(f"❌ Conflict: {e}")
            retry_count += 1
            bot.stats['conflicts'] += 1
            
            wait_time = min(30 * retry_count, 300)
            logger.info(f"⏳ Waiting {wait_time}s before retry...")
            await asyncio.sleep(wait_time)
            
            # Force cleanup
            await force_cleanup()
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            retry_count += 1
            await asyncio.sleep(10)
    
    logger.critical("❌ Max retries reached. Exiting...")

# ==================== KEEP ALIVE ====================
async def keep_alive():
    """Keep-alive pings"""
    while True:
        try:
            import requests
            requests.get(f"https://bot-cash.onrender.com/health", timeout=5)
            logger.debug("Keep-alive ping sent")
        except:
            pass
        await asyncio.sleep(240)  # 4 minutes

# ==================== MAIN ====================
def main():
    """Main entry point"""
    # Start HTTP server
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    
    # Handle signals
    def signal_handler(sig, frame):
        logger.info("👋 Shutting down...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run bot
    try:
        asyncio.run(run_bot_with_retry())
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped")
    except Exception as e:
        logger.error(f"Fatal: {e}")

if __name__ == "__main__":
    main()
