#!/usr/bin/env python3
"""
🤖 Telegram Bot Price Analyzer - با Keep-Alive
"""

import os
import re
import sys
import json
import time
import asyncio
import logging
import threading
import requests
from typing import Dict, Any
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# ==================== LOGGING ====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== CONFIG ====================
TOKEN = os.environ.get("BOT_TOKEN", "")
PORT = int(os.environ.get("PORT", 8443))
APP_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://bot-cash.onrender.com")

if not TOKEN:
    logger.error("❌ BOT_TOKEN is not set!")
    sys.exit(1)

# ==================== IMPORT TELEGRAM ====================
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
except ImportError as e:
    logger.error(f"❌ Missing dependency: {e}")
    sys.exit(1)

# ==================== KEEP ALIVE SYSTEM ====================
def keep_alive_ping():
    """سیستم Keep-Alive برای جلوگیری از sleep"""
    while True:
        try:
            # پینگ به health endpoint خودمان
            requests.get(f"{APP_URL}/health", timeout=10)
            logger.debug("✅ Keep-alive ping sent")
        except Exception as e:
            logger.debug(f"⚠️ Keep-alive ping failed: {e}")
        
        # هر 4 دقیقه پینگ بزن (کمتر از 5 دقیقه timeout Render)
        time.sleep(240)

# ==================== HTTP SERVER ====================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ['/', '/health', '/ping', '/status']:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = json.dumps({
                "status": "online",
                "service": "bot-price-analyzer",
                "timestamp": datetime.now().isoformat(),
                "uptime": time.time() - start_time
            })
            self.wfile.write(response.encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        logger.debug(f"HTTP: {self.path}")

def run_http_server():
    """اجرای HTTP Server"""
    server = HTTPServer(('0.0.0.0', PORT), HealthHandler)
    logger.info(f"🌐 HTTP Server running on port {PORT}")
    server.serve_forever()

# ==================== BOT ANALYZER ====================
class BotAnalyzer:
    """تحلیل‌گر ساده"""
    
    @staticmethod
    def analyze(code: str) -> Dict[str, Any]:
        lines = code.split('\n')
        code_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
        
        analysis = {
            "lines": len(code_lines),
            "features": [],
            "type": "سفارشی"
        }
        
        code_lower = code.lower()
        
        # تشخیص نوع
        if any(x in code_lower for x in ['shop', 'store', 'فروش', 'خرید']):
            analysis["type"] = "فروشگاه آنلاین"
        elif any(x in code_lower for x in ['course', 'lesson', 'آموزش', 'درس']):
            analysis["type"] = "آموزشی"
        elif any(x in code_lower for x in ['admin', 'group', 'مدیریت', 'گروه']):
            analysis["type"] = "مدیریت گروه"
        
        # ویژگی‌ها
        if 'InlineKeyboardMarkup' in code:
            analysis["features"].append("کیبورد اینلاین")
        if 'CommandHandler' in code:
            analysis["features"].append("دستورات سفارشی")
        if any(x in code_lower for x in ['sqlite', 'mysql', 'postgres']):
            analysis["features"].append("دیتابیس")
        
        # امتیاز
        score = min(analysis["lines"] // 5, 50) + len(analysis["features"]) * 10
        analysis["score"] = min(score, 100)
        
        return analysis
    
    @staticmethod
    def calculate_price(analysis: Dict[str, Any]) -> Dict[str, Any]:
        score = analysis["score"]
        base_price = 2000000
        price = int(base_price * (0.5 + (score / 100) * 1.5))
        price = max(500000, min(price, 10000000))
        
        return {
            "price_rials": price,
            "price_tomans": price // 10,
            "score": score,
            "type": analysis["type"]
        }

# ==================== BOT HANDLERS ====================
class BotHandlers:
    def __init__(self):
        self.analyzer = BotAnalyzer()
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = """
🤖 **ربات تحلیل‌گر قیمت**

📊 فایل `.py` ربات خود را ارسال کنید
💰 قیمت منصفانه دریافت کنید

👇 فایل را ارسال کنید:
        """
        await update.message.reply_text(text, parse_mode='Markdown')
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message.document:
            return
        
        doc = update.message.document
        if not doc.file_name.endswith('.py'):
            await update.message.reply_text("❌ فقط فایل .py")
            return
        
        try:
            msg = await update.message.reply_text("📥 تحلیل...")
            
            file = await doc.get_file()
            content_bytes = await file.download_as_bytearray()
            content = content_bytes.decode('utf-8', errors='ignore')
            
            analysis = self.analyzer.analyze(content)
            price = self.analyzer.calculate_price(analysis)
            
            report = f"""
📄 **گزارش تحلیل**
━━━━━━━━━━━━━━━━
🎯 نوع: {analysis['type']}
📊 امتیاز: {price['score']}/100
✨ ویژگی‌ها: {len(analysis['features'])} مورد

💰 **قیمت:**
• ریال: {price['price_rials']:,} ریال
• تومان: {price['price_tomans']:,} تومان

🤖 @BotAnalyzer
            """
            
            await context.bot.delete_message(chat_id=msg.chat_id, message_id=msg.message_id)
            await update.message.reply_text(report, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error: {e}")
            await update.message.reply_text("❌ خطا در پردازش")

# ==================== MAIN ====================
start_time = time.time()

async def run_bot():
    """اجرای ربات"""
    logger.info("🤖 راه‌اندازی ربات...")
    
    # پاکسازی قبل از شروع
    try:
        from telegram import Bot
        bot = Bot(token=TOKEN)
        await bot.delete_webhook(drop_pending_updates=True)
        await asyncio.sleep(2)
    except:
        pass
    
    # ایجاد اپلیکیشن
    app = Application.builder().token(TOKEN).build()
    handlers = BotHandlers()
    
    app.add_handler(CommandHandler("start", handlers.start))
    app.add_handler(MessageHandler(filters.Document.ALL, handlers.handle_document))
    
    # شروع polling
    await app.initialize()
    await app.start()
    await app.updater.start_polling(
        drop_pending_updates=True,
        timeout=30,
        poll_interval=1.0,
        allowed_updates=["message"]
    )
    
    logger.info("✅ ربات فعال!")
    await asyncio.Event().wait()

def main():
    """برنامه اصلی"""
    # شروع HTTP Server
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    
    # شروع Keep-Alive
    keep_alive_thread = threading.Thread(target=keep_alive_ping, daemon=True)
    keep_alive_thread.start()
    
    logger.info(f"🌐 Server: {APP_URL}")
    logger.info(f"🚪 Port: {PORT}")
    logger.info("🔄 Keep-alive فعال شد")
    
    # اجرای ربات
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("👋 متوقف شد")
    except Exception as e:
        logger.error(f"❌ خطا: {e}")

if __name__ == "__main__":
    main()
