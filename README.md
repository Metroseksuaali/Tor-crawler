# Tor Crawler

🔍 Turvallinen ja eettinen web crawler .onion-sivustojen tutkimiseen Tor-verkossa.

**Tarkoitus:** Tutkimus- ja oppimistarkoitukset
**Tekniikka:** Python 3.9+ | aiohttp | BeautifulSoup | Tor SOCKS5

---

## 📋 Sisällysluettelo

- [Ominaisuudet](#-ominaisuudet)
- [Teknologiavalinnat](#-teknologiavalinnat)
- [Esivaatimukset](#-esivaatimukset)
- [Asennus](#-asennus)
- [Käyttö](#-käyttö)
- [Konfiguraatio](#-konfiguraatio)
- [Datan käsittely](#-datan-käsittely)
- [Arkkitehtuuri](#-arkkitehtuuri)
- [Turvallisuus ja etiikka](#-turvallisuus-ja-etiikka)
- [Vianmääritys](#-vianmääritys)

---

## ✨ Ominaisuudet

- ✅ **Tor-integraatio:** Kaikki liikenne kulkee Tor-verkon kautta (SOCKS5-proxy)
- ✅ **Asynkroninen:** Tehokas rinnakkaiskäsittely asyncio:lla
- ✅ **Rate limiting:** Konfiguroitava viive pyyntöjen välillä (eettinen crawlaus)
- ✅ **BFS-algoritmi:** Leveyssuuntainen läpikäynti syvyydenrajoituksella
- ✅ **Kaksi tallennusvaihtoehtoa:** JSON (NDJSON) ja SQLite
- ✅ **HTML-parsinta:** BeautifulSoup + linkkien suodatus
- ✅ **Virheenkäsittely:** Timeout, connection errors, retry-logiikka
- ✅ **Domain-rajaus:** Vain .onion-sivustot, konfiguroitavat domain-rajoitukset
- ✅ **CLI-käyttöliittymä:** Helppo käyttö komentoriviltä
- ✅ **Jatkettava crawlaus:** Voit pysäyttää ja jatkaa myöhemmin

---

## 🎯 Teknologiavalinnat

### Miksi Python + aiohttp?

**Vertaillut vaihtoehdot:**
1. **Python + aiohttp** ⭐ (valittu)
2. Node.js + axios
3. Rust + reqwest

**Valintaperusteet:**
- ✅ Kypsä Tor-ekosysteemi (stem-kirjasto)
- ✅ Erinomainen scraping-tuki (BeautifulSoup)
- ✅ Asynkroninen suoritus (asyncio)
- ✅ Helppo oppia ja ylläpitää
- ✅ Data science -integraatio (pandas, numpy)

---

## 🔧 Esivaatimukset

### 1. Python 3.9+

Tarkista versio:
```bash
python3 --version
```

### 2. Tor

Crawleri tarvitsee käynnissä olevan Tor-instanssin.

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
- Lataa [Tor Expert Bundle](https://www.torproject.org/download/tor/)
- TAI käynnistä Tor Browser (sisältää SOCKS-proxyn)

**Docker:**
```bash
docker run -d -p 9050:9050 --name tor dperson/torproxy
```

**Testaa että Tor toimii:**
```bash
curl --socks5-hostname 127.0.0.1:9050 https://check.torproject.org/api/ip
```

Pitäisi palauttaa: `{"IsTor": true, ...}`

---

## 📦 Asennus

### 1. Kloonaa repository
```bash
git clone <repository-url>
cd Tor-crawler
```

### 2. Luo virtuaaliympäristö (suositeltu)
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# TAI
venv\Scripts\activate  # Windows
```

### 3. Asenna riippuvuudet
```bash
pip install -r requirements.txt
```

### 4. Konfiguroi crawler

Kopioi esimerkkikonfiguraatio:
```bash
cp config.example.yaml config.yaml
```

Muokkaa `config.yaml`:
```yaml
crawler:
  start_url: "http://your-target.onion"  # ⚠️ Lisää tähän tutkittava .onion-osoite
  max_depth: 2
  max_pages: 50
  request_delay: 3.0  # TÄRKEÄ: Älä poista!
```

---

## 🚀 Käyttö

### Peruskomento

```bash
python main.py --config config.yaml
```

### Komentoriviparametrit

```bash
# Käytä kaikki asetukset komentoriviltä
python main.py --start-url "http://example.onion" --max-pages 50 --max-depth 2

# SQLite-tallennus
python main.py --config config.yaml --storage sqlite

# Muuta rate limiting
python main.py --config config.yaml --delay 5.0

# Debug-tila
python main.py --config config.yaml --log-level DEBUG
```

### Esimerkkiajo

```bash
# Aloita pienellä testillä
python main.py \
  --start-url "http://example.onion" \
  --max-pages 10 \
  --max-depth 1 \
  --delay 3.0 \
  --storage json
```

### Keskeytys ja jatkaminen

Voit keskeyttää crawlauksen (`Ctrl+C`) ja jatkaa myöhemmin:
```bash
# Crawler lataa automaattisesti aiemmin käydyt URL:t
python main.py --config config.yaml
```

---

## ⚙️ Konfiguraatio

### YAML-tiedosto (config.yaml)

```yaml
# Tor-asetukset
tor:
  proxy_host: "127.0.0.1"
  proxy_port: 9050
  control_port: 9051
  use_stem: false  # true = mahdollistaa IP-vaihdon

# Crawler-asetukset
crawler:
  start_url: "http://example.onion"
  max_depth: 3              # Kuinka monta linkkitasoa
  max_pages: 100            # Maksimi sivuja yhteensä
  max_pages_per_domain: 50  # Maksimi per domain
  request_delay: 2.0        # Sekuntia pyyntöjen välillä
  request_timeout: 30       # Timeout sekunteina
  follow_external_onion: true  # Seuraa muita .onion-domaineja
  allowed_domains: []       # Tyhjä = kaikki, tai lista: ["a.onion", "b.onion"]

# Tallennus
storage:
  storage_type: "json"      # "json" tai "sqlite"
  output_dir: "./data"
  json_filename: "crawled_pages.json"
  sqlite_filename: "crawler.db"

# Lokitus
log_level: "INFO"
```

### Ympäristömuuttujat

Luo `.env`-tiedosto (kopioi `.env.example`):
```env
TOR_PROXY_HOST=127.0.0.1
TOR_PROXY_PORT=9050
START_URL=http://example.onion
MAX_DEPTH=3
MAX_PAGES=100
LOG_LEVEL=INFO
```

**Prioriteetti:** Komentorivi > Ympäristömuuttujat > YAML

---

## 📊 Datan käsittely

### JSON-tallennus (NDJSON)

Jokainen rivi = yksi JSON-objekti:

```json
{"url": "http://example.onion/page1", "status": 200, "title": "Esimerkki", "depth": 1, "timestamp": "2025-01-01T12:00:00", "links": ["http://example.onion/page2"], "text_preview": "...", "meta": {}, "error": null}
{"url": "http://example.onion/page2", "status": 200, "title": "Toinen", "depth": 2, ...}
```

**Lukeminen Pythonilla:**
```python
import json

with open('data/crawled_pages.json', 'r') as f:
    for line in f:
        page = json.loads(line)
        print(page['url'], page['title'])
```

**Lukeminen pandas:lla:**
```python
import pandas as pd

df = pd.read_json('data/crawled_pages.json', lines=True)
print(df[['url', 'status', 'title']])
```

### SQLite-tallennus

**Rakenne:**
- `pages`: url, status, title, depth, timestamp, text_preview, error, meta
- `links`: source_url, target_url

**Kyselyt:**
```sql
-- Kaikki onnistuneet sivut
SELECT url, title FROM pages WHERE error IS NULL;

-- Virhesivut
SELECT url, status, error FROM pages WHERE error IS NOT NULL;

-- Linkkiverkosto
SELECT source_url, target_url FROM links;
```

**Python-esimerkki:**
```python
import sqlite3

conn = sqlite3.connect('data/crawler.db')
cursor = conn.cursor()

cursor.execute('SELECT url, title FROM pages WHERE status = 200')
for row in cursor.fetchall():
    print(row)
```

---

## 🏗️ Arkkitehtuuri

```
src/
├── config.py          # Konfiguraation lataus ja validointi
├── tor_client.py      # Tor SOCKS5-yhteys + HTTP-pyynnöt
├── parser.py          # HTML-parsinta ja linkkien eristäminen
├── crawler.py         # BFS-algoritmi ja ydinlogiikka
├── storage/
│   ├── base.py        # Abstrakti tallennusluokka
│   ├── json_storage.py   # NDJSON-tallennus
│   └── sqlite_storage.py # SQLite-tallennus
└── utils.py           # Apufunktiot (URL-validointi, logger)
```

**Tietovirta:**
1. `main.py` lataa konfiguraation (`config.py`)
2. `TorCrawler` alustaa `TorClient`:n ja `Storage`:n
3. BFS-silmukka: Ota URL jonosta → Hae `TorClient`:llä → Parsoi `HTMLParser`:llä → Tallenna `Storage`:en → Lisää linkit jonoon
4. Lopeta kun max_pages tai jono tyhjä

---

## 🔒 Turvallisuus ja etiikka

### ⚠️ TÄRKEÄÄ

**SALLITTU käyttö:**
- ✅ Tutkimus- ja oppimistarkoitukset
- ✅ Lailliset .onion-sivustot (julkiset hakemistot, tutkimuskohteet)
- ✅ Oma infrastruktuuri/testisivustot

**KIELLETTY käyttö:**
- ❌ Laittomien .onion-sivustojen crawlaus
- ❌ Denial-of-Service (DoS) -hyökkäykset
- ❌ Palvelinten ylikuormittaminen
- ❌ Tunkeutumisyritykset
- ❌ Henkilötietojen kaappaaminen
- ❌ Käyttäjien deanonymisointi

### Eettiset periaatteet

1. **Noudata lakeja:** Varmista että toimintasi on laillista maassasi
2. **Kunnioita robots.txt:** Crawler kunnioittaa oletuksena robots.txt-tiedostoja
3. **Rate limiting:** ÄLÄ poista tai pienennä `request_delay`-arvoa (vähintään 2-3 sekuntia)
4. **Maksimisivumäärä:** Älä aseta `max_pages` liian korkeaksi (aloita <100)
5. **Henkilötiedot:** Älä tallenna tai jaa henkilökohtaisia tietoja
6. **Vastuu:** Käyttäjä on vastuussa crawlerin käytöstä

### Tekniset turvallisuustoimet

- **Tor-yhteys:** Kaikki liikenne kulkee Tor-verkon kautta
- **Ei JavaScript:** Crawler ei suorita JavaScriptiä (staattinen HTML)
- **SSL-validointi pois päältä:** .onion-sivustoilla ei SSL-sertifikaatteja
- **Timeout:** Kaikki pyynnöt aikakatkaisevat (default 30s)
- **Virheenkäsittely:** Kattava try-except-logiikka

---

## 🐛 Vianmääritys

### Virhe: "Tor-yhteyttä ei voitu muodostaa"

**Syy:** Tor ei ole käynnissä tai portti on väärä.

**Ratkaisu:**
```bash
# Tarkista että Tor on käynnissä
sudo systemctl status tor  # Linux
brew services list | grep tor  # macOS

# Testaa Tor-yhteyttä
curl --socks5-hostname 127.0.0.1:9050 https://check.torproject.org/api/ip

# Tarkista portti config.yaml:ssa (oletuksena 9050)
```

### Virhe: "Konfiguraatiotiedostoa ei löydy"

**Syy:** `config.yaml` puuttuu.

**Ratkaisu:**
```bash
cp config.example.yaml config.yaml
# Muokkaa config.yaml ja lisää start_url
```

### Timeout-virheitä paljon

**Syy:** .onion-sivustot ovat hitaita tai offline.

**Ratkaisu:**
- Kasvata `request_timeout` arvoa (esim. 60)
- Kasvata `max_retries` arvoa (esim. 5)
- Tarkista että sivusto on todella saavutettavissa Tor Browserilla

### ImportError: No module named 'stem'

**Syy:** Riippuvuuksia ei ole asennettu.

**Ratkaisu:**
```bash
pip install -r requirements.txt
```

---

## 📚 Jatkokehitys

**Mahdolliset parannukset:**
- [ ] Robots.txt-tuki (parsinta ja kunnioittaminen)
- [ ] stem-integraatio (automaattinen IP-vaihto)
- [ ] JavaScript-renderöinti (Playwright/Selenium)
- [ ] Graafinen käyttöliittymä (web UI)
- [ ] Verkkoanalyysi (NetworkX, PageRank)
- [ ] Screenshot-tallennus
- [ ] Multi-threading/multiprocessing-tuki

---

## 📄 Lisenssi

Tämä projekti on tarkoitettu **tutkimus- ja oppimistarkoituksiin**. Käyttäjä on täysin vastuussa crawlerin käytöstä ja siitä, että toiminta on laillista.

**Tekijät eivät ota vastuuta:**
- Laittomasta käytöstä
- Vahingosta kolmansille osapuolille
- Datan väärinkäytöstä

---

## 🙏 Kiitokset

- **Tor Project** - Anonymiteetti ja yksityisyys
- **aiohttp** - Erinomainen asynkroninen HTTP-kirjasto
- **BeautifulSoup** - HTML-parsinta
- **Python-yhteisö** - Fantastinen ekosysteemi

---

## 📞 Tuki

**Ongelmat?**
1. Lue [Vianmääritys](#-vianmääritys)-osio
2. Tarkista Tor-yhteys
3. Tarkista konfiguraatio
4. Käytä `--log-level DEBUG` saadaksesi lisätietoja

---

**Hyvää tutkimusmatkaa! 🔍🧅**
