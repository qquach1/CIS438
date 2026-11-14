#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Turn an Apache access log into one clean DataFrame, following dataloader.ipynb step by step.

parse_log() and add_features() are notebook sections 2-4 as plain pandas, and load_data() wraps
them in st.cache_data for the dashboard. On top of the notebook's columns it adds a few the extra
tabs use: browser and device, location (from GeoLite2-City.mmdb), course, AI tools and probes.
"""

import ipaddress
import os
import re
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

try:  # names browsers, operating systems and crawlers -- pip install user-agents
    from user_agents import parse as parse_user_agent
except ImportError:
    parse_user_agent = None

try:  # reads GeoLite2-City.mmdb for the visitor map -- pip install maxminddb
    import maxminddb
except ImportError:
    maxminddb = None

HERE = Path(__file__).parent
LOG_PATH = HERE / "weblog.txt"  # adjust this path if weblog.txt lives elsewhere
GEO_DB_PATH = HERE / "GeoLite2-City.mmdb"

# ── Section 2: one regex pulls every field out of a line ─────────────────────
# IP - - [DD/Mon/YYYY:HH:MM:SS +TZ] "METHOD /path HTTP/1.x" STATUS SIZE "REFERER" "USER-AGENT"
LOG_PATTERN = re.compile(
    r'(?P<ip>\S+) \S+ \S+ '
    r'\[(?P<datetime>[^\]]+)\] '
    r'"(?P<method>\S+) (?P<url>\S+) \S+" '
    r'(?P<status>\d{3}) (?P<size>\S+) '
    r'"(?P<referer>[^"]*)" '
    r'"(?P<user_agent>[^"]*)"'
)
RAW_COLUMNS = ["ip", "datetime_str", "method", "url", "status", "size", "referer", "user_agent"]

# ── Section 4: rules behind the derived columns ──────────────────────────────
STATIC_EXTENSIONS = {
    '.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.ico',
    '.svg', '.woff', '.woff2', '.ttf', '.eot', '.map',
}
STATIC_PREFIXES = ('/css/', '/js/', '/fonts/', '/images/', '/static/', '/socket.io/')

BOT_PATTERNS = re.compile(
    r'bot|crawler|spider|crawl|slurp|bingbot|googlebot|feedcrawler|'
    r'yandex|baidu|semrush|ahref|mj12|dotbot|petalbot', re.I
)

STATUS_BINS = [0, 199, 299, 399, 499, 599]
STATUS_LABELS = ['1xx Info', '2xx Success', '3xx Redirect', '4xx Client Err', '5xx Server Err']

# ── Extra rules, beyond the notebook ─────────────────────────────────────────
# AI assistants and crawlers, by the name they put in their user agent
AI_AGENTS = {
    "GPTBot": "OpenAI", "ChatGPT-User": "OpenAI", "OAI-SearchBot": "OpenAI",
    "ClaudeBot": "Anthropic", "Claude-User": "Anthropic", "Claude-SearchBot": "Anthropic",
    "Claude-Web": "Anthropic", "anthropic-ai": "Anthropic",
    "PerplexityBot": "Perplexity", "Perplexity-User": "Perplexity",
    "Google-CloudVertexBot": "Google", "meta-externalagent": "Meta", "meta-externalfetcher": "Meta",
    "Bytespider": "ByteDance", "CCBot": "Common Crawl", "Amazonbot": "Amazon",
    "cohere-ai": "Cohere", "MistralAI-User": "Mistral", "DuckAssistBot": "DuckDuckGo",
    "YouBot": "You.com", "AI2Bot": "Allen Institute for AI", "Diffbot": "Diffbot",
}
_AI_NAMES = {name.lower(): name for name in AI_AGENTS}
AI_AGENT_PATTERN = re.compile("|".join(re.escape(name) for name in sorted(AI_AGENTS, key=len, reverse=True)), re.I)

# Scripts and headless browsers: automated, but BOT_PATTERNS lets them through as human
SCRIPT_PATTERN = re.compile(
    r'^-?$|python|curl|wget|go-http|headless|httpclient|okhttp|java/|libwww|zgrab|masscan|nmap|'
    r'scrapy|aiohttp|axios|node-fetch', re.I
)

# Requests for software this site doesn't run (WordPress, PHP, leaked config files) are vulnerability scans
PROBE_PATTERN = re.compile(
    r'wp-|\.php|\.env|\.git/|\.aws/|\.ds_store|cgi-bin|xmlrpc|phpmyadmin|eval-stdin|alfacgiapi|autodiscover',
    re.I
)

COURSE_PATTERN = re.compile(r'/([a-z]{3}\d{2}[0-9x])(?=/|$)', re.I)  # /course/cis511, /gba411/..., /msm50x
AI_TOOL_PATTERN = re.compile(r'chatgpt', re.I)  # the site's own ChatGPT pages, e.g. /community/gba411/chatgpt

# Named crawler in a user agent ("bingbot/2.0" -> "bingbot") when the parser can't name it
CRAWLER_TOKEN = re.compile(r'([a-z][\w.\-]*?(?:bot|crawler|spider|slurp))', re.I)

# What each column holds -- shown in the dashboard's Data tab
COLUMN_NOTES = {
    'ip': 'Visitor IP address',
    'datetime_str': 'Timestamp text exactly as logged',
    'method': 'HTTP method: GET, POST, …',
    'url': 'Requested URL, query string included',
    'status': 'HTTP status code the server answered with',
    'size': 'Response size in bytes (a "-" becomes 0)',
    'referer': 'Page that led to this request ("-" when none)',
    'user_agent': 'Browser or crawler identification string',
    'timestamp': 'Parsed time, converted to UTC',
    'date': 'Calendar day, on the selected clock',
    'hour': 'Hour of day 0–23, on the selected clock',
    'day_of_week': '0 = Monday … 6 = Sunday, on the selected clock',
    'month': 'Year and month such as 2023-07, on the selected clock',
    'is_static': 'CSS, JS, image, font or socket.io request',
    'is_bot': 'User agent names a crawler (BOT_PATTERNS)',
    'status_cat': 'Status bucket: 2xx Success, 3xx Redirect, …',
    'section': 'First URL path segment, such as /course',
    'local_time': "Time on the server's own clock",
    'path': 'URL without its query string',
    'browser': 'Browser family, from user-agents',
    'os': 'Operating system, from user-agents',
    'device': 'Desktop, Mobile, Tablet, Bot or Other',
    'crawler': 'Crawler name, on bot requests',
    'ai_agent': 'AI assistant or crawler named in the user agent',
    'ai_company': 'Company behind ai_agent',
    'is_script': 'Script or headless browser that BOT_PATTERNS misses',
    'referer_host': 'Host name in the referer',
    'referer_type': 'Direct, Internal (same site) or External',
    'referer_path': 'Referring page, for links within the site',
    'course': 'Course code in the URL, such as cis511',
    'is_probe': "Scan for software the site doesn't run (WordPress, PHP, .env)",
    'ai_page': 'ChatGPT page the request belongs to',
    'ai_course': 'Course of that ChatGPT page ("general" for none)',
    'country': 'Country, from GeoLite2 ("Private network" for 192.168.x.x)',
    'city': 'City, from GeoLite2',
    'latitude': 'Latitude, from GeoLite2',
    'longitude': 'Longitude, from GeoLite2',
}


# ── Section 3: parse every line into a record ────────────────────────────────

def parse_log(lines):
    """One record per line the regex understands. Returns (DataFrame, number of lines it couldn't read)."""
    records, skipped = [], 0
    for line in lines:
        m = LOG_PATTERN.match(line)
        if not m:
            skipped += bool(line.strip())
            continue
        d = m.groupdict()
        try:
            size = int(d['size']) if d['size'] != '-' else 0
        except ValueError:
            size = 0
        records.append({
            'ip':           d['ip'],
            'datetime_str': d['datetime'],
            'method':       d['method'],
            'url':          d['url'],
            'status':       int(d['status']),
            'size':         size,
            'referer':      d['referer'],
            'user_agent':   d['user_agent'],
        })
    return pd.DataFrame(records, columns=RAW_COLUMNS), skipped


# ── Section 4: feature engineering ───────────────────────────────────────────

def is_static(url):
    """CSS, JS, images and fonts -- decorative files, not content."""
    lower = url.lower()
    if os.path.splitext(lower)[1] in STATIC_EXTENSIONS:
        return True
    if lower.startswith(STATIC_PREFIXES):
        return True
    return 'favicon' in lower


def section_of(url):
    """First URL path segment, e.g. /course or /account."""
    return '/' + url.strip('/').split('/')[0] if url != '/' else '/'


def add_clock_columns(df, clock):
    """date, hour, day_of_week and month read off one clock: UTC as in the notebook, or the server's own."""
    df['date'] = clock.dt.date
    df['hour'] = clock.dt.hour
    df['day_of_week'] = clock.dt.day_of_week  # 0 = Monday
    df['month'] = clock.dt.to_period('M').astype(str)
    return df


def use_server_clock(df):
    """Swap the UTC clock columns for the server's local time (the clock the log was written in)."""
    return add_clock_columns(df, df['local_time'])


def device_type(info, bot):
    if bot:
        return 'Bot'
    if info is None:
        return 'Unknown'
    if info.is_tablet:
        return 'Tablet'
    if info.is_mobile:
        return 'Mobile'
    if info.is_pc:
        return 'Desktop'
    return 'Other'


def crawler_name(user_agent, info):
    """A short name for a bot: the parser's when it knows the crawler, else the word that gave it away."""
    if info is not None and info.is_bot and info.browser.family != 'Other':
        return info.browser.family
    token = CRAWLER_TOKEN.search(user_agent)
    if token:
        return token.group(1)
    hit = BOT_PATTERNS.search(user_agent)
    return hit.group(0) if hit else 'Unknown'


def describe_user_agents(user_agents):
    """Bot flag, browser, OS, device and crawler names for each distinct user agent (parsed once each)."""
    rows = []
    for ua in user_agents:
        info = parse_user_agent(ua) if parse_user_agent else None
        bot = bool(BOT_PATTERNS.search(ua))
        ai = AI_AGENT_PATTERN.search(ua)
        ai_agent = _AI_NAMES[ai.group(0).lower()] if ai else None
        rows.append({
            'user_agent': ua,
            'is_bot': bot,
            'browser': info.browser.family if info else 'Unknown',
            'os': info.os.family if info else 'Unknown',
            'device': device_type(info, bot),
            'crawler': crawler_name(ua, info) if bot else None,
            'ai_agent': ai_agent,
            'ai_company': AI_AGENTS.get(ai_agent),
            'is_script': not bot and bool(SCRIPT_PATTERN.search(ua)),
        })
    return pd.DataFrame(rows).set_index('user_agent')


def place_of(reader, ip):
    """Country, city and coordinates for one IP address."""
    try:
        address = ipaddress.ip_address(ip)
    except ValueError:
        return dict(country='Unknown', city=None, latitude=np.nan, longitude=np.nan)
    if address.is_private or address.is_loopback:
        return dict(country='Private network', city=None, latitude=np.nan, longitude=np.nan)
    record = reader.get(ip) or {}
    country = (record.get('country') or record.get('registered_country') or {}).get('names', {})
    city = (record.get('city') or {}).get('names', {})
    location = record.get('location') or {}
    return dict(country=country.get('en', 'Unknown'), city=city.get('en'),
                latitude=location.get('latitude', np.nan), longitude=location.get('longitude', np.nan))


def locate_ips(ips, db_path=GEO_DB_PATH):
    """Where each IP is, from the GeoLite2 database. None when maxminddb or the database is missing."""
    if maxminddb is None or not Path(db_path).exists():
        return None
    with maxminddb.open_database(str(db_path)) as reader:
        rows = [{'ip': ip, **place_of(reader, ip)} for ip in ips]
    return pd.DataFrame(rows).set_index('ip')


def add_features(df_raw):
    """Notebook section 4, plus the dashboard's extra columns."""
    # ── Timestamp parsing ───────────────────────────────────────────────────
    df = df_raw.copy()
    df['timestamp'] = pd.to_datetime(df['datetime_str'], format='%d/%b/%Y:%H:%M:%S %z',
                                     errors='coerce', utc=True)
    df = df.dropna(subset=['timestamp']).reset_index(drop=True)  # drop unparseable lines
    add_clock_columns(df, df['timestamp'].dt.tz_convert(None))

    # ── Static resources, bots, status categories, sections ─────────────────
    df['is_static'] = df['url'].map(is_static)
    agents = describe_user_agents(df['user_agent'].unique())  # BOT_PATTERNS runs once per distinct agent
    df['is_bot'] = df['user_agent'].map(agents['is_bot'])
    df['status_cat'] = pd.cut(df['status'], bins=STATUS_BINS, labels=STATUS_LABELS)
    df['section'] = df['url'].map(section_of)

    # ── Extras the dashboard uses ───────────────────────────────────────────
    # The server's wall clock: the same timestamp text without its UTC offset
    df['local_time'] = pd.to_datetime(df['datetime_str'].str[:20], format='%d/%b/%Y:%H:%M:%S', errors='coerce')
    df['path'] = df['url'].str.split('?', n=1).str[0]  # url without its query string

    for col in ['browser', 'os', 'device', 'crawler', 'ai_agent', 'ai_company', 'is_script']:
        df[col] = df['user_agent'].map(agents[col])

    # Where each request came from: typed in or bookmarked, another page on this site, or another site
    host = df['referer'].str.extract(r'^[a-z][a-z0-9+.\-]*://([^/:?#]+)', flags=re.I)[0].str.lower()
    bare = host.str.removeprefix('www.')  # www.huaxia.ai is the same site as huaxia.ai
    site = bare.mode().iloc[0] if bare.notna().any() else None  # pages on the site refer to its own assets most
    internal = bare.eq(site).fillna(False).astype(bool)
    df['referer_host'] = host
    df['referer_type'] = np.select([df['referer'].isin(['-', '']), internal], ['Direct', 'Internal'], 'External')
    df['referer_path'] = (df['referer'].str.extract(r'^[a-z][a-z0-9+.\-]*://[^/?#]+(/[^?#]*)?', flags=re.I)[0]
                          .fillna('/').where(internal))

    df['course'] = df['path'].str.extract(COURSE_PATTERN)[0].str.lower()
    df['is_probe'] = df['path'].str.contains(PROBE_PATTERN)

    # The ChatGPT tool chats over socket.io, so its traffic carries the tool's page in the referer
    on_page = df['path'].str.contains(AI_TOOL_PATTERN)
    from_page = df['referer_path'].fillna('').str.contains(AI_TOOL_PATTERN)
    df['ai_page'] = df['path'].where(on_page, df['referer_path'].where(from_page))
    df['ai_course'] = (df['ai_page'].str.extract(COURSE_PATTERN)[0].str.lower()
                       .fillna('general').where(df['ai_page'].notna()))

    places = locate_ips(df['ip'].unique())
    if places is None:
        df['country'], df['city'], df['latitude'], df['longitude'] = 'Unknown', None, np.nan, np.nan
    else:
        df = df.join(places, on='ip')
    return df


# ── Section 6: the three slices the dashboard uses ──────────────────────────

def split_traffic(df):
    """(df_pages, df_humans): content pages only, then content pages from people rather than crawlers."""
    df_pages = df[~df['is_static']]
    df_humans = df_pages[~df_pages['is_bot']]
    return df_pages, df_humans


# ── Section 7: headline numbers ─────────────────────────────────────────────

def site_kpis(df):
    return dict(
        total_requests=len(df),
        unique_visitors=df['ip'].nunique(),
        bandwidth_gb=df['size'].sum() / 1e9,
        error_rate=(df['status'] >= 400).mean() if len(df) else 0.0,
        bot_pct=df['is_bot'].mean() if len(df) else 0.0,
    )


# ── Section 9: visitor engagement segments ──────────────────────────────────

SEGMENTS = {'Bounced': '1 request', 'Casual': '2–4', 'Engaged': '5–15', 'Power User': '16+'}


def segment(n):
    if n == 1:
        return 'Bounced'
    if n <= 4:
        return 'Casual'
    if n <= 15:
        return 'Engaged'
    return 'Power User'


def engagement_segments(df_humans):
    """Visitors (IPs) per segment, in segment order."""
    visit_counts = df_humans.groupby('ip').size()
    counts = visit_counts.map(segment).value_counts().reindex(list(SEGMENTS), fill_value=0)
    return pd.DataFrame({'segment': counts.index, 'requests_per_ip': list(SEGMENTS.values()),
                         'visitors': counts.values})


# ── Cached loader for the dashboard ─────────────────────────────────────────

@st.cache_data(show_spinner="Parsing the log…")
def load_data(log_bytes):
    """Sections 2-4 in one cached call: raw log bytes in, (DataFrame, lines skipped) out."""
    lines = log_bytes.decode('utf-8', errors='ignore').splitlines()
    df_raw, skipped = parse_log(lines)
    if df_raw.empty:  # not an access log; the app says so instead of charting nothing
        return df_raw, skipped
    return add_features(df_raw), skipped
