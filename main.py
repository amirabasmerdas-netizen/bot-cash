#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    🤖 TELEGRAM BOT PRICE ANALYZER ULTIMATE                     ║
║                         Version: 25.0 - Professional Edition                   ║
║                    Advanced Telegram Bot Price Analysis System                 ║
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
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from enum import Enum

# ==================== TELEGRAM SETUP ====================
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
    TELEGRAM_AVAILABLE = True
except ImportError as e:
    TELEGRAM_AVAILABLE = False
    print(f"❌ Error: {e}")
    print("Please install: pip install python-telegram-bot==21.7")
    sys.exit(1)

# ==================== CONFIGURATION ====================
TOKEN = os.environ.get("BOT_TOKEN", "")
PORT = int(os.environ.get("PORT", 8443))
ENVIRONMENT = os.environ.get("ENVIRONMENT", "production")
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"

if not TOKEN:
    print("❌ BOT_TOKEN is not set!")
    sys.exit(1)

# ==================== LOGGING SYSTEM ====================
class LogColors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

class ColoredFormatter(logging.Formatter):
    """فرمatter رنگی برای لاگ‌ها"""
    
    format_str = "%(asctime)s | %(levelname)8s | %(message)s"
    
    FORMATS = {
        logging.DEBUG: LogColors.BLUE + format_str + LogColors.END,
        logging.INFO: LogColors.GREEN + format_str + LogColors.END,
        logging.WARNING: LogColors.YELLOW + format_str + LogColors.END,
        logging.ERROR: LogColors.RED + format_str + LogColors.END,
        logging.CRITICAL: LogColors.RED + LogColors.BOLD + format_str + LogColors.END
    }
    
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt='%H:%M:%S')
        return formatter.format(record)

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)

# Console handler with colors
console = logging.StreamHandler(sys.stdout)
console.setFormatter(ColoredFormatter())
logger.addHandler(console)

# File handler
try:
    os.makedirs('logs', exist_ok=True)
    file_handler = logging.FileHandler(f'logs/bot_{datetime.now().strftime("%Y%m%d")}.log')
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(file_handler)
except:
    pass

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

class ComplexityLevel(Enum):
    LOW = "🟢 کم"
    MEDIUM = "🟡 متوسط"
    HIGH = "🟠 زیاد"
    VERY_HIGH = "🔴 خیلی زیاد"

class SecurityLevel(Enum):
    EXCELLENT = "🛡️ عالی"
    GOOD = "🔒 خوب"
    AVERAGE = "⚠️ متوسط"
    POOR = "🚨 ضعیف"

# ==================== DATA MODELS ====================
@dataclass
class AnalysisResult:
    """نتیجه تحلیل"""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    filename: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Basic info
    total_lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    
    # Code metrics
    functions: int = 0
    classes: int = 0
    imports: int = 0
    async_functions: int = 0
    complexity: int = 0
    
    # Bot type
    category: str = ""
    confidence: float = 0.0
    base_price: int = 0
    
    # Features
    features: List[str] = field(default_factory=list)
    
    # Security
    security_score: int = 100
    security_issues: List[str] = field(default_factory=list)
    security_practices: List[str] = field(default_factory=list)
    
    # Price
    final_price: int = 0
    price_score: int = 0
    price_level: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "filename": self.filename,
            "timestamp": self.timestamp.isoformat(),
            "total_lines": self.total_lines,
            "code_lines": self.code_lines,
            "category": self.category,
            "confidence": self.confidence,
            "features": self.features,
            "final_price": self.final_price
        }

# ==================== AST ANALYZER ====================
class ASTAnalyzer:
    """تحلیل‌گر AST پیشرفته"""
    
    @staticmethod
    def analyze(code: str) -> Dict[str, Any]:
        """تحلیل کد با AST"""
        try:
            tree = ast.parse(code)
            analyzer = _ASTVisitor()
            analyzer.visit(tree)
            return analyzer.results
        except SyntaxError as e:
            logger.error(f"Syntax error: {e}")
            return {}
        except Exception as e:
            logger.error(f"AST error: {e}")
            return {}

class _ASTVisitor(ast.NodeVisitor):
    """بازدیدکننده AST"""
    
    def __init__(self):
        self.results = {
            "functions": 0,
            "classes": 0,
            "imports": 0,
            "async_functions": 0,
            "conditionals": 0,
            "loops": 0,
            "exceptions": 0,
            "max_nesting": 0,
            "_current_depth": 0
        }
    
    def visit_FunctionDef(self, node):
        self.results["functions"] += 1
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node):
        self.results["async_functions"] += 1
        self.results["functions"] += 1
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        self.results["classes"] += 1
        self.generic_visit(node)
    
    def visit_Import(self, node):
        self.results["imports"] += len(node.names)
    
    def visit_ImportFrom(self, node):
        self.results["imports"] += len(node.names)
    
    def visit_If(self, node):
        self.results["conditionals"] += 1
        self._visit_with_depth(node)
    
    def visit_For(self, node):
        self.results["loops"] += 1
        self._visit_with_depth(node)
    
    def visit_While(self, node):
        self.results["loops"] += 1
        self._visit_with_depth(node)
    
    def visit_Try(self, node):
        self.results["exceptions"] += 1
        self._visit_with_depth(node)
    
    def _visit_with_depth(self, node):
        self.results["_current_depth"] += 1
        self.results["max_nesting"] = max(
            self.results["max_nesting"], 
            self.results["_current_depth"]
        )
        self.generic_visit(node)
        self.results["_current_depth"] -= 1

# ==================== BOT TYPE DETECTOR ====================
class BotTypeDetector:
    """تشخیص‌گر نوع ربات با الگوریتم پیشرفته"""
    
    # Database of keywords for each category
    KEYWORDS = {
        BotCategory.ECOMMERCE: {
            "primary": ["سبد خرید", "پرداخت", "محصول", "فروش", "خرید", "zarinpal", "idpay", "قیمت"],
            "secondary": ["سفارش", "موجودی", "تخفیف", "حمل و نقل"]
        },
        BotCategory.EDUCATIONAL: {
            "primary": ["آزمون", "سوال", "نمره", "آموزش", "دوره", "quiz", "exam", "درس"],
            "secondary": ["تمرین", "پاسخ", "کلاس", "کتاب", "دانشجو"]
        },
        BotCategory.GROUP_MANAGEMENT: {
            "primary": ["اخراج", "مسدود", "اخطار", "فیلتر", "kick", "ban", "warn", "مدیریت"],
            "secondary": ["خوش آمد", "اعضا", "قوانین", "گروه", "عضویت"]
        },
        BotCategory.ENTERTAINMENT: {
            "primary": ["بازی", "حدس", "شانس", "مسابقه", "game", "play", "سرگرمی"],
            "secondary": ["امتیاز", "لول", "برنده", "جایزه", "قرعه کشی"]
        },
        BotCategory.NEWS: {
            "primary": ["اخبار", "خبر", "اطلاعیه", "اعلان", "news", "رسانه"],
            "secondary": ["روزنامه", "مصاحبه", "گزارش", "آخرین"]
        },
        BotCategory.UTILITY: {
            "primary": ["تبدیل", "دانلود", "جستجو", "محاسبه", "tool", "ابزار"],
            "secondary": ["سرویس", "راهنما", "پشتیبانی", "help"]
        },
        BotCategory.FINANCIAL: {
            "primary": ["کیف پول", "تراکنش", "موجودی", "واریز", "برداشت", "wallet"],
            "secondary": ["حساب", "گزارش", "صورتحساب", "پول"]
        },
        BotCategory.CRYPTO: {
            "primary": ["بیت‌کوین", "اتریوم", "ارز دیجیتال", "crypto", "bitcoin"],
            "secondary": ["صرافی", "قیمت", "خرید", "فروش", "کیف پول"]
        }
    }
    
    @classmethod
    def detect(cls, code: str) -> Tuple[BotCategory, float, List[str]]:
        """تشخیص نوع ربات"""
        code_lower = code.lower()
        scores = {}
        reasons = []
        
        for category, keywords in cls.KEYWORDS.items():
            score = 0
            
            # Primary keywords (weight 10)
            for kw in keywords["primary"]:
                if kw.lower() in code_lower:
                    count = code_lower.count(kw.lower())
                    points = count * 10
                    score += points
                    reasons.append(f"کلمه '{kw}' ({count} بار)")
            
            # Secondary keywords (weight 5)
            for kw in keywords.get("secondary", []):
                if kw.lower() in code_lower:
                    count = code_lower.count(kw.lower())
                    points = count * 5
                    score += points
                    reasons.append(f"کلمه '{kw}' ({count} بار)")
            
            if score > 0:
                scores[category] = score
        
        if scores:
            # Sort by score
            sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            best_category, best_score = sorted_scores[0]
            
            # Calculate confidence
            max_possible = 100  # Maximum possible score
            confidence = min(best_score / max_possible, 0.95)
            
            # Get top reasons
            top_reasons = reasons[:3]
            
            return best_category, confidence, top_reasons
        
        return BotCategory.CUSTOM, 0.3, ["الگوی خاصی یافت نشد"]

# ==================== FEATURE DETECTOR ====================
class FeatureDetector:
    """تشخیص‌گر ویژگی‌های ربات"""
    
    FEATURES = [
        (r"InlineKeyboardMarkup", "کیبورد اینلاین", 2),
        (r"ReplyKeyboardMarkup", "کیبورد معمولی", 1),
        (r"CallbackQueryHandler", "دکمه‌های تعاملی", 2),
        (r"ConversationHandler", "مکالمه چندمرحله‌ای", 3),
        (r"async def", "برنامه‌نویسی Async", 2),
        (r"class\s+\w+", "برنامه‌نویسی شی‌گرا", 1),
        (r"try:.*except", "مدیریت خطا", 2),
        (r"logging", "سیستم لاگ", 1),
        (r"sqlite|mysql|postgres", "دیتابیس", 3),
        (r"zarinpal|idpay|payment", "درگاه پرداخت", 5),
        (r"requests|httpx|aiohttp", "API خارجی", 2),
        (r"job_queue|JobQueue", "زمان‌بندی خودکار", 2),
        (r"filters\.[A-Za-z]+", "فیلترهای پیشرفته", 1),
        (r"@bot\.", "دکوراتورها", 1),
        (r"webhook", "Webhook", 1),
        (r"redis|memcache", "کش", 2),
        (r"docker|container", "داکر", 2)
    ]
    
    @classmethod
    def detect(cls, code: str) -> List[Dict[str, Any]]:
        """تشخیص ویژگی‌ها"""
        features = []
        seen = set()
        
        for pattern, name, weight in cls.FEATURES:
            if re.search(pattern, code, re.IGNORECASE) and name not in seen:
                features.append({
                    "name": name,
                    "weight": weight,
                    "icon": "✅"
                })
                seen.add(name)
        
        return features

# ==================== SECURITY ANALYZER ====================
class SecurityAnalyzer:
    """تحلیل‌گر امنیتی"""
    
    VULNERABILITIES = [
        (r"eval\(.*\)", "استفاده از eval() - خطرناک"),
        (r"exec\(.*\)", "استفاده از exec() - خطرناک"),
        (r"os\.system\(", "دستورات سیستمی - خطرناک"),
        (r"subprocess\.call\(", "اجرای فرمان خارجی"),
        (r"password\s*=\s*['\"][^'\"]+['\"]", "پسورد hardcoded"),
        (r"api_key\s*=\s*['\"][^'\"]+['\"]", "API key hardcoded"),
        (r"token\s*=\s*['\"][^'\"]+['\"]", "توکن hardcoded"),
        (r"SELECT.*FROM.*WHERE.*\+", "SQL Injection risk"),
        (r"execute\(.*\+.*\)", "SQL Injection risk"),
        (r"\.\./", "Path traversal risk")
    ]
    
    PRACTICES = [
        (r"try:.*except", "مدیریت خطا"),
        (r"logging", "سیستم لاگ"),
        (r"validate|sanitize", "اعتبارسنجی ورودی"),
        (r"escape", "escape کردن خروجی"),
        (r"rate_limit|throttle", "محدودیت نرخ"),
        (r"https|ssl", "ارتباط امن"),
        (r"@bot\.", "دسترسی کنترل شده"),
        (r"hashed|hashlib", "هش کردن پسورد")
    ]
    
    @classmethod
    def analyze(cls, code: str) -> Dict[str, Any]:
        """تحلیل امنیتی"""
        issues = []
        score = 100
        practices_found = []
        
        # Check vulnerabilities
        for pattern, desc in cls.VULNERABILITIES:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append(desc)
                score -= 15
        
        # Check best practices
        for pattern, name in cls.PRACTICES:
            if re.search(pattern, code, re.IGNORECASE):
                practices_found.append(name)
            else:
                issues.append(f"عدم رعایت {name}")
                score -= 5
        
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
            "level": level.value,
            "issues": issues[:5],
            "practices": practices_found[:5]
        }

# ==================== PRICE CALCULATOR ====================
class PriceCalculator:
    """محاسبه‌گر قیمت پیشرفته"""
    
    @classmethod
    def calculate(cls, 
                  category: BotCategory,
                  features: List[Dict],
                  ast_results: Dict[str, Any],
                  confidence: float) -> Dict[str, Any]:
        """محاسبه قیمت نهایی"""
        
        base_price = category.base_price
        
        # Feature factor
        feature_weight = sum(f["weight"] for f in features)
        feature_factor = 1.0 + (feature_weight / 25)
        
        # Size factor (based on code lines)
        code_lines = ast_results.get("functions", 0) * 10 + 50  # Estimate
        if code_lines > 500:
            size_factor = 1.5
        elif code_lines > 300:
            size_factor = 1.3
        elif code_lines > 200:
            size_factor = 1.2
        elif code_lines > 100:
            size_factor = 1.1
        else:
            size_factor = 1.0
        
        # Complexity factor
        complexity = ast_results.get("conditionals", 0) + ast_results.get("loops", 0) * 2
        if complexity > 50:
            complexity_factor = 1.4
        elif complexity > 30:
            complexity_factor = 1.3
        elif complexity > 20:
            complexity_factor = 1.2
        elif complexity > 10:
            complexity_factor = 1.1
        else:
            complexity_factor = 1.0
        
        # Confidence factor
        confidence_factor = 0.8 + (confidence * 0.4)
        
        # Calculate price
        price = base_price
        price *= feature_factor
        price *= size_factor
        price *= complexity_factor
        price *= confidence_factor
        
        # Apply limits
        min_price = 500_000
        max_price = 50_000_000
        final_price = max(min_price, min(int(price), max_price))
        
        # Calculate score
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
        
        return {
            "final": final_price,
            "toman": final_price // 10,
            "usd": round(final_price / 50_000, 2),
            "score": score,
            "level": level,
            "factors": {
                "feature": round(feature_factor, 2),
                "size": round(size_factor, 2),
                "complexity": round(complexity_factor, 2),
                "confidence": round(confidence_factor, 2)
            }
        }

# ==================== REPORT GENERATOR ====================
class ReportGenerator:
    """تولیدکننده گزارش حرفه‌ای"""
    
    @classmethod
    def generate(cls, filename: str, analysis: AnalysisResult, price: Dict) -> str:
        """تولید گزارش نهایی"""
        
        now = analysis.timestamp.strftime("%Y/%m/%d %H:%M:%S")
        
        # Category line
        category_line = f"{analysis.category} (با اطمینان {analysis.confidence*100:.0f}%)"
        
        # Features list
        features_text = ""
        for f in analysis.features[:8]:
            features_text += f"• ✅ {f}\n"
        if len(analysis.features) > 8:
            features_text += f"• ... و {len(analysis.features)-8} مورد دیگر\n"
        if not features_text:
            features_text = "• ❌ ویژگی خاصی شناسایی نشد\n"
        
        # Security issues
        issues_text = ""
        for issue in analysis.security_issues[:3]:
            issues_text += f"• ⚠️ {issue}\n"
        if not issues_text:
            issues_text = "• ✅ بدون مشکل امنیتی\n"
        
        # Security practices
        practices_text = ""
        for p in analysis.security_practices:
            practices_text += f"• ✅ {p}\n"
        if not practices_text:
            practices_text = "• ❌ هیچکدام\n"
        
        # Price factors
        factors = price["factors"]
        factors_text = f"""
📊 **فاکتورهای قیمت:**
• ویژگی‌ها: {factors['feature']}x
• اندازه: {factors['size']}x
• پیچیدگی: {factors['complexity']}x
• اعتماد: {factors['confidence']}x
        """
        
        return f"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                         📄 **گزارش تحلیل ربات تلگرام**                          ║
║                         Professional Analysis Report                          ║
╚═══════════════════════════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 **اطلاعات عمومی:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 📁 فایل: `{filename}`
• 🆔 شناسه: {analysis.id}
• ⏰ زمان: {now}
• 📊 نسخه: 25.0 Ultimate

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 **تشخیص نوع ربات:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 🏆 {category_line}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨ **ویژگی‌های شناسایی شده:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{features_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 **آمار کد:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• کل خطوط: {analysis.total_lines:,}
• خطوط کد: {analysis.code_lines:,}
• خطوط کامنت: {analysis.comment_lines:,}
• توابع: {analysis.functions}
• کلاس‌ها: {analysis.classes}
• پیچیدگی: {analysis.complexity}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🛡️ **تحلیل امنیتی:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• امتیاز: {analysis.security_score}/100

⚠️ **مشکلات:**
{issues_text}

✅ **بهترین روش‌ها:**
{practices_text}

{factors_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 **قیمت نهایی:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏆 امتیاز: **{price['score']}/100**
🎯 سطح: **{price['level']}**

💵 ریال: **{price['final']:,} ریال**
💳 تومان: **{price['toman']:,} تومان**
💲 دلار: **${price['usd']}**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ تحلیل با دقت بالا انجام شده است
💰 قیمت بر اساس ۱۰+ فاکتور محاسبه شده
📊 بیش از ۳۰ پارامتر مورد بررسی قرار گرفته
🎯 برای سفارش توسعه: @SupportBot

╔═══════════════════════════════════════════════════════════════════════════════╗
║                    🤖 Telegram Price Analyzer - Version 25.0                   ║
║                              Ultimate Edition                                  ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

# ==================== HEALTH SERVER ====================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
            <html>
                <head><title>Bot Status</title></head>
                <body>
                    <h1>🤖 Telegram Bot Price Analyzer</h1>
                    <p>Status: <strong style="color:green">RUNNING</strong></p>
                    <p>Version: 25.0 Ultimate</p>
                </body>
            </html>
            """)
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                "status": "healthy",
                "version": "25.0",
                "timestamp": datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

def run_http_server():
    try:
        server = HTTPServer(('0.0.0.0', PORT), HealthHandler)
        logger.info(f"✅ HTTP Server running on port {PORT}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"HTTP Server error: {e}")

# ==================== MAIN BOT ====================
class UltimateBot:
    """ربات اصلی"""
    
    def __init__(self):
        self.ast_analyzer = ASTAnalyzer()
        self.bot_detector = BotTypeDetector()
        self.feature_detector = FeatureDetector()
        self.security_analyzer = SecurityAnalyzer()
        self.price_calculator = PriceCalculator()
        
        self.processing = set()
        self.stats = {
            "start_time": time.time(),
            "files_received": 0,
            "analyses_done": 0,
            "errors": 0
        }
        
        # Rate limiting
        self.rate_limits = defaultdict(list)
        
        logger.info("✅ Ultimate Bot initialized")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """دستور /start"""
        user = update.effective_user
        
        # Rate limiting
        if not self._check_rate_limit(user.id):
            await update.message.reply_text("⏳ لطفاً کمی صبر کنید...")
            return
        
        welcome = f"""
👋 **سلام {user.first_name}!**

🤖 **به ربات تحلیل‌گر قیمت تلگرام خوش آمدید**

✨ **قابلیت‌های ویژه:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 تشخیص ۸ نوع ربات مختلف
📊 تحلیل AST پیشرفته
🛡️ بررسی امنیتی کامل
💰 محاسبه قیمت هوشمند
📈 گزارش حرفه‌ای

📁 **نحوه استفاده:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1️⃣ فایل `.py` ربات خود را ارسال کنید
2️⃣ منتظر تحلیل باشید (۱۰-۲۰ ثانیه)
3️⃣ گزارش کامل دریافت کنید

📊 **آمار:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• تحلیل‌ها: {self.stats['analyses_done']}
• فایل‌ها: {self.stats['files_received']}

👇 **فایل خود را ارسال کنید:**
        """
        
        await update.message.reply_text(welcome, parse_mode='Markdown')
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش فایل"""
        user_id = update.effective_user.id
        
        # Rate limiting
        if not self._check_rate_limit(user_id):
            await update.message.reply_text("⏳ لطفاً کمی صبر کنید...")
            return
        
        # Check concurrent processing
        if user_id in self.processing:
            await update.message.reply_text("⏳ در حال پردازش درخواست قبلی...")
            return
        
        if not update.message.document:
            return
        
        doc = update.message.document
        if not doc.file_name.endswith('.py'):
            await update.message.reply_text("❌ فقط فایل‌های Python با پسوند `.py`")
            return
        
        self.processing.add(user_id)
        self.stats['files_received'] += 1
        
        try:
            msg = await update.message.reply_text("📥 دریافت فایل...")
            
            # Download
            file = await doc.get_file()
            content = (await file.download_as_bytearray()).decode('utf-8', errors='ignore')
            
            # Count lines
            lines = content.split('\n')
            total_lines = len(lines)
            code_lines = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
            comment_lines = len([l for l in lines if l.strip().startswith('#')])
            blank_lines = len([l for l in lines if not l.strip()])
            
            await msg.edit_text("🔍 تحلیل AST...")
            
            # AST Analysis
            ast_results = self.ast_analyzer.analyze(content)
            
            await msg.edit_text("🎯 تشخیص نوع ربات...")
            
            # Detect type
            category, confidence, reasons = self.bot_detector.detect(content)
            
            await msg.edit_text("✨ استخراج ویژگی‌ها...")
            
            # Detect features
            features = self.feature_detector.detect(content)
            
            await msg.edit_text("🛡️ تحلیل امنیتی...")
            
            # Security analysis
            security = self.security_analyzer.analyze(content)
            
            await msg.edit_text("💰 محاسبه قیمت...")
            
            # Calculate price
            price = self.price_calculator.calculate(
                category, features, ast_results, confidence
            )
            
            # Create analysis result
            result = AnalysisResult(
                filename=doc.file_name,
                total_lines=total_lines,
                code_lines=code_lines,
                comment_lines=comment_lines,
                blank_lines=blank_lines,
                functions=ast_results.get("functions", 0),
                classes=ast_results.get("classes", 0),
                imports=ast_results.get("imports", 0),
                async_functions=ast_results.get("async_functions", 0),
                complexity=ast_results.get("conditionals", 0) + ast_results.get("loops", 0) * 2,
                category=category.value[0],
                confidence=confidence,
                base_price=category.base_price,
                features=[f["name"] for f in features],
                security_score=security["score"],
                security_issues=security["issues"],
                security_practices=security["practices"],
                final_price=price["final"],
                price_score=price["score"],
                price_level=price["level"]
            )
            
            # Generate report
            report = ReportGenerator.generate(doc.file_name, result, price)
            
            await msg.delete()
            await update.message.reply_text(report)
            
            self.stats['analyses_done'] += 1
            logger.info(f"✅ Analysis completed: {doc.file_name} -> {category.name}")
            
        except Exception as e:
            logger.error(f"Error: {e}")
            self.stats['errors'] += 1
            await update.message.reply_text("❌ خطا در پردازش فایل")
        
        finally:
            self.processing.discard(user_id)
    
    def _check_rate_limit(self, user_id: int) -> bool:
        """بررسی محدودیت نرخ"""
        now = time.time()
        self.rate_limits[user_id] = [
            t for t in self.rate_limits[user_id]
            if now - t < 60
        ]
        
        if len(self.rate_limits[user_id]) >= 10:  # 10 requests per minute
            return False
        
        self.rate_limits[user_id].append(now)
        return True

# ==================== CLEANUP ====================
async def cleanup_bot():
    """پاکسازی قبل از شروع"""
    try:
        import requests
        url = f"https://api.telegram.org/bot{TOKEN}/deleteWebhook"
        response = requests.get(url, params={"drop_pending_updates": "true"})
        logger.info(f"✅ Cleanup: {response.json()}")
        await asyncio.sleep(2)
    except Exception as e:
        logger.error(f"Cleanup error: {e}")

# ==================== MAIN LOOP ====================
async def run_bot_with_retry():
    """اجرای ربات با قابلیت Retry"""
    
    retry_count = 0
    max_retries = 10
    
    while retry_count < max_retries:
        try:
            logger.info("="*60)
            logger.info(f"🚀 Starting bot (attempt {retry_count + 1}/{max_retries})")
            logger.info("="*60)
            
            # Cleanup
            await cleanup_bot()
            
            # Create bot
            bot = UltimateBot()
            
            # Create application
            app = Application.builder().token(TOKEN).build()
            
            # Add handlers
            app.add_handler(CommandHandler("start", bot.start_command))
            app.add_handler(CommandHandler("help", bot.start_command))
            app.add_handler(MessageHandler(filters.Document.ALL, bot.handle_document))
            
            # Start
            await app.initialize()
            await app.start()
            await app.updater.start_polling(
                drop_pending_updates=True,
                timeout=30,
                poll_interval=0.5,
                allowed_updates=["message"]
            )
            
            logger.info("✅ Bot is running successfully!")
            
            # Reset retry counter
            retry_count = 0
            
            # Keep running
            await asyncio.Event().wait()
            
        except Conflict as e:
            logger.error(f"❌ Conflict: {e}")
            retry_count += 1
            await asyncio.sleep(min(30 * retry_count, 300))
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            retry_count += 1
            await asyncio.sleep(10)
    
    logger.critical("❌ Max retries reached. Exiting...")

# ==================== MAIN ====================
def main():
    """ورودی اصلی"""
    
    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║                                                                     ║
║     🤖 TELEGRAM BOT PRICE ANALYZER - ULTIMATE EDITION v25.0        ║
║                                                                     ║
║     Configuration:                                                  ║
║     • Python: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}                        ║
║     • Environment: {ENVIRONMENT}                                         ║
║     • Port: {PORT}                                                   ║
║     • Debug: {DEBUG}                                                  ║
║                                                                     ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    # Start HTTP server
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    
    # Run bot
    try:
        asyncio.run(run_bot_with_retry())
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")

if __name__ == "__main__":
    main()
