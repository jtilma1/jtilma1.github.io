#!/usr/bin/env python3
"""
UniFi Access Telegram Bot
Control UniFi Access door locks/unlocks via Telegram chat
"""

import os
import logging
import json
from datetime import datetime, time
from typing import Dict, List, Optional
import asyncio
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
SELECTING_DOOR, SELECTING_ACTION, SELECTING_TIME, CONFIRMING = range(4)


class UniFiAccessAPI:
    """UniFi Access API client - Supports both local and cloud access"""

    def __init__(self, host: str, username: str, password: str, verify_ssl: bool = True, api_key: str = None, site_id: str = None):
        self.host = host.rstrip('/')
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.api_key = api_key  # For cloud access
        self.site_id = site_id  # For cloud access
        self.is_cloud = 'api.ui.com' in host or 'unifi.ui.com' in host
        self.session: Optional[aiohttp.ClientSession] = None
        self.token: Optional[str] = None
        self.headers = {
            'Content-Type': 'application/json',
        }

        # If using cloud API with API key, set it in headers
        if self.is_cloud and self.api_key:
            self.headers['x-api-key'] = self.api_key
            logger.info("Configured for UniFi Cloud API access")

    async def login(self):
        """Authenticate with UniFi Access"""
        if not self.session:
            connector = aiohttp.TCPConnector(ssl=self.verify_ssl)
            self.session = aiohttp.ClientSession(connector=connector)

        # If using cloud API with API key, no login needed
        if self.is_cloud and self.api_key:
            logger.info("Using UniFi Cloud API with API key - no login required")
            self.token = "cloud_api_key"  # Placeholder to indicate authenticated
            return True

        # Local controller login
        login_url = f"{self.host}/api/v1/developer/login"
        payload = {
            "username": self.username,
            "password": self.password
        }

        try:
            async with self.session.post(login_url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    self.token = data.get('token')
                    self.headers['Authorization'] = f'Bearer {self.token}'
                    logger.info("Successfully authenticated with UniFi Access (local)")
                    return True
                else:
                    logger.error(f"Login failed: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False

    def _build_url(self, endpoint: str) -> str:
        """Build the correct URL based on local or cloud mode"""
        if self.is_cloud and self.site_id:
            # Cloud API format
            return f"{self.host}/api/s/{self.site_id}/v1/developer/{endpoint}"
        else:
            # Local API format
            return f"{self.host}/api/v1/developer/{endpoint}"

    async def get_doors(self) -> List[Dict]:
        """Get list of all doors"""
        if not self.token:
            await self.login()

        doors_url = self._build_url("doors")

        try:
            async with self.session.get(doors_url, headers=self.headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('data', [])
                else:
                    logger.error(f"Failed to get doors: {response.status}")
                    text = await response.text()
                    logger.error(f"Response: {text}")
                    return []
        except Exception as e:
            logger.error(f"Error getting doors: {e}")
            return []

    async def unlock_door(self, door_id: str, duration: int = 10) -> bool:
        """Unlock a door for specified duration (seconds)"""
        if not self.token:
            await self.login()

        unlock_url = self._build_url(f"doors/{door_id}/unlock")
        payload = {"duration": duration}

        try:
            async with self.session.post(unlock_url, json=payload, headers=self.headers) as response:
                if response.status == 200:
                    logger.info(f"Door {door_id} unlocked successfully")
                    return True
                else:
                    logger.error(f"Failed to unlock door: {response.status}")
                    text = await response.text()
                    logger.error(f"Response: {text}")
                    return False
        except Exception as e:
            logger.error(f"Error unlocking door: {e}")
            return False

    async def lock_door(self, door_id: str) -> bool:
        """Lock a door immediately"""
        if not self.token:
            await self.login()

        lock_url = self._build_url(f"doors/{door_id}/lock")

        try:
            async with self.session.post(lock_url, headers=self.headers) as response:
                if response.status == 200:
                    logger.info(f"Door {door_id} locked successfully")
                    return True
                else:
                    logger.error(f"Failed to lock door: {response.status}")
                    text = await response.text()
                    logger.error(f"Response: {text}")
                    return False
        except Exception as e:
            logger.error(f"Error locking door: {e}")
            return False

    async def get_door_status(self, door_id: str) -> Optional[Dict]:
        """Get current status of a door"""
        if not self.token:
            await self.login()

        status_url = self._build_url(f"doors/{door_id}")

        try:
            async with self.session.get(status_url, headers=self.headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('data', {})
                else:
                    logger.error(f"Failed to get door status: {response.status}")
                    text = await response.text()
                    logger.error(f"Response: {text}")
                    return None
        except Exception as e:
            logger.error(f"Error getting door status: {e}")
            return None

    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()


class UniFiTelegramBot:
    """Telegram bot for UniFi Access control"""

    def __init__(self, telegram_token: str, unifi_api: UniFiAccessAPI, allowed_users: List[int]):
        self.telegram_token = telegram_token
        self.unifi_api = unifi_api
        self.allowed_users = allowed_users
        self.schedules: Dict = {}  # Store scheduled tasks

    def is_authorized(self, user_id: int) -> bool:
        """Check if user is authorized to use the bot"""
        return user_id in self.allowed_users

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = update.effective_user.id

        if not self.is_authorized(user_id):
            await update.message.reply_text(
                "⛔ You are not authorized to use this bot.\n"
                f"Your Telegram ID: {user_id}\n"
                "Contact the administrator to get access."
            )
            return

        keyboard = [
            [InlineKeyboardButton("🚪 Control Doors Now", callback_data="control_now")],
            [InlineKeyboardButton("📅 Schedule Door Access", callback_data="schedule")],
            [InlineKeyboardButton("📋 View Schedules", callback_data="view_schedules")],
            [InlineKeyboardButton("ℹ️ Door Status", callback_data="door_status")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "🏛️ Welcome to Church UniFi Access Control Bot!\n\n"
            "I can help you control door locks and create schedules.\n"
            "What would you like to do?",
            reply_markup=reply_markup
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
🏛️ **Church Access Control Bot Help**

**Quick Commands:**
/start - Main menu
/unlock - Unlock a door now
/lock - Lock a door now
/status - Check door status
/schedule - Create a schedule
/schedules - View all schedules
/help - Show this help

**How to use:**
1. Choose an action from the menu
2. Select which door(s) to control
3. Set the time (for scheduling)
4. Confirm your action

**Security:**
Only authorized users can control the doors.
All actions are logged.

**Need help?** Contact your church administrator.
        """
        await update.message.reply_text(help_text)

    async def control_now(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start immediate door control"""
        query = update.callback_query
        await query.answer()

        doors = await self.unifi_api.get_doors()

        if not doors:
            await query.edit_message_text("❌ No doors found or unable to connect to UniFi Access.")
            return ConversationHandler.END

        # Store doors in context for later use
        context.user_data['doors'] = doors
        context.user_data['mode'] = 'immediate'

        # Create keyboard with door options
        keyboard = []
        for door in doors:
            door_name = door.get('name', 'Unknown Door')
            door_id = door.get('id')
            keyboard.append([InlineKeyboardButton(f"🚪 {door_name}", callback_data=f"door_{door_id}")])

        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "Select a door to control:",
            reply_markup=reply_markup
        )

        return SELECTING_ACTION

    async def door_selected(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle door selection"""
        query = update.callback_query
        await query.answer()

        door_id = query.data.replace("door_", "")
        context.user_data['selected_door_id'] = door_id

        # Find door name
        doors = context.user_data.get('doors', [])
        door_name = next((d['name'] for d in doors if d['id'] == door_id), 'Unknown')
        context.user_data['selected_door_name'] = door_name

        keyboard = [
            [InlineKeyboardButton("🔓 Unlock", callback_data="action_unlock")],
            [InlineKeyboardButton("🔒 Lock", callback_data="action_lock")],
            [InlineKeyboardButton("🔙 Back", callback_data="control_now")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"🚪 **{door_name}**\n\nWhat would you like to do?",
            reply_markup=reply_markup
        )

        return SELECTING_TIME

    async def action_selected(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle action selection (lock/unlock)"""
        query = update.callback_query
        await query.answer()

        action = query.data.replace("action_", "")
        context.user_data['action'] = action

        mode = context.user_data.get('mode', 'immediate')
        door_name = context.user_data.get('selected_door_name', 'Unknown')

        if mode == 'immediate':
            # Execute immediately
            door_id = context.user_data['selected_door_id']

            if action == 'unlock':
                success = await self.unifi_api.unlock_door(door_id, duration=10)
                result_emoji = "✅" if success else "❌"
                result_text = "unlocked for 10 seconds" if success else "unlock failed"
            else:
                success = await self.unifi_api.lock_door(door_id)
                result_emoji = "✅" if success else "❌"
                result_text = "locked" if success else "lock failed"

            await query.edit_message_text(
                f"{result_emoji} **{door_name}** {result_text}!\n\n"
                f"Action performed at: {datetime.now().strftime('%I:%M %p')}"
            )

            return ConversationHandler.END

        else:
            # Schedule mode - ask for time
            await query.edit_message_text(
                f"🚪 **{door_name}** - {action.upper()}\n\n"
                "Please enter the time (e.g., '9:00 AM' or '14:30'):"
            )
            return CONFIRMING

    async def schedule_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start schedule creation"""
        query = update.callback_query
        await query.answer()

        context.user_data['mode'] = 'schedule'

        # Reuse control_now logic but with schedule mode
        await self.control_now(update, context)

        return SELECTING_ACTION

    async def view_schedules(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View all scheduled tasks"""
        query = update.callback_query
        await query.answer()

        if not self.schedules:
            await query.edit_message_text("📋 No schedules configured yet.")
            return

        schedule_text = "📋 **Active Schedules:**\n\n"
        for schedule_id, schedule in self.schedules.items():
            schedule_text += (
                f"• {schedule['door_name']}: {schedule['action']} at {schedule['time']}\n"
                f"  ID: {schedule_id}\n\n"
            )

        await query.edit_message_text(schedule_text)

    async def door_status_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show status of all doors"""
        query = update.callback_query
        await query.answer()

        doors = await self.unifi_api.get_doors()

        if not doors:
            await query.edit_message_text("❌ Unable to retrieve door status.")
            return

        status_text = "🚪 **Door Status:**\n\n"
        for door in doors:
            door_name = door.get('name', 'Unknown')
            # Get detailed status
            door_status = await self.unifi_api.get_door_status(door['id'])

            if door_status:
                lock_status = door_status.get('lock_status', 'unknown')
                status_emoji = "🔒" if lock_status == 'locked' else "🔓"
                status_text += f"{status_emoji} **{door_name}**: {lock_status}\n"
            else:
                status_text += f"❓ **{door_name}**: Status unknown\n"

        await query.edit_message_text(status_text)

    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel current operation"""
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("❌ Operation cancelled.")
        return ConversationHandler.END

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all button callbacks"""
        query = update.callback_query

        if query.data == "control_now":
            return await self.control_now(update, context)
        elif query.data == "schedule":
            return await self.schedule_handler(update, context)
        elif query.data == "view_schedules":
            await self.view_schedules(update, context)
        elif query.data == "door_status":
            await self.door_status_handler(update, context)
        elif query.data == "cancel":
            return await self.cancel(update, context)
        elif query.data.startswith("door_"):
            return await self.door_selected(update, context)
        elif query.data.startswith("action_"):
            return await self.action_selected(update, context)

    def run(self):
        """Run the bot"""
        # Create the Application
        application = Application.builder().token(self.telegram_token).build()

        # Add handlers
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help_command))

        # Conversation handler for door control
        conv_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.button_handler)],
            states={
                SELECTING_ACTION: [CallbackQueryHandler(self.button_handler)],
                SELECTING_TIME: [CallbackQueryHandler(self.button_handler)],
                CONFIRMING: [CallbackQueryHandler(self.button_handler)],
            },
            fallbacks=[CallbackQueryHandler(self.cancel, pattern="^cancel$")],
        )

        application.add_handler(conv_handler)
        application.add_handler(CallbackQueryHandler(self.button_handler))

        # Start the bot
        logger.info("Starting UniFi Access Telegram Bot...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """Main function to start the bot"""
    # Load configuration from environment variables
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    UNIFI_HOST = os.getenv('UNIFI_ACCESS_HOST')
    UNIFI_USERNAME = os.getenv('UNIFI_ACCESS_USERNAME', '')
    UNIFI_PASSWORD = os.getenv('UNIFI_ACCESS_PASSWORD', '')
    UNIFI_API_KEY = os.getenv('UNIFI_API_KEY', '')  # For cloud access
    UNIFI_SITE_ID = os.getenv('UNIFI_SITE_ID', '')  # For cloud access
    ALLOWED_USER_IDS = os.getenv('ALLOWED_TELEGRAM_USERS', '')
    VERIFY_SSL = os.getenv('VERIFY_SSL', 'true').lower() == 'true'

    # Determine if using cloud or local access
    is_cloud = 'api.ui.com' in UNIFI_HOST or 'unifi.ui.com' in UNIFI_HOST if UNIFI_HOST else False

    # Validate configuration
    if not TELEGRAM_TOKEN or not UNIFI_HOST:
        logger.error("Missing required environment variables!")
        logger.error("Please set: TELEGRAM_BOT_TOKEN, UNIFI_ACCESS_HOST")
        return

    # Cloud mode requires API key and site ID
    if is_cloud:
        if not UNIFI_API_KEY or not UNIFI_SITE_ID:
            logger.error("Cloud mode requires UNIFI_API_KEY and UNIFI_SITE_ID!")
            logger.error("Get your API key from: https://account.ui.com/")
            logger.error("Find your site ID in the UniFi Access web console URL")
            return
        logger.info("Configured for UniFi Cloud API access")
    else:
        # Local mode requires username and password
        if not UNIFI_USERNAME or not UNIFI_PASSWORD:
            logger.error("Local mode requires UNIFI_ACCESS_USERNAME and UNIFI_ACCESS_PASSWORD!")
            return
        logger.info("Configured for local UniFi Access controller")

    # Parse allowed users
    allowed_users = []
    if ALLOWED_USER_IDS:
        try:
            allowed_users = [int(uid.strip()) for uid in ALLOWED_USER_IDS.split(',')]
        except ValueError:
            logger.error("Invalid ALLOWED_TELEGRAM_USERS format. Use comma-separated user IDs.")
            return

    if not allowed_users:
        logger.warning("No allowed users configured! Set ALLOWED_TELEGRAM_USERS environment variable.")

    # Initialize UniFi API client
    unifi_api = UniFiAccessAPI(
        host=UNIFI_HOST,
        username=UNIFI_USERNAME,
        password=UNIFI_PASSWORD,
        verify_ssl=VERIFY_SSL,
        api_key=UNIFI_API_KEY,
        site_id=UNIFI_SITE_ID
    )

    # Initialize and run bot
    bot = UniFiTelegramBot(
        telegram_token=TELEGRAM_TOKEN,
        unifi_api=unifi_api,
        allowed_users=allowed_users
    )

    try:
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    finally:
        asyncio.run(unifi_api.close())


if __name__ == '__main__':
    main()
