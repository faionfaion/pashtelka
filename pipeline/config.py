"""Pipeline configuration: paths, models, constants."""

from pathlib import Path

# Project root
ROOT = Path(__file__).resolve().parent.parent

# Directories
CONTENT_DIR = ROOT / "content"
STATE_DIR = ROOT / "state"
SCRIPTS_DIR = ROOT / "scripts"
PROMPTS_DIR = ROOT / "pipeline" / "prompts"
GATSBY_DIR = ROOT / "gatsby"
IMAGES_DIR = GATSBY_DIR / "static" / "images"

# Scripts
SEND_POST = SCRIPTS_DIR / "send_post.py"
DEPLOY_SH = GATSBY_DIR / "deploy-gh.sh"

# Site
SITE_BASE_URL = "https://pashtelka.faion.net"

# Single language — no translation pipeline needed
LANG = "ua"

# Models per stage (all Opus per project convention)
MODEL_COLLECT = "opus"
MODEL_RESEARCH = "opus"
MODEL_GENERATE = "opus"
MODEL_REVIEW = "opus"
MODEL_TG = "opus"
MODEL_IMAGE = "opus"  # image prompt generation
MODEL_VERIFY = "opus"

# Review loop limits
MAX_REVIEW_CYCLES = 3
MAX_TG_REVIEW_CYCLES = 2

# SDK retry config
RETRY_MAX_ATTEMPTS = 3
RETRY_BASE_DELAY = 5.0
RETRY_MAX_DELAY = 60.0

# Telegram
TG_BOT_TOKEN = "8585090528:AAHWmjiT9TIlmdtz0x8Q_YpUCnP3APEx7i8"
TG_CHANNEL_ID = "-1003726391778"
TG_CHANNEL_USERNAME = "pashtelka_news"
TG_BUTTON_LABEL = "Читати повністю →"

# Silent mode: sound ON only during this window (Lisbon time)
SOUND_ON_START = 8
SOUND_ON_END = 22

# Max TG caption length (safe for multi-byte UTF-8)
MAX_TG_CAPTION = 900

# Publishing schedule (Lisbon time hours)
SLOTS = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21]

# Slot types: which slots get which content type
SLOT_TYPES = {
    8: "weather",       # Morning greeting + weather
    12: "material",     # Compiled article 1
    16: "material",     # Compiled article 2
    21: "digest",       # Evening digest
    # All other slots: "news"
}

# Content type configs
CONTENT_TYPES = {
    "news": {"min_words": 300, "max_words": 600},
    "utility": {"min_words": 150, "max_words": 400},
    "immigration": {"min_words": 400, "max_words": 800},
    "material": {"min_words": 600, "max_words": 1500},
    "digest": {"min_words": 500, "max_words": 1000},
    "weather": {"min_words": 100, "max_words": 250},
    "guide": {"min_words": 800, "max_words": 2000},
}

# Author persona
AUTHOR_NAME = "Оксана Литвин"
AUTHOR_NAME_EN = "Oksana Lytvyn"
AUTHOR_BIO = "Українська журналістка в Лісабоні з 2018 року"

# City hashtags
CITY_TAGS = {
    "lisbon": "#Лісабон",
    "porto": "#Порту",
    "faro": "#Фару",
    "algarve": "#Алгарве",
    "greater_lisbon": "#ВеликийЛісабон",
    "cascais": "#Кашкайш",
    "sintra": "#Сінтра",
    "albufeira": "#Албуфейра",
    "coimbra": "#Коїмбра",
    "braga": "#Брага",
    "portugal": "#Португалія",
}

# Topic hashtags
TOPIC_TAGS = {
    "news": "#Новини",
    "immigration": "#Імміграція",
    "taxes": "#Податки",
    "transport": "#Транспорт",
    "weather": "#Погода",
    "utilities": "#Комуналка",
    "healthcare": "#Здоровя",
    "education": "#Освіта",
    "employment": "#Робота",
    "housing": "#Житло",
    "safety": "#Безпека",
    "culture": "#Культура",
    "sports": "#Спорт",
    "diaspora": "#Діаспора",
    "digest": "#Дайджест",
    "guide": "#Гайд",
    "material": "#Матеріал",
}

# RSS feeds for news collection
RSS_FEEDS = {
    "rtp_latest": "https://www.rtp.pt/noticias/rss",
    "rtp_country": "https://www.rtp.pt/noticias/rss/pais",
    "rtp_economy": "https://www.rtp.pt/noticias/rss/economia",
    "rtp_world": "https://www.rtp.pt/noticias/rss/mundo",
    "rtp_culture": "https://www.rtp.pt/noticias/rss/cultura",
    "publico": "https://feeds.feedburner.com/PublicoRSS",
    # "observador": "https://observador.pt/feed/",  # 403 Forbidden
    "cmjornal": "https://www.cmjornal.pt/rss",
}

# IPMA API endpoints
IPMA_FORECAST = "https://api.ipma.pt/open-data/forecast/meteorology/cities/daily/{city_id}.json"
IPMA_WARNINGS = "https://api.ipma.pt/open-data/forecast/warnings/warnings_www.json"
IPMA_LOCATIONS = "https://api.ipma.pt/open-data/distrits-islands.json"

# IPMA city IDs
IPMA_CITIES = {
    "Lisboa": 1110600,
    "Porto": 1131200,
    "Faro": 806011,
    "Cascais": 1104300,
    "Sintra": 1111500,
    "Coimbra": 612300,
    "Braga": 303200,
}

# Metro Lisboa API
METRO_LISBOA_API = "http://app.metrolisboa.pt/status/getLinhas.php"
