# Cybersecurity Community Discord Bot

An automated Discord bot tailored for cybersecurity communities and clubs. It delivers weekly online CTF announcements from CTFtime, manages a community catalog of cybersecurity certifications, monitors Raspberry Pi host health, and provides interactive slash commands.

---

## Features

- 🚩 **Weekly CTF Announcements**: Automatically discovers and posts upcoming online CTFs from CTFtime once a week, formatted in UTC+8 with competition weights, formats, and event links.
- 📜 **Certifications Directory (`/certifications`)**: Community catalog of cybersecurity certifications with full CRUD support, categorizing certifications as Free/Paid and Hands-on/Theoretical. Sensitive actions (delete) are secured with an admin password hash.
- 🩺 **Host & Hardware Health Monitoring (`/health`)**: Reports real-time Raspberry Pi telemetry including SoC temperature, power & undervoltage throttling (`vcgencmd`), RAM usage, disk usage, and uptime.
- 💬 **Slash Commands Suite**: Native Discord application slash commands (`/ctfs`, `/certifications`, `/health`, `/help`).
- 🛡️ **Hardened & Lightweight**: Runs as a non-root container with dropped Linux capabilities, read-only host mounts, and transactional SQLite storage.

---

## Slash Commands

| Command | Description | Parameters & Options |
| :--- | :--- | :--- |
| `/ctfs` | Lists upcoming online CTFs scheduled for the next 7 days. | *None* |
| `/certifications` | View or manage certifications in the community database. | • `action`: Operation to perform (`create`, `update`, `delete`, or leave empty to list)<br>• `certification_id`: ID of the certification (for `update` or `delete`)<br>• `name`: Certification name<br>• `provider`: Issuing body or platform (e.g. OffSec, CompTIA)<br>• `url`: Link to certification or exam page<br>• `free`: Boolean (`True` for free, `False` for paid)<br>• `hands_on`: Boolean (`True` for practical/lab-based, `False` for theoretical)<br>• `password`: Admin password (required for `delete`) |
| `/health` | Displays host/Raspberry Pi hardware and system health. | *None* |
| `/help` | Shows available bot commands and their usage. | *None* |

---

## Configuration

Configuration is loaded from environment variables or a local `.env` file:

| Variable | Required | Default | Description |
| :--- | :---: | :--- | :--- |
| `DISCORD_TOKEN` | **Yes** | — | Discord Bot token from the [Discord Developer Portal](https://discord.com/developers/applications). |
| `ANNOUNCEMENT_CHANNEL_ID` | **Yes** | — | Discord channel ID (integer) where weekly CTF announcements will be posted. |
| `CRUD_ADMIN_PASSWORD_HASH` | **Yes** | — | PBKDF2-SHA256 password hash required to perform protected operations (e.g. deleting certifications). |
| `ANNOUNCEMENT_WEEKDAY` | No | `0` | Day of the week for automated announcements (`0` = Monday, `6` = Sunday). |
| `ANNOUNCEMENT_HOUR_UTC` | No | `9` | Hour of the day (0–23 in UTC) for announcements (e.g. `9` = 09:00 UTC / 17:00 UTC+8). |
| `DATABASE_PATH` | No | `data/bot.sqlite3` | File path for the SQLite database. |
| `CTFTIME_API_URL` | No | `https://ctftime.org/api/v1/events/` | CTFtime events API endpoint. |

### Generating the Admin Password Hash

Run the following command to generate the `CRUD_ADMIN_PASSWORD_HASH` for your admin password:

```bash
python -c "from bot.security import hash_password; print(hash_password('your-strong-password'))"
```

---

## Getting Started

### Local Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/juhenes/cyber-discord-bot.git
   cd cyber-discord-bot
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your DISCORD_TOKEN, ANNOUNCEMENT_CHANNEL_ID, and CRUD_ADMIN_PASSWORD_HASH
   ```

3. **Install dependencies & run tests**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   pytest
   ```

4. **Start the bot**:
   ```bash
   python -m bot.main
   ```

---

## Docker Deployment

The bot includes a hardened `Dockerfile` and `docker-compose.yml` pre-configured for deployment on Linux hosts and Raspberry Pis.

1. **Configure `.env`**:
   ```bash
   cp .env.example .env
   # Populate .env with production credentials
   ```

2. **Launch with Docker Compose**:
   ```bash
   docker compose up --build -d
   ```

- **Logs**: View real-time logs with `docker compose logs -f bot`.
- **Persistence**: SQLite database data is stored in the Docker named volume `bot-data`.
- **Automatic restarts**: The container uses `restart: unless-stopped` to automatically recover from reboots or transient crashes.

### Raspberry Pi Hardware Health Permissions

For `/health` to read GPU power and throttling alerts via `/dev/vcio` on Raspberry Pi hosts, ensure the container's video group has access:

```bash
sudo chmod 660 /dev/vcio
printf 'SUBSYSTEM=="misc", KERNEL=="vcio", GROUP="video", MODE="0660"\n' | sudo tee /etc/udev/rules.d/rpi-vcio.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

---

## Architecture & Codebase Structure

The bot is organized into focused subpackages separating Discord interactions, business logic, persistence, and utilities:

```text
bot/
├── commands/                 # Discord slash command interactions
│   ├── ctfs.py               # /ctfs: on-demand CTF competition listing
│   ├── certifications.py     # /certifications: CRUD catalog with admin protection
│   ├── health.py             # /health: hardware and host telemetry display
│   └── help.py               # /help: command index and usage instructions
├── services/                 # Business logic, APIs & background tasks
│   ├── ctfs.py               # CTF data model and CTFtime API client
│   ├── announcements.py      # Portable message formatting (UTC+8)
│   ├── scheduler.py          # Resilient WeeklyCTFAnnouncer task loop
│   └── system.py             # Pure host telemetry (temperature, power, RAM, disk, uptime)
├── storage/                  # SQLite persistence & models
│   ├── database.py           # SQLite connection manager, SQLiteCrudStore, AnnouncementStore, CertificationStore
│   └── models.py             # Certification data models
├── utils/                    # Shared utilities
│   └── security.py           # PBKDF2 password hashing & verification
├── config.py                 # Configuration parsing and validation (Settings)
└── main.py                   # Client setup, logging, and command registration
```