# 🏛️ UniFi Access Telegram Bot for Church

Control your church's UniFi Access door locks directly from Telegram! Schedule door access, lock/unlock doors remotely, and manage access control through an easy-to-use chat interface.

## ✨ Features

- 🚪 **Instant Door Control**: Lock/unlock doors immediately with button clicks
- 📅 **Schedule Management**: Program door schedules via chat
- 📊 **Door Status**: Check real-time status of all doors
- 🔐 **Secure Access**: Whitelist specific Telegram users
- 💬 **User-Friendly**: Simple button-based interface, no complex commands needed
- 🐳 **Docker Ready**: Easy deployment with Docker
- 🔄 **Async Operations**: Fast, non-blocking API calls

## 📋 Prerequisites

1. **UniFi Access Controller** (on-premise or hosted)
2. **Telegram Account**
3. **Python 3.9+** (if running locally) OR **Docker** (recommended)
4. Stable internet connection for the bot server

## 🚀 Quick Start

### Step 1: Create a Telegram Bot

1. Open Telegram and message [@BotFather](https://t.me/botfather)
2. Send `/newbot` command
3. Follow the prompts to name your bot (e.g., "Church Access Bot")
4. Save the **bot token** you receive (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Step 2: Get Your Telegram User ID

1. Message [@userinfobot](https://t.me/userinfobot) on Telegram
2. It will reply with your user ID (a number like `123456789`)
3. Get IDs for all authorized users (church staff, pastors, etc.)

### Step 3: Configure the Bot

1. Copy the example configuration file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your details:
   ```bash
   nano .env
   ```

3. Fill in the required values:
   ```env
   TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
   UNIFI_ACCESS_HOST=https://your-unifi-controller.local:12443
   UNIFI_ACCESS_USERNAME=your_unifi_username
   UNIFI_ACCESS_PASSWORD=your_unifi_password
   ALLOWED_TELEGRAM_USERS=123456789,987654321
   VERIFY_SSL=true
   ```

### Step 4: Run the Bot

#### Option A: Using Docker (Recommended)

```bash
# Build the Docker image
docker build -t church-access-bot .

# Run the container
docker run -d --name church-access-bot --env-file .env church-access-bot

# View logs
docker logs -f church-access-bot
```

#### Option B: Using Python Directly

```bash
# Install dependencies
pip install -r requirements.txt

# Run the bot
python bot.py
```

#### Option C: Using Docker Compose

```bash
# Start the bot
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the bot
docker-compose down
```

## 💬 Using the Bot

### Starting the Bot

1. Open Telegram and search for your bot by username
2. Send `/start` to begin
3. You'll see a menu with options:
   - 🚪 Control Doors Now
   - 📅 Schedule Door Access
   - 📋 View Schedules
   - ℹ️ Door Status

### Quick Actions

**Unlock a door immediately:**
1. Tap "🚪 Control Doors Now"
2. Select the door
3. Tap "🔓 Unlock"
4. Door will unlock for 10 seconds

**Lock a door:**
1. Tap "🚪 Control Doors Now"
2. Select the door
3. Tap "🔒 Lock"

**Check door status:**
1. Tap "ℹ️ Door Status"
2. See real-time status of all doors

**Create a schedule:**
1. Tap "📅 Schedule Door Access"
2. Select the door
3. Choose lock/unlock
4. Enter the time (e.g., "9:00 AM")
5. Confirm

## 🏗️ Deployment Options

### For Small Churches (Free Options)

1. **Raspberry Pi** (one-time cost ~$50)
   - Install Raspberry Pi OS
   - Clone this repository
   - Run with Docker or Python
   - Set up to auto-start on boot

2. **Free Cloud Hosting**
   - **Railway.app**: Free tier, easy deployment
   - **Render.com**: 750 hours/month free
   - **Fly.io**: Free allowance included
   - **PythonAnywhere**: Free tier available

### For Larger Churches

1. **Cloud Servers**: AWS, Google Cloud, Azure
2. **VPS Providers**: DigitalOcean, Linode, Vultr
3. **On-Premise Server**: Run on existing church server

## 🔐 Security Best Practices

1. **Limit User Access**: Only add trusted staff to `ALLOWED_TELEGRAM_USERS`
2. **Secure Credentials**: Never commit `.env` file to Git
3. **Use Strong Passwords**: Use complex UniFi Access password
4. **Network Security**: Run bot on same network as UniFi controller if possible
5. **Regular Updates**: Keep the bot and dependencies updated
6. **Monitor Logs**: Check logs regularly for suspicious activity

## 📁 Project Structure

```
unifi-telegram-bot/
├── bot.py                 # Main bot code
├── requirements.txt       # Python dependencies
├── .env.example          # Configuration template
├── .env                  # Your actual config (don't commit!)
├── Dockerfile            # Docker image definition
├── docker-compose.yml    # Docker Compose configuration
├── .gitignore           # Files to ignore in Git
└── README.md            # This file
```

## 🛠️ Troubleshooting

### Bot doesn't respond
- Check if bot is running: `docker ps` or check process
- View logs: `docker logs church-access-bot`
- Verify Telegram token is correct

### Can't connect to UniFi Access
- Verify `UNIFI_ACCESS_HOST` URL is correct
- Check username/password
- If using self-signed SSL, set `VERIFY_SSL=false`
- Ensure bot server can reach UniFi controller

### "Not authorized" message
- Verify your Telegram user ID is in `ALLOWED_TELEGRAM_USERS`
- Check logs to see what user ID is trying to connect
- IDs should be comma-separated with no spaces

### Door commands fail
- Check UniFi Access user has proper permissions
- Verify doors are online in UniFi Access dashboard
- Check network connectivity

## 📖 Advanced Configuration

### Auto-start on Boot (Raspberry Pi)

1. Create systemd service:
   ```bash
   sudo nano /etc/systemd/system/church-access-bot.service
   ```

2. Add this content:
   ```ini
   [Unit]
   Description=Church UniFi Access Telegram Bot
   After=network.target

   [Service]
   Type=simple
   User=pi
   WorkingDirectory=/home/pi/unifi-telegram-bot
   ExecStart=/usr/bin/python3 /home/pi/unifi-telegram-bot/bot.py
   Restart=always
   EnvironmentFile=/home/pi/unifi-telegram-bot/.env

   [Install]
   WantedBy=multi-user.target
   ```

3. Enable and start:
   ```bash
   sudo systemctl enable church-access-bot
   sudo systemctl start church-access-bot
   ```

### Adding More Features

The bot is designed to be extended. You can add:
- Recurring schedules (daily/weekly)
- Multiple door unlocks at once
- Access logs and reports
- Integration with church calendar
- Notifications for door events

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review logs for error messages
3. Open an issue on GitHub
4. Contact your church IT administrator

## 📝 License

This project is provided as-is for church and non-profit use.

## 🙏 Credits

Built with:
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [aiohttp](https://github.com/aio-libs/aiohttp)
- UniFi Access API

---

**Made with ❤️ for churches using UniFi Access**
