# Docker Guide for Tor Crawler

This guide explains how to use Docker with Tor Crawler for the easiest setup experience.

## 🎯 Why Docker?

- ✅ **Zero setup:** No Python or Tor installation needed
- ✅ **Consistent environment:** Works the same on all platforms
- ✅ **Isolated:** Doesn't affect your system
- ✅ **Auto-sync data:** Results appear instantly in `./data/` folder
- ✅ **One command:** Everything starts with `docker-compose up`

---

## 📋 Quick Start

### 1. Install Docker

**Linux:**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Log out and back in
```

**macOS:**
- Download [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)

**Windows:**
- Download [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)

### 2. Start Crawling

```bash
# Clone repo
git clone <repo-url>
cd Tor-crawler

# Configure
cp config.example.yaml config.yaml
nano config.yaml  # Set your start_url

# Start!
docker-compose up
```

**Data automatically appears in `./data/` folder!**

---

## 🔧 Docker Architecture

```
┌─────────────────────────────────────┐
│   Your Computer (Host)              │
│                                     │
│   ./data/  ← Auto-synced! ──────┐  │
│   config.yaml                   │  │
│                                 │  │
│   ┌─────────────────────────┐   │  │
│   │  Docker Network         │   │  │
│   │                         │   │  │
│   │  ┌──────────┐           │   │  │
│   │  │   Tor    │           │   │  │
│   │  │  Proxy   │           │   │  │
│   │  └────┬─────┘           │   │  │
│   │       │                 │   │  │
│   │  ┌────▼─────┐           │   │  │
│   │  │ Crawler  │───────────┼───┘  │
│   │  │          │ Volume    │      │
│   │  └──────────┘  Mount    │      │
│   └─────────────────────────┘      │
└─────────────────────────────────────┘
```

---

## 📁 Data Extraction

### Automatic (Recommended)

Data is **automatically saved** to `./data/` on your computer in real-time:

```bash
# View live data while crawler runs
cat data/crawled_pages.json

# Pretty print
cat data/crawled_pages.json | jq .

# SQLite query
sqlite3 data/crawler.db "SELECT * FROM pages;"
```

### Manual Copy (Alternative)

If you need to copy data manually:

```bash
# Copy from container
docker cp tor-crawler:/app/data ./data-backup

# Or access container directly
docker exec -it tor-crawler bash
cd /app/data
ls -lh
```

---

## ⚙️ Configuration Options

### Option 1: Config File (Recommended)

Edit `config.yaml` and mount it:

```yaml
# config.yaml
crawler:
  start_url: "http://example.onion"
  max_pages: 100
  max_depth: 3
```

```bash
docker-compose up
```

### Option 2: Environment Variables

Edit `docker-compose.yaml`:

```yaml
services:
  crawler:
    environment:
      - START_URL=http://example.onion
      - MAX_PAGES=100
      - MAX_DEPTH=3
      - LOG_LEVEL=DEBUG
```

### Option 3: Command Line

```bash
docker-compose run --rm crawler \
  --start-url "http://example.onion" \
  --max-pages 50 \
  --max-depth 2 \
  --storage sqlite
```

---

## 🛠️ Common Commands

### Starting

```bash
# Start (foreground, see logs)
docker-compose up

# Start (background)
docker-compose up -d

# Start only specific service
docker-compose up tor
docker-compose up crawler
```

### Stopping

```bash
# Stop (Ctrl+C in foreground)
# Or:
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove everything (including volumes)
docker-compose down -v
```

### Logs

```bash
# View all logs
docker-compose logs

# Follow logs (live)
docker-compose logs -f

# Specific service logs
docker-compose logs crawler
docker-compose logs tor

# Last 100 lines
docker-compose logs --tail=100 crawler
```

### Debugging

```bash
# Check container status
docker-compose ps

# Access crawler shell
docker exec -it tor-crawler bash

# Access tor container
docker exec -it tor-proxy sh

# Check network
docker network ls
docker network inspect tor-crawler_tor-network
```

### Maintenance

```bash
# Rebuild after code changes
docker-compose build

# Rebuild without cache
docker-compose build --no-cache

# Pull latest images
docker-compose pull

# Remove old images
docker image prune
```

---

## 🔍 Advanced Usage

### Custom Docker Compose Override

Create `docker-compose.override.yaml`:

```yaml
version: '3.8'

services:
  crawler:
    environment:
      - START_URL=http://mysite.onion
      - MAX_PAGES=500
    volumes:
      # Additional volume for custom scripts
      - ./scripts:/app/scripts
```

Docker Compose automatically merges this with `docker-compose.yaml`.

### Running Multiple Crawlers

```bash
# Create separate directories
mkdir crawler1 crawler2

# Copy files
cp -r * crawler1/
cp -r * crawler2/

# Run separately
cd crawler1 && docker-compose up -d
cd ../crawler2 && docker-compose -p crawler2 up -d
```

### Using Different Tor Circuits

```bash
# Restart Tor to get new circuit
docker-compose restart tor

# Or configure in docker-compose.yaml:
services:
  tor:
    environment:
      - TOR_MaxCircuitDirtiness=60
```

---

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Check what's using port 9050
sudo lsof -i :9050

# Or change port in docker-compose.yaml:
services:
  tor:
    ports:
      - "9051:9050"  # Use 9051 on host
```

### Tor Not Ready

```bash
# Check Tor logs
docker-compose logs tor

# Increase healthcheck timeout in docker-compose.yaml:
services:
  tor:
    healthcheck:
      start_period: 60s
```

### Permission Issues

```bash
# Fix data folder permissions
sudo chown -R $USER:$USER ./data

# Or run with specific user
services:
  crawler:
    user: "${UID}:${GID}"
```

### Container Keeps Restarting

```bash
# Check logs for errors
docker-compose logs crawler

# Run without restart policy for debugging
docker-compose run --rm crawler --log-level DEBUG
```

---

## 📊 Monitoring

### Resource Usage

```bash
# Real-time stats
docker stats tor-crawler tor-proxy

# Disk usage
docker system df
```

### Health Checks

```bash
# Check Tor health
docker inspect tor-proxy | grep -A 10 Health

# Test Tor connection
docker exec tor-proxy curl --socks5-hostname localhost:9050 \
  https://check.torproject.org/api/ip
```

---

## 🔒 Security Notes

- Containers run in isolated network
- Tor traffic is contained within Docker network
- Data volume only mounts `./data/` (not full filesystem)
- Config is mounted read-only (`:ro` flag)
- No privileged mode required
- Minimal base images used (python:slim)

---

## 📚 Learn More

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Tor Project](https://www.torproject.org/)

---

**Happy containerized crawling! 🐳🔍**
