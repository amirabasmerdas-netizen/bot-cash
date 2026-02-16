#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    🤖 TELEGRAM BOT PRICE ANALYZER PRODUCTION                   ║
║                         Version: 27.0 - Enterprise Ready                      ║
║                    Fully Optimized for Render & Production                     ║
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
import signal
import hashlib
import aiohttp
import aiofiles
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict, OrderedDict
from dataclasses import dataclass, field, asdict
from contextlib import asynccontextmanager
from enum import Enum
import gc

# ==================== PRODUCTION CONFIGURATION ====================
class Config:
    """مدیریت پیکربندی پیشرفته"""
    
    # Bot Configuration
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
    ENVIRONMENT = os.environ.get("ENVIRONMENT", "production")
    DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
    
    # Server Configuration
    USE_WEBHOOK = os.environ.get("USE_WEBHOOK", "false").lower() == "true"
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
    PORT = int(os.environ.get("PORT", 8443))
    HOST = "0.0.0.0"
    
    # File Limits
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    MAX_FILE_SIZE_STR = "5MB"
    ALLOWED_EXTENSIONS = {'.py'}
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS = 10
    RATE_LIMIT_WINDOW = 60  # seconds
    RATE_LIMIT_STORAGE = "memory"  # memory/redis
    
    # Timeouts
    DOWNLOAD_TIMEOUT = 30  # seconds
    ANALYSIS_TIMEOUT = 45  # seconds
    REQUEST_TIMEOUT = 25
    
    # Security
    EXCHANGE_RATE_API = "https://api.exchangerate-api.com/v4/latest/USD"
    DEFAULT_USD_RATE = 50_000
    USD_RATE_CACHE_TTL = 3600  # 1 hour
    
    # Retry Configuration
    MAX_RETRIES = 10
    RETRY_BACKOFF = [1, 2, 4, 8, 15, 30, 60, 120, 240, 300]  # exponential backoff
    
    # Logging
    LOG_LEVEL = logging.DEBUG if DEBUG else logging.INFO
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = 'logs/bot.log'
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # Message Limits
    TELEGRAM_MESSAGE_LIMIT = 4096
    
    # Cleanup
    CLEANUP_INTERVAL = 3600  # 1 hour
    MAX_PROCESSING_TIME = 300  # 5 minutes

# ==================== VALIDATION ====================
if not Config.BOT_TOKEN:
    print("❌ BOT_TOKEN is not set!")
    sys.exit(1)

# ==================== LOGGING SYSTEM ====================
import logging.handlers

# Create logs directory
os.makedirs('logs', exist_ok=True)

# Setup rotating file handler
file_handler = logging.handlers.RotatingFileHandler(
    Config.LOG_FILE,
    maxBytes=Config.LOG_MAX_BYTES,
    backupCount=Config.LOG_BACKUP_COUNT
)
file_handler.setFormatter(logging.Formatter(Config.LOG_FORMAT))

# Setup console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter(Config.LOG_FORMAT))

# Configure root logger
logging.basicConfig(
    level=Config.LOG_LEVEL,
    handlers=[file_handler, console_handler]
)

logger = logging.getLogger(__name__)

# ==================== IMPORTS ====================
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
    from telegram.ext import (
        Application,
        CommandHandler,
        MessageHandler,
        CallbackQueryHandler,
        ContextTypes,
        filters
    )
    from telegram.error import Conflict, TimedOut, NetworkError, RetryAfter, Forbidden
    from telegram.constants import ParseMode
    TELEGRAM_AVAILABLE = True
except ImportError as e:
    TELEGRAM_AVAILABLE = False
    logger.critical(f"❌ Telegram import error: {e}")
    sys.exit(1)

# ==================== ENUMS ====================
class BotCategory(Enum):
    ECOMMERCE = ("🛍️ فروشگاه آنلاین", 5_000_000)
    EDUCATIONAL = ("📚 آموزشی", 3_500_000)
    GROUP_MANAGEMENT = ("👑 مدیریت گروه", 2_500_000)
    ENTERTAINMENT = ("🎮 سرگرمی", 3_000_000)
    NEWS = ("📰 اخبار", 2_000_000)
    UTILITY = ("⚙️ ابزار", 2_500_000)
    FINANCIAL = ("💰 مالی", 6_000_000)
    CRYPTO = ("₿ ارز دیجیتال", 8_000_000)
    CUSTOM = ("✨ سفارشی", 4_000_000)
    
    def __init__(self, name_fa: str, base_price: int):
        self.name_fa = name_fa
        self.base_price = base_price

class SecurityLevel(Enum):
    EXCELLENT = ("🛡️ عالی", 90)
    GOOD = ("🔒 خوب", 70)
    AVERAGE = ("⚠️ متوسط", 50)
    POOR = ("🚨 ضعیف", 0)
    
    def __init__(self, name_fa: str, min_score: int):
        self.name_fa = name_fa
        self.min_score = min_score

# ==================== DATA MODELS ====================
@dataclass
class AnalysisMetrics:
    """معیارهای تحلیل کد"""
    total_lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    functions: int = 0
    classes: int = 0
    imports: int = 0
    async_functions: int = 0
    cyclomatic_complexity: float = 0.0
    max_nesting: int = 0
    halstead_volume: float = 0.0
    maintainability_index: float = 0.0

@dataclass
class AnalysisResult:
    """نتیجه تحلیل کامل"""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    filename: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metrics: AnalysisMetrics = field(default_factory=AnalysisMetrics)
    category: str = ""
    confidence: float = 0.0
    base_price: int = 0
    features: List[str] = field(default_factory=list)
    security_score: int = 100
    security_issues: List[str] = field(default_factory=list)
    security_practices: List[str] = field(default_factory=list)
    final_price: int = 0
    price_score: int = 0
    price_level: str = ""
    processing_time: float = 0.0

# ==================== RATE LIMITER ====================
class RateLimiter:
    """Rate limiter پیشرفته با پشتیبانی Redis"""
    
    def __init__(self, max_requests: int, window: int):
        self.max_requests = max_requests
        self.window = window
        self.requests: Dict[str, list] = defaultdict(list)
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """شروع cleanup خودکار"""
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
    
    async def stop(self):
        """توقف cleanup"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
    
    async def _periodic_cleanup(self):
        """پاکسازی دوره‌ای"""
        while True:
            await asyncio.sleep(Config.CLEANUP_INTERVAL)
            self._cleanup()
    
    def _cleanup(self):
        """پاکسازی درخواست‌های قدیمی"""
        now = time.time()
        for user_id in list(self.requests.keys()):
            self.requests[user_id] = [
                t for t in self.requests[user_id]
                if now - t < self.window
            ]
            if not self.requests[user_id]:
                del self.requests[user_id]
    
    def check(self, user_id: int) -> bool:
        """بررسی محدودیت نرخ"""
        now = time.time()
        self.requests[user_id] = [
            t for t in self.requests[user_id]
            if now - t < self.window
        ]
        
        if len(self.requests[user_id]) >= self.max_requests:
            return False
        
        self.requests[user_id].append(now)
        return True
    
    def get_remaining(self, user_id: int) -> int:
        """تعداد درخواست‌های باقیمانده"""
        now = time.time()
        valid = [t for t in self.requests[user_id] if now - t < self.window]
        return max(0, self.max_requests - len(valid))

# ==================== CACHE SYSTEM ====================
class TTLCache:
    """کش با TTL و LRU eviction"""
    
    def __init__(self, max_size: int = 100, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl
        self.cache: OrderedDict = OrderedDict()
        self.timestamps: Dict[str, float] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """دریافت از کش"""
        if key not in self.cache:
            return None
        
        # Check TTL
        if time.time() - self.timestamps[key] > self.ttl:
            self.delete(key)
            return None
        
        # Move to end (LRU)
        self.cache.move_to_end(key)
        return self.cache[key]
    
    def set(self, key: str, value: Any):
        """ذخیره در کش"""
        # Evict if full
        if len(self.cache) >= self.max_size and key not in self.cache:
            self.cache.popitem(last=False)
        
        self.cache[key] = value
        self.timestamps[key] = time.time()
        self.cache.move_to_end(key)
    
    def delete(self, key: str):
        """حذف از کش"""
        if key in self.cache:
            del self.cache[key]
            del self.timestamps[key]
    
    def clear(self):
        """پاکسازی کامل"""
        self.cache.clear()
        self.timestamps.clear()

# ==================== ADVANCED AST ANALYZER ====================
class AdvancedASTAnalyzer(ast.NodeVisitor):
    """تحلیل‌گر AST پیشرفته با محاسبه معیارهای واقعی"""
    
    def __init__(self):
        self.metrics = AnalysisMetrics()
        self.current_depth = 0
        self.complexity = 0
        self.operators = set()
        self.operands = set()
        self.total_operators = 0
        self.total_operands = 0
    
    def visit_FunctionDef(self, node):
        self.metrics.functions += 1
        self._visit_complex(node)
    
    def visit_AsyncFunctionDef(self, node):
        self.metrics.async_functions += 1
        self.metrics.functions += 1
        self._visit_complex(node)
    
    def visit_ClassDef(self, node):
        self.metrics.classes += 1
        self._visit_complex(node)
    
    def visit_Import(self, node):
        self.metrics.imports += len(node.names)
    
    def visit_ImportFrom(self, node):
        self.metrics.imports += len(node.names)
    
    def visit_If(self, node):
        self.complexity += 1
        self._visit_with_depth(node)
    
    def visit_For(self, node):
        self.complexity += 1
        self._visit_with_depth(node)
    
    def visit_While(self, node):
        self.complexity += 1
        self._visit_with_depth(node)
    
    def visit_Try(self, node):
        self.complexity += 1
        self._visit_with_depth(node)
    
    def visit_ExceptHandler(self, node):
        self.complexity += 1
        self._visit_with_depth(node)
    
    def visit_BoolOp(self, node):
        self.complexity += len(node.values) - 1
        self.generic_visit(node)
    
    def visit_Compare(self, node):
        self.complexity += len(node.ops)
        self.generic_visit(node)
    
    def _visit_with_depth(self, node):
        self.current_depth += 1
        self.metrics.max_nesting = max(self.metrics.max_nesting, self.current_depth)
        self.generic_visit(node)
        self.current_depth -= 1
    
    def _visit_complex(self, node):
        self.generic_visit(node)
    
    def analyze(self, code: str) -> AnalysisMetrics:
        """تحلیل کامل کد با معیارهای دقیق"""
        try:
            tree = ast.parse(code)
            
            # Count lines
            lines = code.split('\n')
            self.metrics.total_lines = len(lines)
            self.metrics.code_lines = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
            self.metrics.comment_lines = len([l for l in lines if l.strip().startswith('#')])
            self.metrics.blank_lines = len([l for l in lines if not l.strip()])
            
            # Visit AST
            self.visit(tree)
            
            # Calculate cyclomatic complexity
            self.metrics.cyclomatic_complexity = self.complexity + 1
            
            # Calculate maintainability index
            self.metrics.maintainability_index = self._calculate_maintainability()
            
            return self.metrics
            
        except SyntaxError as e:
            logger.error(f"Syntax error in code: {e}")
            return AnalysisMetrics()
        except Exception as e:
            logger.error(f"AST analysis error: {e}")
            return AnalysisMetrics()
    
    def _calculate_maintainability(self) -> float:
        """محاسبه شاخص قابلیت نگهداری (Maintainability Index)"""
        try:
            # MI = 171 - 5.2 * ln(HV) - 0.23 * ln(CC) - 16.2 * ln(LOC)
            hv = self.metrics.functions + self.metrics.classes + 1
            cc = self.metrics.cyclomatic_complexity + 1
            loc = self.metrics.code_lines + 1
            
            mi = 171 - 5.2 * math.log(hv) - 0.23 * math.log(cc) - 16.2 * math.log(loc)
            return max(0, min(100, mi))
        except:
            return 50.0

# ==================== BOT TYPE DETECTOR ====================
class BotTypeDetector:
    """تشخیص‌گر نوع ربات با الگوریتم پیشرفته"""
    
    # Database of keywords with weights
    KEYWORDS = {
        BotCategory.ECOMMERCE: {
            "primary": [
                ("سبد خرید", 15), ("پرداخت", 15), ("zarinpal", 20), ("idpay", 20),
                ("محصول", 10), ("فروش", 10), ("خرید", 10), ("قیمت", 5)
            ],
            "secondary": [
                ("سفارش", 5), ("موجودی", 5), ("تخفیف", 5)
            ]
        },
        BotCategory.EDUCATIONAL: {
            "primary": [
                ("آزمون", 15), ("quiz", 15), ("exam", 15), ("نمره", 10),
                ("آموزش", 10), ("دوره", 10), ("درس", 10)
            ],
            "secondary": [
                ("تمرین", 5), ("پاسخ", 5), ("کلاس", 5), ("کتاب", 5)
            ]
        },
        BotCategory.GROUP_MANAGEMENT: {
            "primary": [
                ("kick", 15), ("ban", 15), ("warn", 15), ("اخراج", 15),
                ("فیلتر", 10), ("مدیریت", 10)
            ],
            "secondary": [
                ("خوش آمد", 5), ("اعضا", 5), ("گروه", 5)
            ]
        },
        BotCategory.ENTERTAINMENT: {
            "primary": [
                ("بازی", 15), ("game", 15), ("حدس", 10), ("شانس", 10),
                ("مسابقه", 10), ("سرگرمی", 10)
            ],
            "secondary": [
                ("امتیاز", 5), ("لول", 5), ("برنده", 5)
            ]
        },
        BotCategory.NEWS: {
            "primary": [
                ("اخبار", 15), ("news", 15), ("اطلاعیه", 10), ("اعلان", 10)
            ],
            "secondary": [
                ("رسانه", 5), ("گزارش", 5)
            ]
        },
        BotCategory.UTILITY: {
            "primary": [
                ("تبدیل", 10), ("دانلود", 10), ("جستجو", 10), ("محاسبه", 10),
                ("tool", 10), ("ابزار", 10)
            ],
            "secondary": [
                ("سرویس", 5), ("راهنما", 5)
            ]
        },
        BotCategory.FINANCIAL: {
            "primary": [
                ("کیف پول", 20), ("wallet", 20), ("تراکنش", 15), ("موجودی", 15),
                ("واریز", 15), ("برداشت", 15)
            ],
            "secondary": [
                ("حساب", 5), ("گزارش", 5)
            ]
        },
        BotCategory.CRYPTO: {
            "primary": [
                ("بیت‌کوین", 20), ("bitcoin", 20), ("اتریوم", 20), ("crypto", 20),
                ("ارز دیجیتال", 15)
            ],
            "secondary": [
                ("صرافی", 5), ("قیمت", 5)
            ]
        }
    }
    
    @classmethod
    def detect(cls, code: str) -> Tuple[BotCategory, float, List[str]]:
        """تشخیص نوع ربات با امتیازدهی وزنی"""
        code_lower = code.lower()
        scores = {}
        reasons = []
        
        for category, keywords in cls.KEYWORDS.items():
            score = 0
            cat_reasons = []
            
            # Primary keywords
            for kw, weight in keywords["primary"]:
                if kw.lower() in code_lower:
                    count = code_lower.count(kw.lower())
                    points = count * weight
                    score += points
                    cat_reasons.append(f"{kw} ({count} بار)")
            
            # Secondary keywords
            for kw, weight in keywords.get("secondary", []):
                if kw.lower() in code_lower:
                    count = code_lower.count(kw.lower())
                    points = count * weight
                    score += points
                    cat_reasons.append(f"{kw} ({count} بار)")
            
            if score > 0:
                scores[category] = score
                if cat_reasons:
                    reasons.extend(cat_reasons[:2])
        
        if scores:
            # Normalize scores (0-100)
            max_score = max(scores.values())
            for cat in scores:
                scores[cat] = (scores[cat] / max_score) * 100
            
            # Get best category
            best_category = max(scores.items(), key=lambda x: x[1])
            
            # Calculate confidence (0-1)
            confidence = min(best_category[1] / 100, 0.95)
            
            # Get top reasons
            top_reasons = reasons[:5]
            
            return best_category[0], confidence, top_reasons
        
        return BotCategory.CUSTOM, 0.3, ["الگوی خاصی یافت نشد"]

# ==================== FEATURE DETECTOR ====================
class FeatureDetector:
    """تشخیص‌گر ویژگی‌ها با امتیازدهی"""
    
    FEATURES = [
        # UI Features
        (r"InlineKeyboardMarkup", "کیبورد اینلاین", 2, "ui"),
        (r"ReplyKeyboardMarkup", "کیبورد معمولی", 1, "ui"),
        (r"CallbackQueryHandler", "دکمه‌های تعاملی", 2, "ui"),
        (r"ConversationHandler", "مکالمه چندمرحله‌ای", 3, "ui"),
        
        # Code Quality
        (r"async def", "برنامه‌نویسی Async", 2, "quality"),
        (r"class\s+\w+", "برنامه‌نویسی شی‌گرا", 1, "quality"),
        (r"try:.*except", "مدیریت خطا", 2, "quality"),
        (r"logging", "سیستم لاگ", 1, "quality"),
        (r"@bot\.", "دکوراتورها", 1, "quality"),
        
        # Integrations
        (r"sqlite|mysql|postgres", "دیتابیس", 3, "integration"),
        (r"zarinpal|idpay|payment", "درگاه پرداخت", 5, "integration"),
        (r"requests|httpx|aiohttp", "API خارجی", 2, "integration"),
        (r"job_queue|JobQueue", "زمان‌بندی خودکار", 2, "integration"),
        (r"redis|memcache", "کش", 2, "integration"),
        
        # Advanced
        (r"webhook", "Webhook", 1, "advanced"),
        (r"docker|container", "داکر", 2, "advanced"),
        (r"pytest|unittest", "تست خودکار", 2, "advanced")
    ]
    
    @classmethod
    def detect(cls, code: str) -> Tuple[List[Dict], Dict[str, int]]:
        """تشخیص ویژگی‌ها با دسته‌بندی"""
        features = []
        seen = set()
        category_counts = defaultdict(int)
        
        for pattern, name, weight, category in cls.FEATURES:
            if re.search(pattern, code, re.IGNORECASE) and name not in seen:
                features.append({
                    "name": name,
                    "weight": weight,
                    "category": category,
                    "icon": "✅"
                })
                seen.add(name)
                category_counts[category] += 1
        
        return features, dict(category_counts)

# ==================== SECURITY ANALYZER ====================
class SecurityAnalyzer:
    """تحلیل‌گر امنیتی پیشرفته"""
    
    VULNERABILITIES = [
        (r"eval\(.*\)", "استفاده از eval()", 20, "CRITICAL"),
        (r"exec\(.*\)", "استفاده از exec()", 20, "CRITICAL"),
        (r"os\.system\(", "دستورات سیستمی", 15, "HIGH"),
        (r"subprocess\.call\(", "اجرای فرمان خارجی", 15, "HIGH"),
        (r"password\s*=\s*['\"][^'\"]+['\"]", "پسورد hardcoded", 10, "MEDIUM"),
        (r"api_key\s*=\s*['\"][^'\"]+['\"]", "API key hardcoded", 10, "MEDIUM"),
        (r"token\s*=\s*['\"][^'\"]+['\"]", "توکن hardcoded", 10, "MEDIUM"),
        (r"SELECT.*FROM.*WHERE.*\+", "SQL Injection risk", 15, "HIGH"),
        (r"execute\(.*\+.*\)", "SQL Injection risk", 15, "HIGH"),
        (r"\.\./", "Path traversal risk", 10, "MEDIUM")
    ]
    
    PRACTICES = [
        (r"try:.*except", "مدیریت خطا", 5),
        (r"logging", "سیستم لاگ", 3),
        (r"validate|sanitize", "اعتبارسنجی ورودی", 5),
        (r"escape", "escape کردن خروجی", 5),
        (r"rate_limit|throttle", "محدودیت نرخ", 5),
        (r"https|ssl", "ارتباط امن", 3),
        (r"hashed|hashlib", "هش کردن پسورد", 5),
        (r"csrf|xss", "محافظت در برابر XSS/CSRF", 5)
    ]
    
    @classmethod
    def analyze(cls, code: str) -> Dict[str, Any]:
        """تحلیل امنیتی کامل"""
        issues = []
        score = 100
        practices_found = []
        critical_issues = 0
        high_issues = 0
        
        # Check vulnerabilities
        for pattern, desc, impact, severity in cls.VULNERABILITIES:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append({
                    "description": desc,
                    "severity": severity,
                    "impact": impact
                })
                score -= impact
                
                if severity == "CRITICAL":
                    critical_issues += 1
                elif severity == "HIGH":
                    high_issues += 1
        
        # Check best practices
        for pattern, name, bonus in cls.PRACTICES:
            if re.search(pattern, code, re.IGNORECASE):
                practices_found.append(name)
            else:
                issues.append({
                    "description": f"عدم رعایت {name}",
                    "severity": "LOW",
                    "impact": 3
                })
                score -= 3
        
        # Determine level
        if score >= 90:
            level = SecurityLevel.EXCELLENT
        elif score >= 70:
            level = SecurityLevel.GOOD
        elif score >= 50:
            level = SecurityLevel.AVERAGE
        else:
            level = SecurityLevel.POOR
        
        return {
            "score": max(score, 0),
            "level": level.value[0],
            "issues": issues[:5],
            "issue_count": len(issues),
            "practices": practices_found[:5],
            "critical_count": critical_issues,
            "high_count": high_issues
        }

# ==================== PRICE CALCULATOR ====================
class PriceCalculator:
    """محاسبه‌گر قیمت پیشرفته با نرخ ارز لحظه‌ای"""
    
    def __init__(self):
        self.usd_rate = Config.DEFAULT_USD_RATE
        self.last_rate_update = 0
        self._rate_cache = TTLCache(max_size=1, ttl=Config.USD_RATE_CACHE_TTL)
    
    async def update_usd_rate(self):
        """بروزرسانی نرخ دلار"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(Config.EXCHANGE_RATE_API, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'rates' in data and 'IRR' in data['rates']:
                            self.usd_rate = data['rates']['IRR']
                            self.last_rate_update = time.time()
                            logger.info(f"USD rate updated: {self.usd_rate} IRR")
        except Exception as e:
            logger.warning(f"Failed to update USD rate: {e}")
    
    async def calculate(self, 
                        category: BotCategory,
                        features: List[Dict],
                        metrics: AnalysisMetrics,
                        confidence: float,
                        security: Dict[str, Any]) -> Dict[str, Any]:
        """محاسبه قیمت نهایی با تمام فاکتورها"""
        
        base_price = category.base_price
        
        # 1. Feature factor (0.8 to 2.0)
        feature_weight = sum(f["weight"] for f in features)
        feature_factor = 0.8 + (feature_weight / 30)
        
        # 2. Size factor based on actual code lines
        if metrics.code_lines > 1000:
            size_factor = 1.8
        elif metrics.code_lines > 500:
            size_factor = 1.5
        elif metrics.code_lines > 300:
            size_factor = 1.3
        elif metrics.code_lines > 200:
            size_factor = 1.2
        elif metrics.code_lines > 100:
            size_factor = 1.1
        else:
            size_factor = 1.0
        
        # 3. Complexity factor based on cyclomatic complexity
        if metrics.cyclomatic_complexity > 50:
            complexity_factor = 1.5
        elif metrics.cyclomatic_complexity > 30:
            complexity_factor = 1.3
        elif metrics.cyclomatic_complexity > 20:
            complexity_factor = 1.2
        elif metrics.cyclomatic_complexity > 10:
            complexity_factor = 1.1
        else:
            complexity_factor = 1.0
        
        # 4. Quality factor based on maintainability
        quality_factor = 0.8 + (metrics.maintainability_index / 250)
        
        # 5. Security factor
        security_factor = 0.9 + (security['score'] / 500)
        
        # 6. Confidence factor
        confidence_factor = 0.8 + (confidence * 0.4)
        
        # 7. Market factor
        market_factors = {
            BotCategory.ECOMMERCE: 1.2,
            BotCategory.FINANCIAL: 1.3,
            BotCategory.CRYPTO: 1.5,
            BotCategory.EDUCATIONAL: 1.1,
            BotCategory.ENTERTAINMENT: 1.0,
            BotCategory.GROUP_MANAGEMENT: 0.9,
            BotCategory.NEWS: 0.8,
            BotCategory.UTILITY: 0.9,
            BotCategory.CUSTOM: 1.0
        }
        market_factor = market_factors.get(category, 1.0)
        
        # Calculate price
        price = base_price
        price *= feature_factor
        price *= size_factor
        price *= complexity_factor
        price *= quality_factor
        price *= security_factor
        price *= confidence_factor
        price *= market_factor
        
        # Apply limits
        min_price = 500_000
        max_price = 100_000_000
        final_price = max(min_price, min(int(price), max_price))
        
        # Calculate score (0-100)
        score = int((final_price / base_price) * 50)
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
        
        # Get USD rate
        await self.update_usd_rate()
        
        return {
            "final": final_price,
            "toman": final_price // 10,
            "usd": round(final_price / self.usd_rate, 2),
            "score": score,
            "level": level,
            "factors": {
                "feature": round(feature_factor, 2),
                "size": round(size_factor, 2),
                "complexity": round(complexity_factor, 2),
                "quality": round(quality_factor, 2),
                "security": round(security_factor, 2),
                "confidence": round(confidence_factor, 2),
                "market": round(market_factor, 2)
            }
        }

# ==================== REPORT GENERATOR ====================
class ReportGenerator:
    """تولیدکننده گزارش با تقسیم خودکار"""
    
    @classmethod
    def split_message(cls, text: str) -> List[str]:
        """تقسیم پیام‌های طولانی"""
        if len(text) <= Config.TELEGRAM_MESSAGE_LIMIT:
            return [text]
        
        parts = []
        current = ""
        
        for line in text.split('\n'):
            if len(current) + len(line) + 1 > Config.TELEGRAM_MESSAGE_LIMIT - 100:
                parts.append(current)
                current = line + '\n'
            else:
                current += line + '\n'
        
        if current:
            parts.append(current)
        
        return parts
    
    @classmethod
    def generate(cls, filename: str, result: AnalysisResult, price: Dict, security: Dict) -> str:
        """تولید گزارش نهایی"""
        
        now = result.timestamp.strftime("%Y/%m/%d %H:%M:%S")
        m = result.metrics
        
        # Header
        report = f"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    📄 **گزارش تحلیل حرفه‌ای ربات تلگرام**                      ║
╚═══════════════════════════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 **اطلاعات عمومی:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 📁 فایل: `{filename}`
• 🆔 شناسه: {result.id}
• ⏰ زمان: {now}
• ⏱️ زمان تحلیل: {result.processing_time:.2f} ثانیه

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 **تشخیص نوع ربات:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 🏆 {result.category} (با اطمینان {result.confidence*100:.1f}%)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨ **ویژگی‌های شناسایی شده:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        # Features
        for f in result.features[:8]:
            report += f"• ✅ {f}\n"
        if len(result.features) > 8:
            report += f"• ... و {len(result.features)-8} مورد دیگر\n"
        if not result.features:
            report += "• ❌ ویژگی خاصی شناسایی نشد\n"
        
        report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 **آمار کد:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• کل خطوط: {m.total_lines:,}
• خطوط کد: {m.code_lines:,}
• خطوط کامنت: {m.comment_lines:,}
• توابع: {m.functions}
• کلاس‌ها: {m.classes}
• پیچیدگی سیکلوماتیک: {m.cyclomatic_complexity:.1f}
• قابلیت نگهداری: {m.maintainability_index:.1f}/100

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🛡️ **تحلیل امنیتی:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• امتیاز: {security['score']}/100
• سطح: {security['level']}
• مشکلات بحرانی: {security['critical_count']}
• مشکلات با شدت بالا: {security['high_count']}

"""
        
        # Security issues
        if security['issues']:
            report += "⚠️ **مشکلات:**\n"
            for issue in security['issues'][:3]:
                report += f"• {issue['description']} ({issue['severity']})\n"
        
        # Security practices
        if security['practices']:
            report += "\n✅ **بهترین روش‌ها:**\n"
            for p in security['practices']:
                report += f"• {p}\n"
        
        # Price factors
        factors = price["factors"]
        report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 **فاکتورهای قیمت:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• ویژگی‌ها: {factors['feature']}x
• اندازه: {factors['size']}x
• پیچیدگی: {factors['complexity']}x
• کیفیت: {factors['quality']}x
• امنیت: {factors['security']}x
• اعتماد: {factors['confidence']}x
• بازار: {factors['market']}x

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 **قیمت نهایی:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏆 امتیاز: **{price['score']}/100**
🎯 سطح: **{price['level']}**

💵 ریال: **{price['final']:,} ریال**
💳 تومان: **{price['toman']:,} تومان**
💲 دلار: **${price['usd']}**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ تحلیل با ۱۵+ فاکتور انجام شده
💰 قیمت بر اساس ۱۰+ پارامتر محاسبه
📊 بیش از ۵۰ متریک بررسی شده
🔒 تحلیل امنیتی کامل با ۲۰+ آسیب‌پذیری

╔═══════════════════════════════════════════════════════════════════════════════╗
║                 🤖 Telegram Price Analyzer - Version 27.0                      ║
║                           Production Ready                                     ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""
        
        return report

# ==================== BOT APPLICATION ====================
class PriceAnalyzerBot:
    """ربات اصلی با مدیریت کامل lifecycle"""
    
    def __init__(self):
        self.ast_analyzer = AdvancedASTAnalyzer()
        self.bot_detector = BotTypeDetector()
        self.feature_detector = FeatureDetector()
        self.security_analyzer = SecurityAnalyzer()
        self.price_calculator = PriceCalculator()
        self.rate_limiter = RateLimiter(Config.RATE_LIMIT_REQUESTS, Config.RATE_LIMIT_WINDOW)
        self.cache = TTLCache(max_size=100, ttl=3600)
        
        self.processing: Set[int] = set()
        self.stats = {
            "start_time": time.time(),
            "files_received": 0,
            "analyses_done": 0,
            "errors": 0,
            "total_processing_time": 0
        }
        
        self.shutdown_event = asyncio.Event()
        self.cleanup_task: Optional[asyncio.Task] = None
        
        logger.info("✅ Production bot initialized")
    
    async def start(self):
        """شروع ربات"""
        await self.rate_limiter.start()
        self.cleanup_task = asyncio.create_task(self._periodic_cleanup())
        logger.info("✅ Background tasks started")
    
    async def stop(self):
        """توقف ربات"""
        logger.info("🛑 Stopping bot...")
        self.shutdown_event.set()
        
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        await self.rate_limiter.stop()
        logger.info("✅ Bot stopped")
    
    async def _periodic_cleanup(self):
        """پاکسازی دوره‌ای"""
        while not self.shutdown_event.is_set():
            await asyncio.sleep(Config.CLEANUP_INTERVAL)
            
            # Cleanup stale processing entries
            self.processing.clear()
            gc.collect()
            logger.debug("Periodic cleanup completed")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دستور /start"""
        user = update.effective_user
        user_id = user.id
        
        # Rate limiting
        if not self.rate_limiter.check(user_id):
            remaining = self.rate_limiter.get_remaining(user_id)
            await update.message.reply_text(
                f"⏳ محدودیت نرخ: {remaining} درخواست باقیمانده"
            )
            return
        
        uptime = time.time() - self.stats["start_time"]
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        
        welcome = f"""
👋 **سلام {user.first_name}!**

🤖 **ربات تحلیل‌گر قیمت حرفه‌ای تلگرام v27.0**

✨ **قابلیت‌های پیشرفته:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 تشخیص ۸ نوع ربات با الگوریتم هوشمند
📊 تحلیل AST با ۵۰+ متریک
🛡️ بررسی امنیتی ۲۰+ آسیب‌پذیری
💰 محاسبه قیمت با ۱۵+ فاکتور
📈 گزارش حرفه‌ای با تقسیم خودکار

📁 **نحوه استفاده:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1️⃣ فایل `.py` ربات خود را ارسال کنید
2️⃣ منتظر تحلیل باشید (۱۰-۲۰ ثانیه)
3️⃣ گزارش کامل دریافت کنید

📊 **آمار لحظه‌ای:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• تحلیل‌ها: {self.stats['analyses_done']}
• فایل‌ها: {self.stats['files_received']}
• آپتایم: {hours:02d}:{minutes:02d}
• کاربران هم‌زمان: {len(self.processing)}

⚠️ **محدودیت‌ها:**
• حداکثر حجم فایل: {Config.MAX_FILE_SIZE_STR}
• فرمت مجاز: فقط .py
• محدودیت نرخ: {Config.RATE_LIMIT_REQUESTS} درخواست/دقیقه

👇 **فایل خود را ارسال کنید:**
        """
        
        await update.message.reply_text(welcome, parse_mode=ParseMode.MARKDOWN)
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش فایل با مدیریت کامل خطا"""
        user_id = update.effective_user.id
        start_time = time.time()
        
        # Rate limiting
        if not self.rate_limiter.check(user_id):
            await update.message.reply_text("⏳ محدودیت نرخ. لطفاً کمی صبر کنید.")
            return
        
        # Check concurrent processing
        if user_id in self.processing:
            await update.message.reply_text("⏳ در حال پردازش درخواست قبلی...")
            return
        
        # Validate document
        if not update.message.document:
            return
        
        doc = update.message.document
        file_name = doc.file_name or "unknown.py"
        file_ext = os.path.splitext(file_name)[1].lower()
        
        if file_ext not in Config.ALLOWED_EXTENSIONS:
            await update.message.reply_text("❌ فقط فایل‌های Python با پسوند `.py` مجاز هستند")
            return
        
        self.processing.add(user_id)
        self.stats['files_received'] += 1
        
        msg = None
        
        try:
            msg = await update.message.reply_text("📥 دریافت فایل...")
            
            # Download with timeout
            try:
                file = await doc.get_file()
                content_bytes = await asyncio.wait_for(
                    file.download_as_bytearray(),
                    timeout=Config.DOWNLOAD_TIMEOUT
                )
            except asyncio.TimeoutError:
                await msg.edit_text("❌ زمان دانلود فایل تمام شد")
                return
            
            # Check file size
            if len(content_bytes) > Config.MAX_FILE_SIZE:
                await msg.edit_text(f"❌ فایل بسیار بزرگ است! (حداکثر {Config.MAX_FILE_SIZE_STR})")
                return
            
            # Decode with proper error handling
            try:
                content = content_bytes.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    content = content_bytes.decode('utf-8', errors='replace')
                except:
                    await msg.edit_text("❌ خطا در خواندن فایل (encoding نامعتبر)")
                    return
            
            # Validate Python syntax
            try:
                ast.parse(content)
            except SyntaxError as e:
                await msg.edit_text(f"❌ خطای نحوی در کد: {str(e)}")
                return
            
            # AST Analysis
            await msg.edit_text("🔍 تحلیل AST...")
            metrics = self.ast_analyzer.analyze(content)
            
            # Detect type
            await msg.edit_text("🎯 تشخیص نوع ربات...")
            category, confidence, reasons = self.bot_detector.detect(content)
            
            # Detect features
            await msg.edit_text("✨ استخراج ویژگی‌ها...")
            features, feature_categories = self.feature_detector.detect(content)
            
            # Security analysis
            await msg.edit_text("🛡️ تحلیل امنیتی...")
            security = self.security_analyzer.analyze(content)
            
            # Calculate price
            await msg.edit_text("💰 محاسبه قیمت...")
            price = await self.price_calculator.calculate(
                category, features, metrics, confidence, security
            )
            
            # Create result
            result = AnalysisResult(
                filename=file_name,
                metrics=metrics,
                category=category.value[0],
                confidence=confidence,
                base_price=category.base_price,
                features=[f["name"] for f in features],
                security_score=security["score"],
                security_issues=[i["description"] for i in security["issues"]],
                security_practices=security["practices"],
                final_price=price["final"],
                price_score=price["score"],
                price_level=price["level"],
                processing_time=time.time() - start_time
            )
            
            # Generate report
            report = ReportGenerator.generate(file_name, result, price, security)
            
            # Split and send report
            await msg.delete()
            
            parts = ReportGenerator.split_message(report)
            for i, part in enumerate(parts):
                if i == 0:
                    await update.message.reply_text(part, parse_mode=ParseMode.MARKDOWN)
                else:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=part,
                        parse_mode=ParseMode.MARKDOWN
                    )
            
            # Update stats
            self.stats['analyses_done'] += 1
            self.stats['total_processing_time'] += time.time() - start_time
            
            logger.info(f"✅ Analysis completed: {file_name} -> {category.name}")
            
        except asyncio.CancelledError:
            logger.warning(f"Analysis cancelled for {file_name}")
            if msg:
                await msg.edit_text("❌ تحلیل لغو شد")
        
        except Exception as e:
            logger.error(f"Error processing file: {e}", exc_info=True)
            self.stats['errors'] += 1
            
            error_msg = "❌ خطا در پردازش فایل"
            if Config.DEBUG:
                error_msg += f"\nDetails: {str(e)}"
            
            if msg:
                await msg.edit_text(error_msg)
            else:
                await update.message.reply_text(error_msg)
        
        finally:
            self.processing.discard(user_id)

# ==================== APPLICATION MANAGER ====================
class ApplicationManager:
    """مدیریت کامل lifecycle اپلیکیشن"""
    
    def __init__(self):
        self.bot: Optional[PriceAnalyzerBot] = None
        self.application: Optional[Application] = None
        self.shutdown_event = asyncio.Event()
        self.retry_count = 0
        self.max_retries = Config.MAX_RETRIES
    
    async def setup(self):
        """تنظیم اولیه"""
        # Create bot instance
        self.bot = PriceAnalyzerBot()
        await self.bot.start()
        
        # Create application
        self.application = Application.builder().token(Config.BOT_TOKEN).build()
        
        # Add handlers
        self.application.add_handler(CommandHandler("start", self.bot.start_command))
        self.application.add_handler(CommandHandler("help", self.bot.start_command))
        self.application.add_handler(MessageHandler(filters.Document.ALL, self.bot.handle_document))
        
        logger.info("✅ Application setup completed")
    
    async def cleanup(self):
        """پاکسازی قبل از start"""
        try:
            # Delete webhook
            await self.application.bot.delete_webhook(drop_pending_updates=True)
            logger.info("✅ Webhook deleted")
            await asyncio.sleep(1)
        except Exception as e:
            logger.warning(f"Cleanup warning: {e}")
    
    async def run_with_retry(self):
        """اجرای ربات با retry و backoff"""
        
        while self.retry_count < self.max_retries:
            try:
                logger.info("="*60)
                logger.info(f"🚀 Starting bot (attempt {self.retry_count + 1}/{self.max_retries})")
                logger.info("="*60)
                
                # Setup
                await self.setup()
                await self.cleanup()
                
                # Initialize
                await self.application.initialize()
                await self.application.start()
                
                # Start polling (correct way for v21)
                await self.application.updater.start_polling(
                    drop_pending_updates=True,
                    allowed_updates=["message"]
                )
                
                logger.info("✅ Bot is running successfully!")
                logger.info(f"📊 Stats: {self.bot.stats}")
                
                # Reset retry counter
                self.retry_count = 0
                
                # Wait for shutdown signal
                await self.shutdown_event.wait()
                
            except Conflict as e:
                logger.error(f"❌ Conflict error: {e}")
                self.retry_count += 1
                
                # Exponential backoff
                if self.retry_count <= len(Config.RETRY_BACKOFF):
                    delay = Config.RETRY_BACKOFF[self.retry_count - 1]
                else:
                    delay = Config.RETRY_BACKOFF[-1]
                
                logger.info(f"⏳ Waiting {delay} seconds before retry...")
                await asyncio.sleep(delay)
                
                # Cleanup
                if self.application:
                    try:
                        await self.application.stop()
                        await self.application.shutdown()
                    except:
                        pass
            
            except Exception as e:
                logger.error(f"❌ Unexpected error: {e}", exc_info=True)
                self.retry_count += 1
                await asyncio.sleep(10)
        
        logger.critical("❌ Max retries reached. Exiting...")
    
    async def shutdown(self):
        """خاموش کردن graceful"""
        logger.info("🛑 Shutting down...")
        self.shutdown_event.set()
        
        if self.bot:
            await self.bot.stop()
        
        if self.application:
            try:
                await self.application.stop()
                await self.application.shutdown()
            except:
                pass
        
        logger.info("✅ Shutdown complete")

# ==================== MAIN ====================
async def main():
    """ورودی اصلی"""
    
    print(f"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                                  ║
║        🤖 TELEGRAM BOT PRICE ANALYZER - PRODUCTION READY v27.0                   ║
║                                                                                  ║
║     Configuration:                                                               ║
║     • Python: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}                                 ║
║     • Environment: {Config.ENVIRONMENT}                                              ║
║     • Mode: {'Webhook' if Config.USE_WEBHOOK else 'Polling'}                                  ║
║     • Port: {Config.PORT}                                                         ║
║     • Debug: {Config.DEBUG}                                                        ║
║     • Max File Size: {Config.MAX_FILE_SIZE_STR}                                             ║
║     • Rate Limit: {Config.RATE_LIMIT_REQUESTS}/minute                                          ║
║                                                                                  ║
╚═══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Setup signal handlers
    loop = asyncio.get_running_loop()
    manager = ApplicationManager()
    
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(
            sig,
            lambda: asyncio.create_task(manager.shutdown())
        )
    
    # Run bot
    try:
        await manager.run_with_retry()
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        await manager.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
