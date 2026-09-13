# Weekly CTF Discord Bot

This bot posts the upcoming **online** CTFtime events once a week and includes each event's weight. It exposes `/ctfs` for an on-demand list and `/health` for Raspberry Pi temperature, power, memory, storage, and uptime status. The code is split into provider, formatting, storage, scheduling, health, and Discord entrypoint modules so new slash commands can be added without changing the announcement logic.

## Setup

1. Create a Discord application and bot, then enable the bot's `Send Messages` permission in the target channel.
2. Copy `.env.example` to `.env`, set `DISCORD_TOKEN` and `ANNOUNCEMENT_CHANNEL_ID`, and generate `CRUD_ADMIN_PASSWORD_HASH` with the command shown in `.env.example`.
3. Install dependencies and run the tests:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   pytest
   ```

4. Start the bot:

   ```bash
   python -m bot.main
   ```

## Docker

Copy `.env.example` to `.env`, set the required values, and start the bot in the background:

```bash
docker compose up --build -d
```

The service uses `restart: unless-stopped`, so Docker starts it again after a crash or host reboot. Its SQLite database is stored in the named `bot-data` volume. View logs with `docker compose logs -f bot` and stop it with `docker compose down`.

The `/health` command reads Raspberry Pi temperature, memory, uptime, and power status through narrowly scoped read-only host mounts. The container remains non-root, drops all Linux capabilities, and has no published ports or host networking.

On the Raspberry Pi host, grant the video group access to the power-status device once, then make it persistent:

```bash
sudo chmod 660 /dev/vcio
printf 'SUBSYSTEM=="misc", KERNEL=="vcio", GROUP="video", MODE="0660"\n' | sudo tee /etc/udev/rules.d/rpi-vcio.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

The default announcement is Monday at 09:00 UTC. Change `ANNOUNCEMENT_WEEKDAY` (`0` is Monday) and `ANNOUNCEMENT_HOUR_UTC` if needed. SQLite prevents a restart from posting the same week's announcement twice.

The event source is CTFtime's public API. It filters events using CTFtime's `onsite: false` field; CTFtime is the event directory, while individual competitions may be hosted on CTFd or another platform. If “CTFd” must be a strict filter, the provider is the intended place to add a reliable platform field or allowlist once the desired event source exposes one.

Certifications are managed with `/certifications`. Leave `action` empty to show them. Use `action: create`, `update`, or `delete` for management operations. Create and update accept `free` and `hands_on` flags. Discord slash commands cannot dynamically autofill or show sibling options based on the selected action, so the command keeps these fields optional and validates the fields required by each operation. The output is compact, with each certification name linking to its URL and showing whether it is free/paid and theory/hands-on. The storage and command use reusable CRUD building blocks so another resource can be added later without putting its persistence or commands in `main.py`.