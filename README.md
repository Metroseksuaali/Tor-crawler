# Tor Crawler

🔍 Secure and ethical web crawler for researching .onion sites on the Tor network.

**Purpose:** Research and educational use
**Technology:** Python 3.9+ | aiohttp | BeautifulSoup | Tor SOCKS5

---

## 📋 Table of Contents

- [Features](#-features)
- [Technology Choice](#-technology-choice)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Usage](#-usage)
- [Configuration](#-configuration)
- [Data Processing](#-data-processing)
- [Architecture](#-architecture)
- [Security & Ethics](#-security--ethics)
- [Troubleshooting](#-troubleshooting)

---

## ✨ Features

- ✅ **Tor Integration:** All traffic goes through Tor network (SOCKS5 proxy)
- ✅ **Asynchronous:** Efficient parallel processing with asyncio
- ✅ **Rate Limiting:** Configurable delay between requests (ethical crawling)
- ✅ **BFS Algorithm:** Breadth-first traversal with depth limiting
- ✅ **Two Storage Options:** JSON (NDJSON) and SQLite
- ✅ **HTML Parsing:** BeautifulSoup + link filtering
- ✅ **Error Handling:** Timeouts, connection errors, retry logic
- ✅ **Domain Filtering:** .onion sites only, configurable domain restrictions
- ✅ **CLI Interface:** Easy command-line usage
- ✅ **Resumable Crawling:** Stop and continue later

---

## 🎯 Technology Choice

### Why Python + aiohttp?

**Compared alternatives:**
1. **Python + aiohttp** ⭐ (selected)
2. Node.js + axios
3. Rust + reqwest

**Selection criteria:**
- ✅ Mature Tor ecosystem (stem library)
- ✅ Excellent scraping support (BeautifulSoup)
- ✅ Asynchronous execution (asyncio)
- ✅ Easy to learn and maintain
- ✅ Data science integration (pandas, numpy)

---

## 🔧 Prerequisites

### 1. Python 3.9+

Check version:
```bash
python3 --version
```

### 2. Tor

The crawler requires a running Tor instance.

**Linux/macOS:**
```bash
# Debian/Ubuntu
sudo apt install tor
sudo systemctl start tor

# macOS (Homebrew)
brew install tor
brew services start tor
```

**Windows:**
- Download [Tor Expert Bundle](https://www.torproject.org/download/tor/)
- OR start Tor Browser (includes SOCKS proxy)

**Docker:**
```bash
docker run -d -p 9050:9050 --name tor dperson/torproxy
```

**Test that Tor works:**
```bash
curl --socks5-hostname 127.0.0.1:9050 https://check.torproject.org/api/ip
```

Should return: `{"IsTor": true, ...}`

---

## 📦 Installation

### 1. Clone repository
```bash
git clone <repository-url>
cd Tor-crawler
```

### 2. Create virtual environment (recommended)
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate  # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure crawler

Copy example configuration:
```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml`:
```yaml
crawler:
  start_url: "http://your-target.onion"  # ⚠️ Add .onion address here
  max_depth: 2
  max_pages: 50
  request_delay: 3.0  # IMPORTANT: Don't remove!
```

---

## 🚀 Usage

### Basic command

```bash
python main.py --config config.yaml
```

### Command line parameters

```bash
# Use all settings from command line
python main.py --start-url "http://example.onion" --max-pages 50 --max-depth 2

# SQLite storage
python main.py --config config.yaml --storage sqlite

# Change rate limiting
python main.py --config config.yaml --delay 5.0

# Debug mode
python main.py --config config.yaml --log-level DEBUG
```

### Example run

```bash
# Start with small test
python main.py \
  --start-url "http://example.onion" \
  --max-pages 10 \
  --max-depth 1 \
  --delay 3.0 \
  --storage json
```

### Interruption and resuming

You can interrupt crawling (`Ctrl+C`) and resume later:
```bash
# Crawler automatically loads previously visited URLs
python main.py --config config.yaml
```

---

## ⚙️ Configuration

### YAML file (config.yaml)

```yaml
# Tor settings
tor:
  proxy_host: "127.0.0.1"
  proxy_port: 9050
  control_port: 9051
  use_stem: false  # true = enables IP rotation

# Crawler settings
crawler:
  start_url: "http://example.onion"
  max_depth: 3              # How many link levels
  max_pages: 100            # Maximum total pages
  max_pages_per_domain: 50  # Maximum per domain
  request_delay: 2.0        # Seconds between requests
  request_timeout: 30       # Timeout in seconds
  follow_external_onion: true  # Follow other .onion domains
  allowed_domains: []       # Empty = all, or list: ["a.onion", "b.onion"]

# Storage
storage:
  storage_type: "json"      # "json" or "sqlite"
  output_dir: "./data"
  json_filename: "crawled_pages.json"
  sqlite_filename: "crawler.db"

# Logging
log_level: "INFO"
```

### Environment variables

Create `.env` file (copy `.env.example`):
```env
TOR_PROXY_HOST=127.0.0.1
TOR_PROXY_PORT=9050
START_URL=http://example.onion
MAX_DEPTH=3
MAX_PAGES=100
LOG_LEVEL=INFO
```

**Priority:** Command line > Environment variables > YAML

---

## 📊 Data Processing

### JSON storage (NDJSON)

Each line = one JSON object:

```json
{"url": "http://example.onion/page1", "status": 200, "title": "Example", "depth": 1, "timestamp": "2025-01-01T12:00:00", "links": ["http://example.onion/page2"], "text_preview": "...", "meta": {}, "error": null}
{"url": "http://example.onion/page2", "status": 200, "title": "Second", "depth": 2, ...}
```

**Reading with Python:**
```python
import json

with open('data/crawled_pages.json', 'r') as f:
    for line in f:
        page = json.loads(line)
        print(page['url'], page['title'])
```

**Reading with pandas:**
```python
import pandas as pd

df = pd.read_json('data/crawled_pages.json', lines=True)
print(df[['url', 'status', 'title']])
```

### SQLite storage

**Structure:**
- `pages`: url, status, title, depth, timestamp, text_preview, error, meta
- `links`: source_url, target_url

**Queries:**
```sql
-- All successful pages
SELECT url, title FROM pages WHERE error IS NULL;

-- Error pages
SELECT url, status, error FROM pages WHERE error IS NOT NULL;

-- Link network
SELECT source_url, target_url FROM links;
```

**Python example:**
```python
import sqlite3

conn = sqlite3.connect('data/crawler.db')
cursor = conn.cursor()

cursor.execute('SELECT url, title FROM pages WHERE status = 200')
for row in cursor.fetchall():
    print(row)
```

---

## 🏗️ Architecture

```
src/
├── config.py          # Configuration loading and validation
├── tor_client.py      # Tor SOCKS5 connection + HTTP requests
├── parser.py          # HTML parsing and link extraction
├── crawler.py         # BFS algorithm and core logic
├── storage/
│   ├── base.py        # Abstract storage class
│   ├── json_storage.py   # NDJSON storage
│   └── sqlite_storage.py # SQLite storage
└── utils.py           # Helper functions (URL validation, logger)
```

**Data flow:**
1. `main.py` loads configuration (`config.py`)
2. `TorCrawler` initializes `TorClient` and `Storage`
3. BFS loop: Get URL from queue → Fetch with `TorClient` → Parse with `HTMLParser` → Save to `Storage` → Add links to queue
4. End when max_pages or queue empty

---

## 🔒 Security & Ethics

### ⚠️ IMPORTANT

**ALLOWED use:**
- ✅ Research and educational purposes
- ✅ Legal .onion sites (public directories, research targets)
- ✅ Own infrastructure/test sites

**FORBIDDEN use:**
- ❌ Illegal .onion site crawling
- ❌ Denial-of-Service (DoS) attacks
- ❌ Server overloading
- ❌ Intrusion attempts
- ❌ Personal data harvesting
- ❌ User deanonymization

### Ethical principles

1. **Follow laws:** Ensure your actions are legal in your country
2. **Respect robots.txt:** Crawler respects robots.txt files by default
3. **Rate limiting:** DO NOT remove or decrease `request_delay` (minimum 2-3 seconds)
4. **Maximum pages:** Don't set `max_pages` too high (start <100)
5. **Personal data:** Don't store or share personal information
6. **Responsibility:** User is responsible for crawler usage

### Technical security measures

- **Tor connection:** All traffic goes through Tor network
- **No JavaScript:** Crawler doesn't execute JavaScript (static HTML)
- **SSL validation off:** .onion sites don't have SSL certificates
- **Timeout:** All requests timeout (default 30s)
- **Error handling:** Comprehensive try-except logic

---

## 🐛 Troubleshooting

### Error: "Could not establish Tor connection"

**Cause:** Tor is not running or port is wrong.

**Solution:**
```bash
# Check that Tor is running
sudo systemctl status tor  # Linux
brew services list | grep tor  # macOS

# Test Tor connection
curl --socks5-hostname 127.0.0.1:9050 https://check.torproject.org/api/ip

# Check port in config.yaml (default 9050)
```

### Error: "Configuration file not found"

**Cause:** `config.yaml` is missing.

**Solution:**
```bash
cp config.example.yaml config.yaml
# Edit config.yaml and add start_url
```

### Many timeout errors

**Cause:** .onion sites are slow or offline.

**Solution:**
- Increase `request_timeout` value (e.g. 60)
- Increase `max_retries` value (e.g. 5)
- Check that site is actually reachable with Tor Browser

### ImportError: No module named 'stem'

**Cause:** Dependencies not installed.

**Solution:**
```bash
pip install -r requirements.txt
```

---

## 📚 Future Development

**Possible improvements:**
- [ ] Robots.txt support (parsing and respecting)
- [ ] stem integration (automatic IP rotation)
- [ ] JavaScript rendering (Playwright/Selenium)
- [ ] Graphical user interface (web UI)
- [ ] Network analysis (NetworkX, PageRank)
- [ ] Screenshot saving
- [ ] Multi-threading/multiprocessing support

---

## 📄 License

This project is intended for **research and educational purposes**. User is fully responsible for crawler usage and ensuring actions are legal.

**Authors take no responsibility for:**
- Illegal use
- Harm to third parties
- Data misuse

---

## 🙏 Credits

- **Tor Project** - Anonymity and privacy
- **aiohttp** - Excellent asynchronous HTTP library
- **BeautifulSoup** - HTML parsing
- **Python community** - Fantastic ecosystem

---

## 📞 Support

**Problems?**
1. Read [Troubleshooting](#-troubleshooting) section
2. Check Tor connection
3. Check configuration
4. Use `--log-level DEBUG` for more information

---

**Happy researching! 🔍🧅**
