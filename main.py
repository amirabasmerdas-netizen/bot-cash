#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    🤖 TELEGRAM BOT PRICE ANALYZER FINAL                        ║
║                         Version: 28.0 - Render Ready                          ║
║                    Webhook Mode - No Conflict Guaranteed                       ║
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
import signal
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass, field

# ==================== CONFIGURATION ====================
TOKEN = os.environ.get("BOT_TOKEN", "")
PORT = int(os.environ.get("PORT", 8443))
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL", "")
ENVIRONMENT = os.environ.get("ENVIRONMENT", "production")
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"

if not TOKEN:
    print("❌ BOT_TOKEN is not set!")
    sys.exit(1)

if not RENDER_EXTERNAL_URL and ENVIRONMENT == "production":
    print("⚠️ RENDER_EXTERNAL_URL not set, webhook may not work")

# ==================== LOGGING ====================
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ==================== TELEGRAM IMPORTS ====================
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        Application,
        CommandHandler,
        MessageHandler,
        ContextTypes,
        filters
    )
    from telegram.error import Conflict, TimedOut, NetworkError
    from telegram.constants import ParseMode
    logger.info("✅ Telegram library imported")
except ImportError as e:
    logger.error(f"❌ Import error: {e}")
    sys.exit(1)

# ==================== WEBHOOK SETUP ====================
async def setup_webhook(application: Application) -> bool:
    """تنظیم webhook برای Render"""
    try:
        if not RENDER_EXTERNAL_URL:
            logger.warning("⚠️ RENDER_EXTERNAL_URL not set, using polling")
            return False
        
        webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
        logger.info(f"🌐 Setting webhook to: {webhook_url}")
        
        # Delete any existing webhook/polling
        await application.bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Previous webhook deleted")
        
        # Set new webhook
        await application.bot.set_webhook(
            url=webhook_url,
            allowed_updates=["message", "callback_query"],
            max_connections=1,
            drop_pending_updates=True
        )
        
        # Verify webhook
        webhook_info = await application.bot.get_webhook_info()
        logger.info(f"✅ Webhook set: {webhook_info.url}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Webhook setup failed: {e}")
        return False

# ==================== ENUMS ====================
class BotCategory:
    CATEGORIES = {
        "ECOMMERCE": ("🛍️ فروشگاه آنلاین", 5_000_000),
        "EDUCATIONAL": ("📚 آموزشی", 3_500_000),
        "GROUP_MANAGEMENT": ("👑 مدیریت گروه", 2_500_000),
        "ENTERTAINMENT": ("🎮 سرگرمی", 3_000_000),
        "NEWS": ("📰 اخبار", 2_000_000),
        "UTILITY": ("⚙️ ابزار", 2_500_000),
        "FINANCIAL": ("💰 مالی", 6_000_000),
        "CRYPTO": ("₿ ارز دیجیتال", 8_000_000),
        "CUSTOM": ("✨ سفارشی", 4_000_000)
    }
    
    @classmethod
    def detect(cls, code: str) -> Tuple[str, str, float, int]:
        code_lower = code.lower()
        scores = {}
        
        for cat_id, (name, price) in cls.CATEGORIES.items():
            score = 0
            keywords = {
                "ECOMMERCE": ["خرید", "فروش", "محصول", "پرداخت", "zarinpal"],
                "EDUCATIONAL": ["آموزش", "درس", "آزمون", "quiz", "exam"],
                "GROUP_MANAGEMENT": ["مدیریت", "گروه", "kick", "ban", "admin"],
                "ENTERTAINMENT": ["بازی", "game", "سرگرمی", "امتیاز"],
                "NEWS": ["اخبار", "news", "اطلاعیه"],
                "UTILITY": ["ابزار", "tool", "تبدیل", "دانلود"],
                "FINANCIAL": ["مالی", "کیف پول", "wallet", "پول"],
                "CRYPTO": ["بیت‌کوین", "crypto", "bitcoin", "ارز"]
            }.get(cat_id, [])
            
            for kw in keywords:
                if kw in code_lower:
                    score += 10
            
            if score > 0:
                scores[cat_id] = score
        
        if scores:
            best = max(scores.items(), key=lambda x: x[1])
            cat_id, score = best
            name, price = cls.CATEGORIES[cat_id]
            confidence = min(score / 100, 0.95)
            return cat_id, name, confidence, price
        
        return "CUSTOM", "✨ سفارشی", 0.3, 4_000_000

# ==================== FEATURE DETECTOR ====================
class FeatureDetector:
    FEATURES = [
        (r"InlineKeyboardMarkup", "کیبورد اینلاین"),
        (r"CallbackQueryHandler", "دکمه‌های تعاملی"),
        (r"ConversationHandler", "مکالمه چندمرحله‌ای"),
        (r"async def", "Async Programming"),
        (r"class\s+\w+", "شی‌گرایی"),
        (r"try:.*except", "مدیریت خطا"),
        (r"sqlite|mysql|postgres", "دیتابیس"),
        (r"zarinpal|idpay|payment", "درگاه پرداخت"),
        (r"requests|httpx", "API خارجی")
    ]
    
    @classmethod
    def detect(cls, code: str) -> List[str]:
        features = []
        for pattern, name in cls.FEATURES:
            if re.search(pattern, code, re.IGNORECASE):
                features.append(name)
        return list(set(features))

# ==================== SECURITY ANALYZER ====================
class SecurityAnalyzer:
    VULNS = [
        (r"eval\(.*\)", "استفاده از eval"),
        (r"exec\(.*\)", "استفاده از exec"),
        (r"os\.system\(", "دستورات سیستمی"),
        (r"password\s*=\s*['\"][^'\"]+['\"]", "پسورد hardcoded")
    ]
    
    @classmethod
    def analyze(cls, code: str) -> Dict:
        issues = []
        score = 100
        
        for pattern, desc in cls.VULNS:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append(desc)
                score -= 20
        
        return {
            "score": max(score, 0),
            "issues": issues[:3]
        }

# ==================== PRICE CALCULATOR ====================
class PriceCalculator:
    @classmethod
    def calculate(cls, base_price: int, features: List[str], lines: int, confidence: float) -> Dict:
        price = base_price
        
        # Feature factor
        price *= (1 + len(features) * 0.05)
        
        # Size factor
        if lines > 500:
            price *= 1.5
        elif lines > 300:
            price *= 1.3
        elif lines > 200:
            price *= 1.2
        elif lines > 100:
            price *= 1.1
        
        # Confidence factor
        price *= (0.8 + confidence * 0.4)
        
        # Apply limits
        price = max(500_000, min(int(price), 50_000_000))
        
        # Score
        score = int((price / base_price) * 50)
        score = min(score, 100)
        
        # Level
        if score >= 80:
            level = "🏆 حرفه‌ای"
        elif score >= 60:
            level = "⭐ پیشرفته"
        elif score >= 40:
            level = "📱 استاندارد"
        else:
            level = "🛠️ ساده"
        
        return {
            "price": price,
            "toman": price // 10,
            "usd": round(price / 50_000, 2),
            "score": score,
            "level": level
        }

# ==================== REPORT GENERATOR ====================
class ReportGenerator:
    @classmethod
    def generate(cls, filename: str, category: str, features: List[str], 
                 lines: int, security: Dict, price: Dict) -> str:
        
        features_text = "\n".join([f"• ✅ {f}" for f in features[:8]])
        if len(features) > 8:
            features_text += f"\n• ... و {len(features)-8} مورد دیگر"
        
        issues_text = "\n".join([f"• ⚠️ {i}" for i in security['issues'][:3]]) or "• ✅ بدون مشکل"
        
        return f"""
╔══════════════════════════════════════════════════════════════════╗
║              📄 **گزارش تحلیل ربات تلگرام**                       ║
╚══════════════════════════════════════════════════════════════════╝

📁 فایل: `{filename}`
⏰ زمان: {datetime.now().strftime("%Y/%m/%d %H:%M")}

🎯 **نوع ربات:** {category}
📊 **خطوط کد:** {lines} خط

✨ **ویژگی‌ها:**
{features_text}

🛡️ **امنیت:** {security['score']}/100
{issues_text}

💰 **قیمت:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏆 امتیاز: {price['score']}/100
🎯 سطح: {price['level']}

💵 ریال: **{price['price']:,} ریال**
💳 تومان: **{price['toman']:,} تومان**
💲 دلار: **${price['usd']}**

╔══════════════════════════════════════════════════════════════════╗
║              🤖 Telegram Price Analyzer - v28.0                   ║
╚══════════════════════════════════════════════════════════════════╝
"""

# ==================== BOT HANDLERS ====================
class BotHandlers:
    def __init__(self):
        self.processing = set()
        self.stats = {
            "start_time": time.time(),
            "files": 0,
            "analyses": 0,
            "errors": 0
        }
        logger.info("✅ Bot handlers initialized")
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        
        uptime = time.time() - self.stats["start_time"]
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        
        text = f"""
👋 سلام {user.first_name}!

🤖 **ربات تحلیل‌گر قیمت تلگرام v28.0**

📁 **نحوه استفاده:**
1️⃣ فایل `.py` ربات خود را ارسال کنید
2️⃣ منتظر تحلیل باشید
3️⃣ گزارش کامل دریافت کنید

📊 **آمار:**
• تحلیل‌ها: {self.stats['analyses']}
• فایل‌ها: {self.stats['files']}
• آپتایم: {hours:02d}:{minutes:02d}

⚠️ **حداکثر حجم فایل: 5MB**

👇 **فایل خود را ارسال کنید:**
        """
        
        await update.message.reply_text(text)
    
    async def handle_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        if user_id in self.processing:
            await update.message.reply_text("⏳ در حال پردازش...")
            return
        
        if not update.message.document:
            return
        
        doc = update.message.document
        if not doc.file_name.endswith('.py'):
            await update.message.reply_text("❌ فقط فایل‌های .py مجاز هستند")
            return
        
        self.processing.add(user_id)
        self.stats['files'] += 1
        
        try:
            msg = await update.message.reply_text("📥 دریافت فایل...")
            
            # Download
            file = await doc.get_file()
            content = (await file.download_as_bytearray()).decode('utf-8', errors='ignore')
            
            # Check size
            if len(content) > 5 * 1024 * 1024:
                await msg.edit_text("❌ فایل بسیار بزرگ است!")
                return
            
            await msg.edit_text("🔍 تحلیل...")
            
            # Count lines
            lines = len([l for l in content.split('\n') if l.strip()])
            
            # Detect type
            cat_id, cat_name, confidence, base_price = BotCategory.detect(content)
            
            # Features
            features = FeatureDetector.detect(content)
            
            # Security
            security = SecurityAnalyzer.analyze(content)
            
            # Price
            price = PriceCalculator.calculate(base_price, features, lines, confidence)
            
            # Report
            report = ReportGenerator.generate(
                doc.file_name, cat_name, features, lines, security, price
            )
            
            await msg.delete()
            await update.message.reply_text(report)
            
            self.stats['analyses'] += 1
            logger.info(f"✅ {doc.file_name} -> {cat_name}")
            
        except Exception as e:
            logger.error(f"Error: {e}")
            self.stats['errors'] += 1
            await update.message.reply_text("❌ خطا در پردازش")
        
        finally:
            self.processing.discard(user_id)

# ==================== APPLICATION SETUP ====================
async def create_application() -> Application:
    """ایجاد و تنظیم اپلیکیشن"""
    app = Application.builder().token(TOKEN).build()
    handlers = BotHandlers()
    
    app.add_handler(CommandHandler("start", handlers.start))
    app.add_handler(CommandHandler("help", handlers.start))
    app.add_handler(MessageHandler(filters.Document.ALL, handlers.handle_file))
    
    return app, handlers

# ==================== WEBHOOK SERVER ====================
from aiohttp import web

async def webhook_handler(request):
    """Handler برای webhook تلگرام"""
    try:
        json_data = await request.json()
        update = Update.de_json(json_data, app.bot)
        await app.process_update(update)
        return web.Response(status=200)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return web.Response(status=500)

async def health_handler(request):
    """Health check برای Render"""
    return web.json_response({
        "status": "healthy",
        "version": "28.0",
        "timestamp": datetime.now().isoformat()
    })

async def setup_web_server(application: Application):
    """راه‌اندازی سرور وب برای webhook"""
    global app
    app = application
    
    web_app = web.Application()
    web_app.router.add_post('/webhook', webhook_handler)
    web_app.router.add_get('/health', health_handler)
    web_app.router.add_get('/', health_handler)
    
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    
    logger.info(f"✅ Web server running on port {PORT}")
    return runner

# ==================== MAIN ====================
async def main():
    """تابع اصلی"""
    
    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║        🤖 TELEGRAM BOT PRICE ANALYZER - v28.0                     ║
║                    Webhook Mode - No Conflict                     ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        # Create application
        global app
        app, handlers = await create_application()
        
        # Initialize
        await app.initialize()
        await app.start()
        
        # Setup webhook
        if RENDER_EXTERNAL_URL:
            webhook_url = f"{RENDER_EXTERNAL_URL}/webhook"
            await app.bot.delete_webhook(drop_pending_updates=True)
            await asyncio.sleep(1)
            await app.bot.set_webhook(url=webhook_url)
            logger.info(f"✅ Webhook set to: {webhook_url}")
        else:
            logger.warning("⚠️ No webhook URL, using polling")
            await app.updater.start_polling()
        
        # Start web server
        runner = await setup_web_server(app)
        
        logger.info("✅ Bot is running!")
        logger.info(f"📊 Stats: {handlers.stats}")
        
        # Keep running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("👋 Shutting down...")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
    finally:
        if 'runner' in locals():
            await runner.cleanup()
        await app.stop()
        await app.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
