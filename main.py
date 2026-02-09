#!/usr/bin/env python3
"""
🤖 Telegram Bot Price Analyzer - Auto Reconnect
Version: 14.0 - Connection Recovery
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
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler

# ==================== CONFIG ====================
TOKEN = os.environ.get("BOT_TOKEN", "")
PORT = int(os.environ.get("PORT", 8443))
APP_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://bot-cash.onrender.com")

if not TOKEN:
    print("❌ BOT_TOKEN is not set!")
    sys.exit(1)

# ==================== LOGGING ====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')  # Log to file
    ]
)
logger = logging.getLogger(__name__)

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
    from telegram.error import (
        TimedOut, NetworkError, BadRequest, 
        Conflict, RetryAfter, ChatMigrated
    )
except ImportError as e:
    logger.error(f"Import error: {e}")
    sys.exit(1)

# ==================== CONNECTION MONITOR ====================
class ConnectionMonitor:
    """مانیتور وضعیت اتصال"""
    
    def __init__(self):
        self.last_update_time = time.time()
        self.last_message_time = time.time()
        self.is_connected = False
        self.reconnect_count = 0
        self.max_reconnects = 10
        
    def update_activity(self):
        """آپدیت زمان آخرین فعالیت"""
        self.last_update_time = time.time()
        self.is_connected = True
        
    def check_timeout(self):
        """بررسی timeout اتصال"""
        timeout = 120  # 2 دقیقه
        elapsed = time.time() - self.last_update_time
        return elapsed > timeout
    
    def should_reconnect(self):
        """آیا باید reconnect کنیم؟"""
        return self.check_timeout() and self.reconnect_count < self.max_reconnects
    
    def increment_reconnect(self):
        """شمارنده reconnect افزایش می‌دهد"""
        self.reconnect_count += 1
        return self.reconnect_count

# ==================== HTTP SERVER WITH PING ====================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/ping':
            # پینگ ساده برای keep-alive
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'pong')
            return
            
        elif self.path in ['/', '/health', '/status']:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            status = {
                "status": "online",
                "timestamp": datetime.now().isoformat(),
                "service": "bot-price-analyzer",
                "reconnects": monitor.reconnect_count if 'monitor' in globals() else 0
            }
            
            self.wfile.write(json.dumps(status).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        logger.debug(f"HTTP: {self.path}")

def run_http_server():
    """اجرای HTTP Server"""
    try:
        server = HTTPServer(('0.0.0.0', PORT), HealthHandler)
        logger.info(f"✅ HTTP Server running on port {PORT}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"HTTP Server error: {e}")

# ==================== KEEP ALIVE SYSTEM ====================
def keep_alive_pinger():
    """سیستم Keep-Alive برای جلوگیری از sleep Render"""
    while True:
        try:
            # پینگ به خودمان
            response = requests.get(f"{APP_URL}/ping", timeout=5)
            logger.debug(f"Keep-alive ping: {response.status_code}")
            
            # همچنین پینگ به یک سایت معتبر
            requests.get("https://www.google.com", timeout=5)
            
        except Exception as e:
            logger.debug(f"Keep-alive failed: {e}")
        
        # هر 2 دقیقه پینگ بزن
        time.sleep(120)

# ==================== BOT WITH RECONNECT ====================
class ResilientBot:
    """ربات با قابلیت reconnect خودکار"""
    
    def __init__(self):
        self.app = None
        self.monitor = ConnectionMonitor()
        self.retry_delay = 5
        self.max_retry_delay = 60
        
    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دستور /start"""
        self.monitor.update_activity()
        
        text = """
🤖 **ربات تحلیل‌گر قیمت ربات تلگرام**

✨ **ویژگی‌ها:**
• تحلیل کد Python ربات شما
• تشخیص نوع ربات
• محاسبه قیمت منصفانه
• **اتصال پایدار با auto-reconnect**

📁 **نحوه استفاده:**
۱. فایل `.py` ربات خود را ارسال کنید
۲. منتظر تحلیل باشید (۱۰-۲۰ ثانیه)
۳. گزارش کامل را دریافت کنید

👇 **فایل ربات خود را همین حالا ارسال کنید!**
        """
        
        await update.message.reply_text(text, parse_mode='Markdown')
        logger.info(f"✅ /start sent to {update.effective_user.id}")
    
    async def document_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش فایل"""
        self.monitor.update_activity()
        
        try:
            if not update.message.document:
                return
            
            file_name = update.message.document.file_name or "bot.py"
            
            if not file_name.endswith('.py'):
                await update.message.reply_text("❌ فقط فایل‌های Python (.py)")
                return
            
            # پیام وضعیت
            status_msg = await update.message.reply_text("📥 دریافت و تحلیل فایل...")
            
            # دانلود و تحلیل ساده
            file = await update.message.document.get_file()
            content_bytes = await file.download_as_bytearray()
            content = content_bytes.decode('utf-8', errors='ignore')
            
            lines = len(content.split('\n'))
            
            # تشخیص نوع ساده
            if 'shop' in content.lower() or 'فروش' in content.lower():
                bot_type = "فروشگاه آنلاین"
                price = 3_500_000
            elif 'course' in content.lower() or 'آموزش' in content.lower():
                bot_type = "آموزشی"
                price = 2_800_000
            else:
                bot_type = "سفارشی"
                price = 2_000_000
            
            # تنظیم قیمت بر اساس سایز
            if lines > 500:
                price = int(price * 1.5)
            elif lines > 200:
                price = int(price * 1.2)
            
            # گزارش
            report = f"""
📄 **گزارش تحلیل**
━━━━━━━━━━━━━━━━
🎯 نوع: {bot_type}
📊 خطوط کد: {lines} خط
💰 قیمت: {price:,} ریال
🔄 اتصال: پایدار ({self.monitor.reconnect_count} reconnects)

🤖 ربات تحلیل‌گر - v14.0
            """
            
            await context.bot.delete_message(
                chat_id=status_msg.chat_id,
                message_id=status_msg.message_id
            )
            
            await update.message.reply_text(report, parse_mode='Markdown')
            logger.info(f"✅ Analysis sent for {file_name}")
            
        except Exception as e:
            logger.error(f"Document processing error: {e}")
            await update.message.reply_text("❌ خطا در پردازش")
    
    async def setup_bot(self):
        """تنظیم اولیه ربات"""
        logger.info("🔄 Setting up bot application...")
        
        try:
            # ایجاد اپلیکیشن
            self.app = Application.builder().token(TOKEN).build()
            
            # ثبت handlerها
            self.app.add_handler(CommandHandler("start", self.start_handler))
            self.app.add_handler(CommandHandler("help", self.start_handler))
            self.app.add_handler(MessageHandler(filters.Document.ALL, self.document_handler))
            
            # خطاگیری
            self.app.add_error_handler(self.error_handler)
            
            logger.info("✅ Bot setup completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Setup failed: {e}")
            return False
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """مدیریت خطاها"""
        error = context.error
        
        if isinstance(error, (TimedOut, NetworkError)):
            logger.warning(f"⚠️ Network error: {error}")
            self.monitor.is_connected = False
            
        elif isinstance(error, Conflict):
            logger.error(f"❌ Conflict error: {error}")
            await asyncio.sleep(10)  # صبر برای رفع conflict
            
        elif isinstance(error, RetryAfter):
            logger.warning(f"⚠️ Rate limited: {error}")
            await asyncio.sleep(error.retry_after)
            
        else:
            logger.error(f"❌ Unexpected error: {error}")
    
    async def run_with_reconnect(self):
        """اجرای ربات با قابلیت reconnect"""
        while True:
            try:
                # پاکسازی قبل از شروع
                await self.cleanup_previous()
                
                # تنظیم ربات
                if not await self.setup_bot():
                    await asyncio.sleep(self.retry_delay)
                    continue
                
                # شروع polling
                logger.info("🚀 Starting bot polling...")
                await self.app.initialize()
                await self.app.start()
                
                # شروع polling با تنظیمات بهینه
                await self.app.updater.start_polling(
                    drop_pending_updates=True,
                    timeout=25,  # کمی کمتر از 30 ثانیه
                    poll_interval=0.5,
                    read_timeout=25,
                    write_timeout=25,
                    connect_timeout=25,
                    pool_timeout=25
                )
                
                self.monitor.is_connected = True
                self.monitor.reconnect_count = 0
                logger.info("✅ Bot is RUNNING and CONNECTED!")
                
                # مانیتور وضعیت اتصال
                await self.connection_monitor()
                
            except (TimedOut, NetworkError) as e:
                logger.warning(f"📡 Connection lost: {e}")
                await self.handle_reconnect()
                
            except Conflict as e:
                logger.error(f"⚡ Conflict: {e}")
                await self.handle_conflict()
                
            except Exception as e:
                logger.error(f"💥 Fatal error: {e}")
                await self.handle_reconnect()
    
    async def cleanup_previous(self):
        """پاکسازی اتصال قبلی"""
        try:
            from telegram import Bot
            temp_bot = Bot(token=TOKEN)
            await temp_bot.delete_webhook(drop_pending_updates=True)
            logger.info("✅ Previous webhook cleared")
            await asyncio.sleep(2)
        except:
            pass
    
    async def connection_monitor(self):
        """مانیتور وضعیت اتصال"""
        while self.monitor.is_connected:
            # آپدیت زمان آخرین فعالیت
            if self.monitor.check_timeout():
                logger.warning("⚠️ Connection timeout detected")
                self.monitor.is_connected = False
                break
            
            # لاگ وضعیت هر 30 ثانیه
            logger.debug(f"🟢 Connection active (last: {time.time() - self.monitor.last_update_time:.0f}s ago)")
            await asyncio.sleep(30)
    
    async def handle_reconnect(self):
        """مدیریت reconnect"""
        if self.app:
            try:
                await self.app.stop()
                await self.app.shutdown()
                logger.info("✅ Bot stopped gracefully")
            except:
                pass
        
        reconnect_num = self.monitor.increment_reconnect()
        
        if reconnect_num > self.monitor.max_reconnects:
            logger.error("❌ Max reconnects reached, waiting 5 minutes...")
            await asyncio.sleep(300)  # 5 دقیقه انتظار
            self.monitor.reconnect_count = 0
        
        # Exponential backoff
        delay = min(self.retry_delay * (2 ** (reconnect_num - 1)), self.max_retry_delay)
        logger.info(f"🔄 Reconnect #{reconnect_num} in {delay} seconds...")
        await asyncio.sleep(delay)
    
    async def handle_conflict(self):
        """مدیریت conflict"""
        logger.warning("⚡ Conflict detected, waiting 30 seconds...")
        await asyncio.sleep(30)
        self.monitor.reconnect_count = 0

# ==================== STATUS CHECKER ====================
async def periodic_status_check(bot: ResilientBot):
    """بررسی دوره‌ای وضعیت"""
    while True:
        try:
            # بررسی اتصال به Telegram API
            from telegram import Bot
            test_bot = Bot(token=TOKEN)
            me = await test_bot.get_me()
            logger.info(f"✅ Telegram API accessible: @{me.username}")
            
            # بررسی آخرین فعالیت
            if bot.monitor.check_timeout():
                logger.warning("⏰ No activity for 2+ minutes")
            
        except Exception as e:
            logger.warning(f"⚠️ Status check failed: {e}")
        
        await asyncio.sleep(60)  # هر 1 دقیقه

# ==================== MAIN ====================
async def main_async():
    """تابع اصلی async"""
    logger.info("=" * 60)
    logger.info("🤖 Telegram Bot Price Analyzer - Auto Reconnect v14.0")
    logger.info("=" * 60)
    logger.info(f"🔑 Token: {TOKEN[:15]}...")
    logger.info(f"🌐 URL: {APP_URL}")
    logger.info(f"🚪 Port: {PORT}")
    
    global monitor
    bot = ResilientBot()
    monitor = bot.monitor
    
    # شروع HTTP Server در thread جداگانه
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    logger.info("✅ HTTP Server started")
    
    # شروع Keep-Alive pinger
    keep_alive_thread = threading.Thread(target=keep_alive_pinger, daemon=True)
    keep_alive_thread.start()
    logger.info("✅ Keep-alive system started")
    
    # شروع status checker
    asyncio.create_task(periodic_status_check(bot))
    
    # اجرای ربات با reconnect
    await bot.run_with_reconnect()

def main():
    """Entry point"""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 Main function error: {e}")

if __name__ == "__main__":
    main()
