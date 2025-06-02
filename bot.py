#!/usr/bin/env python3
"""
Telegram Bot CSV Generator
Generates CSV files with random user data for Google Workspace bulk import.
Command: /g <quantity> <domain> [password]
Authentication required - Admin controlled access
"""

import asyncio
import csv
import json
import logging
import os
import random
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler

# Configuration
BOT_TOKEN = os.getenv('TELEGRAM_BOTCSV_TOKEN', 'TOKEN_HERE')
MAX_QUANTITY = 10000
RATE_LIMIT_PER_MINUTE = 5
OUTPUT_DIR = "generated_files"

# Admin User IDs (hardcoded)
ADMIN_IDS = {1241761975, 1355685828}

# Authentication files
AUTH_FILE = "authorized_users.json"
PENDING_USERNAMES_FILE = "pending_usernames.json"

# CSV Header as specified in the requirements
CSV_HEADER = [
    "First Name [Required]",
    "Last Name [Required]", 
    "Email Address [Required]",
    "Password [Required]",
    "Password Hash Function [UPLOAD ONLY]",
    "Org Unit Path [Required]",
    "New Primary Email [UPLOAD ONLY]",
    "Recovery Email",
    "Home Secondary Email", 
    "Work Secondary Email",
    "Recovery Phone [MUST BE IN THE E.164 FORMAT]",
    "Work Phone",
    "Home Phone",
    "Mobile Phone",
    "Work Address",
    "Home Address",
    "Employee ID",
    "Employee Type",
    "Employee Title",
    "Manager Email",
    "Department",
    "Cost Center",
    "Building ID",
    "Floor Name",
    "Floor Section",
    "Change Password at Next Sign-In",
    "New Status [UPLOAD ONLY]",
    "New Licenses [UPLOAD ONLY]",
    "Advanced Protection Program enrollment"
]

# Global variables
names_database: List[str] = []
user_requests: Dict[int, List[float]] = {}
authorized_users: Set[int] = set()
pending_usernames: Set[str] = set()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def load_authorized_users() -> None:
    """Load authorized users from file."""
    global authorized_users
    try:
        with open(AUTH_FILE, 'r', encoding='utf-8') as file:
            user_list = json.load(file)
            authorized_users = set(user_list)
            # Always include admins
            authorized_users.update(ADMIN_IDS)
        logger.info(f"Loaded {len(authorized_users)} authorized users")
    except FileNotFoundError:
        # Create file with only admins
        authorized_users = ADMIN_IDS.copy()
        save_authorized_users()
        logger.info("Created new authorized users file with admin users")
    except json.JSONDecodeError:
        logger.error("Invalid JSON format in authorized_users.json!")
        authorized_users = ADMIN_IDS.copy()
        save_authorized_users()


def save_authorized_users() -> None:
    """Save authorized users to file."""
    try:
        with open(AUTH_FILE, 'w', encoding='utf-8') as file:
            json.dump(list(authorized_users), file, indent=2)
        logger.info("Saved authorized users to file")
    except Exception as e:
        logger.error(f"Error saving authorized users: {e}")


def load_pending_usernames() -> None:
    """Load pending usernames from file."""
    global pending_usernames
    try:
        with open(PENDING_USERNAMES_FILE, 'r', encoding='utf-8') as file:
            username_list = json.load(file)
            pending_usernames = set(username_list)
        logger.info(f"Loaded {len(pending_usernames)} pending usernames")
    except FileNotFoundError:
        # Create empty file
        pending_usernames = set()
        save_pending_usernames()
        logger.info("Created new pending usernames file")
    except json.JSONDecodeError:
        logger.error("Invalid JSON format in pending_usernames.json!")
        pending_usernames = set()
        save_pending_usernames()


def save_pending_usernames() -> None:
    """Save pending usernames to file."""
    try:
        with open(PENDING_USERNAMES_FILE, 'w', encoding='utf-8') as file:
            json.dump(list(pending_usernames), file, indent=2)
        logger.info("Saved pending usernames to file")
    except Exception as e:
        logger.error(f"Error saving pending usernames: {e}")


def is_admin(user_id: int) -> bool:
    """Check if user is an admin."""
    return user_id in ADMIN_IDS


def is_authorized(user_id: int) -> bool:
    """Check if user is authorized to use the bot."""
    return user_id in authorized_users


def check_and_authorize_username(username: str, user_id: int) -> bool:
    """Check if username is in pending list and authorize if found."""
    if username and username.lower() in {u.lower() for u in pending_usernames}:
        # Find the exact case username to remove
        username_to_remove = None
        for pending_username in pending_usernames:
            if pending_username.lower() == username.lower():
                username_to_remove = pending_username
                break
        
        if username_to_remove:
            # Add user to authorized list
            authorized_users.add(user_id)
            save_authorized_users()
            
            # Remove from pending list
            pending_usernames.remove(username_to_remove)
            save_pending_usernames()
            
            logger.info(f"Auto-authorized user {user_id} (@{username}) from pending list")
            return True
    return False


def load_names_database() -> bool:
    """Load names from name_us.json file."""
    global names_database
    try:
        with open('name_us.json', 'r', encoding='utf-8') as file:
            names_database = json.load(file)
        logger.info(f"Loaded {len(names_database)} names from database")
        return True
    except FileNotFoundError:
        logger.error("name_us.json file not found!")
        return False
    except json.JSONDecodeError:
        logger.error("Invalid JSON format in name_us.json!")
        return False
    except Exception as e:
        logger.error(f"Error loading names database: {e}")
        return False


def is_valid_domain(domain: str) -> bool:
    """Validate domain format using regex."""
    pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
    return bool(re.match(pattern, domain)) and len(domain) <= 253


def check_rate_limit(user_id: int) -> bool:
    """Check if user has exceeded rate limit."""
    current_time = time.time()
    if user_id not in user_requests:
        user_requests[user_id] = []
    
    # Remove requests older than 1 minute
    user_requests[user_id] = [
        req_time for req_time in user_requests[user_id] 
        if current_time - req_time < 60
    ]
    
    # Check if user has exceeded rate limit
    if len(user_requests[user_id]) >= RATE_LIMIT_PER_MINUTE:
        return False
    
    # Add current request
    user_requests[user_id].append(current_time)
    return True


def generate_random_user_data(domain: str, password: str = 'Soller123@') -> Dict[str, str]:
    """Generate random user data for one person."""
    if not names_database:
        raise ValueError("Names database not loaded")
    
    # Select random first and last names
    first_name = random.choice(names_database).title()
    last_name = random.choice(names_database).title()
    
    # Generate random number from 1950 to 2100
    random_number = random.randint(1950, 2100)
    
    # Create email address
    email = f"{first_name.lower()}{last_name.lower()}{random_number}@{domain}"
    
    return {
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'password': password,
        'password_hash_function': '',
        'org_unit_path': '/',
        'new_primary_email': '',
        'recovery_email': '',
        'home_secondary_email': '',
        'work_secondary_email': '',
        'recovery_phone': '',
        'work_phone': '',
        'home_phone': '',
        'mobile_phone': '',
        'work_address': '',
        'home_address': '',
        'employee_id': '',
        'employee_type': '',
        'employee_title': '',
        'manager_email': '',
        'department': '',
        'cost_center': '',
        'building_id': '',
        'floor_name': '',
        'floor_section': '',
        'change_password_at_next_sign_in': '',
        'new_status': '',
        'new_licenses': '',
        'advanced_protection_program_enrollment': ''
    }


def generate_csv_file(quantity: int, domain: str, password: str = 'Soller123@') -> str:
    """Generate CSV file with specified quantity of users."""
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Generate filename
    filename = f"{quantity}-{domain}.csv"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    # Generate CSV data
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header
        writer.writerow(CSV_HEADER)
        
        # Generate and write user data
        for _ in range(quantity):
            user_data = generate_random_user_data(domain, password)
            row = [
                user_data['first_name'],
                user_data['last_name'],
                user_data['email'],
                user_data['password'],
                user_data['password_hash_function'],
                user_data['org_unit_path'],
                user_data['new_primary_email'],
                user_data['recovery_email'],
                user_data['home_secondary_email'],
                user_data['work_secondary_email'],
                user_data['recovery_phone'],
                user_data['work_phone'],
                user_data['home_phone'],
                user_data['mobile_phone'],
                user_data['work_address'],
                user_data['home_address'],
                user_data['employee_id'],
                user_data['employee_type'],
                user_data['employee_title'],
                user_data['manager_email'],
                user_data['department'],
                user_data['cost_center'],
                user_data['building_id'],
                user_data['floor_name'],
                user_data['floor_section'],
                user_data['change_password_at_next_sign_in'],
                user_data['new_status'],
                user_data['new_licenses'],
                user_data['advanced_protection_program_enrollment']
            ]
            writer.writerow(row)
    
    return filepath


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all messages to check for username authentication."""
    user_id = update.effective_user.id
    username = update.effective_user.username
    
    # Check if user is pending authentication by username
    if username and not is_authorized(user_id):
        was_authorized = check_and_authorize_username(username, user_id)
        if was_authorized:
            await update.message.reply_text(
                f"🎉 **Welcome!**\n\n"
                f"You have been automatically authorized based on your username @{username}!\n\n"
                f"You can now use the bot. Type /start to see available commands.",
                parse_mode='Markdown'
            )
            return


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    # Check if user should be auto-authorized by username
    if username != "Unknown" and not is_authorized(user_id):
        was_authorized = check_and_authorize_username(username, user_id)
        if was_authorized:
            await update.message.reply_text(
                f"🎉 **Automatically Authorized!**\n\n"
                f"Welcome @{username}! You have been automatically authorized.\n\n"
                f"Proceeding to show you the bot features...",
                parse_mode='Markdown'
            )
    
    if not is_authorized(user_id):
        await update.message.reply_text(
            "🚫 **Access Denied**\n\n"
            f"Your user ID: `{user_id}`\n"
            f"Username: @{username}\n\n"
            "You are not authorized to use this bot. Please contact an administrator to request access.",
            parse_mode='Markdown'
        )
        logger.warning(f"Unauthorized access attempt by user {user_id} (@{username})")
        return
    
    admin_status = "👑 Admin" if is_admin(user_id) else "👤 User"
    
    # Create inline keyboard for start command
    keyboard = [
        [
            InlineKeyboardButton("📋 Open Menu", callback_data="menu_main"),
            InlineKeyboardButton("📊 Generate CSV", callback_data="menu_generate")
        ],
        [
            InlineKeyboardButton("❓ Help", callback_data="menu_help")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_message = f"""
🤖 **Welcome to CSV Generator Bot!**

Status: {admin_status}
User ID: `{user_id}`

This bot generates CSV files with random user data for Google Workspace bulk import.

**Quick Start:**
• Use `/menu` for interactive navigation
• Use `/g <quantity> <domain> [password]` to generate files

**Example:**
`/g 100 company.com` - Generate 100 users for company.com

**Limits:**
• Maximum 10,000 users per request
• Maximum 5 requests per minute per user

Ready to generate some user data? 🚀
    """

    await update.message.reply_text(
        welcome_message, 
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    user_id = update.effective_user.id
    
    if not is_authorized(user_id):
        await update.message.reply_text(
            "🚫 You are not authorized to use this bot. Please contact an administrator."
        )
        return
    
    help_message = """
📋 **CSV Generator Bot Help**

**Command Format:**
`/g <quantity> <domain> [password]`

**Parameters:**
• `quantity` - Number of users to generate (1-10,000)
• `domain` - Email domain (e.g., company.com)
• `password` - Optional custom password (default: Soller123@)

**Examples:**
• `/g 50 example.com` (default password)
• `/g 1000 mycompany.org` (default password)
• `/g 100 test.com MyPass123` (custom password)
• `/g 500 company.net SecurePassword!` (custom password)

**Output Format:**
The CSV file includes these fields:
- First Name, Last Name
- Email Address (format: firstnamelastname123@domain)
- Password (default: Soller123@ or your custom password)
- Org Unit Path (default: /)
- And 25 other Google Workspace fields

**Rate Limits:**
• Maximum 10,000 users per file
• Maximum 5 requests per minute
• Files are automatically cleaned up after generation

**File Naming:**
Generated files are named: `<quantity>-<domain>.csv`
"""

    if is_admin(user_id):
        help_message += """

**Admin Commands:**
• `/adduser <user_id>` - Grant access to a user by ID
• `/addusername <username>` - Grant access to a user by username  
• `/removeuser <user_id>` - Remove access from a user
• `/listusers` - List all authorized users
• `/pendingusers` - List pending usernames
• `/removeusername <username>` - Remove pending username
• `/stats` - Bot statistics

**Admin Examples:**
• `/adduser 123456789` - Add user ID 123456789
• `/addusername johndoe` - Add username (without @)
• `/removeuser 123456789` - Remove user ID 123456789
• `/removeusername johndoe` - Remove pending username
"""

    help_message += "\n\nNeed help? Contact the bot administrator."
    await update.message.reply_text(help_message, parse_mode='Markdown')


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command to show user's access status."""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    status_message = f"""
📊 **Your Status**

User ID: `{user_id}`
Username: @{username}
Authorization: {"✅ Authorized" if is_authorized(user_id) else "❌ Not Authorized"}
Admin: {"👑 Yes" if is_admin(user_id) else "👤 No"}

Total Authorized Users: {len(authorized_users)}
Pending Usernames: {len(pending_usernames)}
    """
    
    await update.message.reply_text(status_message, parse_mode='Markdown')


async def adduser_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /adduser command (admin only)."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("🚫 This command is only available to administrators.")
        return
    
    if len(context.args) != 1:
        await update.message.reply_text(
            "❌ Invalid format!\n\n"
            "Usage: `/adduser <user_id>`\n"
            "Example: `/adduser 123456789`",
            parse_mode='Markdown'
        )
        return
    
    try:
        target_user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID! Please provide a numeric user ID.")
        return
    
    if target_user_id in authorized_users:
        await update.message.reply_text(f"ℹ️ User `{target_user_id}` is already authorized.", parse_mode='Markdown')
        return
    
    authorized_users.add(target_user_id)
    save_authorized_users()
    
    await update.message.reply_text(
        f"✅ **User Added Successfully!**\n\n"
        f"User ID: `{target_user_id}`\n"
        f"Total authorized users: {len(authorized_users)}",
        parse_mode='Markdown'
    )
    
    logger.info(f"Admin {user_id} added user {target_user_id} to authorized list")


async def addusername_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /addusername command (admin only)."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("🚫 This command is only available to administrators.")
        return
    
    if len(context.args) != 1:
        await update.message.reply_text(
            "❌ Invalid format!\n\n"
            "Usage: `/addusername <username>`\n"
            "Example: `/addusername johndoe` (without @)",
            parse_mode='Markdown'
        )
        return
    
    username = context.args[0].strip().lstrip('@')  # Remove @ if present
    
    if not username:
        await update.message.reply_text("❌ Invalid username! Please provide a valid username.")
        return
    
    if username in pending_usernames:
        await update.message.reply_text(f"ℹ️ Username `@{username}` is already in pending list.", parse_mode='Markdown')
        return
    
    pending_usernames.add(username)
    save_pending_usernames()
    
    await update.message.reply_text(
        f"✅ **Username Added to Pending List!**\n\n"
        f"Username: `@{username}`\n"
        f"When this user interacts with the bot, they will be automatically authorized.\n\n"
        f"Total pending usernames: {len(pending_usernames)}",
        parse_mode='Markdown'
    )
    
    logger.info(f"Admin {user_id} added username @{username} to pending list")


async def removeuser_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /removeuser command (admin only)."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("🚫 This command is only available to administrators.")
        return
    
    if len(context.args) != 1:
        await update.message.reply_text(
            "❌ Invalid format!\n\n"
            "Usage: `/removeuser <user_id>`\n"
            "Example: `/removeuser 123456789`",
            parse_mode='Markdown'
        )
        return
    
    try:
        target_user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID! Please provide a numeric user ID.")
        return
    
    if target_user_id in ADMIN_IDS:
        await update.message.reply_text("🚫 Cannot remove admin users from the authorized list.")
        return
    
    if target_user_id not in authorized_users:
        await update.message.reply_text(f"ℹ️ User `{target_user_id}` is not in the authorized list.", parse_mode='Markdown')
        return
    
    authorized_users.remove(target_user_id)
    save_authorized_users()
    
    await update.message.reply_text(
        f"✅ **User Removed Successfully!**\n\n"
        f"User ID: `{target_user_id}`\n"
        f"Total authorized users: {len(authorized_users)}",
        parse_mode='Markdown'
    )
    
    logger.info(f"Admin {user_id} removed user {target_user_id} from authorized list")


async def removeusername_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /removeusername command (admin only)."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("🚫 This command is only available to administrators.")
        return
    
    if len(context.args) != 1:
        await update.message.reply_text(
            "❌ Invalid format!\n\n"
            "Usage: `/removeusername <username>`\n"
            "Example: `/removeusername johndoe` (without @)",
            parse_mode='Markdown'
        )
        return
    
    username = context.args[0].strip().lstrip('@')  # Remove @ if present
    
    if not username:
        await update.message.reply_text("❌ Invalid username! Please provide a valid username.")
        return
    
    # Find username (case-insensitive)
    username_to_remove = None
    for pending_username in pending_usernames:
        if pending_username.lower() == username.lower():
            username_to_remove = pending_username
            break
    
    if not username_to_remove:
        await update.message.reply_text(f"ℹ️ Username `@{username}` is not in the pending list.", parse_mode='Markdown')
        return
    
    pending_usernames.remove(username_to_remove)
    save_pending_usernames()
    
    await update.message.reply_text(
        f"✅ **Username Removed Successfully!**\n\n"
        f"Username: `@{username_to_remove}`\n"
        f"Total pending usernames: {len(pending_usernames)}",
        parse_mode='Markdown'
    )
    
    logger.info(f"Admin {user_id} removed username @{username_to_remove} from pending list")


async def listusers_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /listusers command (admin only)."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("🚫 This command is only available to administrators.")
        return
    
    if not authorized_users:
        await update.message.reply_text("📝 No authorized users found.")
        return
    
    admin_users = [uid for uid in authorized_users if uid in ADMIN_IDS]
    regular_users = [uid for uid in authorized_users if uid not in ADMIN_IDS]
    
    message = "📝 **Authorized Users List**\n\n"
    
    if admin_users:
        message += "👑 **Admins:**\n"
        for admin_id in sorted(admin_users):
            message += f"• `{admin_id}`\n"
        message += "\n"
    
    if regular_users:
        message += "👤 **Regular Users:**\n"
        for reg_id in sorted(regular_users):
            message += f"• `{reg_id}`\n"
        message += "\n"
    
    message += f"**Total:** {len(authorized_users)} users"
    
    await update.message.reply_text(message, parse_mode='Markdown')


async def pendingusers_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /pendingusers command (admin only)."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("🚫 This command is only available to administrators.")
        return
    
    if not pending_usernames:
        await update.message.reply_text("📝 No pending usernames found.")
        return
    
    message = "⏳ **Pending Usernames**\n\n"
    message += "These users will be automatically authorized when they interact with the bot:\n\n"
    
    for username in sorted(pending_usernames):
        message += f"• `@{username}`\n"
    
    message += f"\n**Total:** {len(pending_usernames)} pending usernames"
    
    await update.message.reply_text(message, parse_mode='Markdown')


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stats command (admin only)."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("🚫 This command is only available to administrators.")
        return
    
    admin_count = len([uid for uid in authorized_users if uid in ADMIN_IDS])
    regular_count = len(authorized_users) - admin_count
    
    stats_message = f"""
📊 **Bot Statistics**

**Users:**
• Total Authorized: {len(authorized_users)}
• Admins: {admin_count}
• Regular Users: {regular_count}
• Pending Usernames: {len(pending_usernames)}

**Database:**
• Names in database: {len(names_database):,}
• Active requests tracking: {len(user_requests)} users

**Configuration:**
• Max quantity per request: {MAX_QUANTITY:,}
• Rate limit: {RATE_LIMIT_PER_MINUTE} requests/minute
• Output directory: `{OUTPUT_DIR}`
    """
    
    await update.message.reply_text(stats_message, parse_mode='Markdown')


async def g_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /g command to generate CSV files with optional custom password."""
    user_id = update.effective_user.id
    
    # Check authorization first
    if not is_authorized(user_id):
        await update.message.reply_text(
            "🚫 You are not authorized to use this bot. Please contact an administrator for access."
        )
        return
    
    # Check rate limiting
    if not check_rate_limit(user_id):
        await update.message.reply_text(
            "⚠️ Rate limit exceeded! You can make maximum 5 requests per minute. Please wait and try again."
        )
        return
    
    # Validate arguments (2 or 3 arguments allowed)
    if len(context.args) < 2 or len(context.args) > 3:
        await update.message.reply_text(
            "❌ Invalid command format!\n\n"
            "Correct usage: `/g <quantity> <domain> [password]`\n\n"
            "Examples:\n"
            "• `/g 100 company.com` (default password)\n"
            "• `/g 100 company.com MyPassword123` (custom password)",
            parse_mode='Markdown'
        )
        return
    
    # Parse arguments
    try:
        quantity = int(context.args[0])
        domain = context.args[1].lower()
        password = 'Soller123@' if len(context.args) == 2 else context.args[2]
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid quantity! Please provide a valid number.\n"
            "Examples:\n"
            "• `/g 100 company.com`\n"
            "• `/g 100 company.com MyPassword123`",
            parse_mode='Markdown'
        )
        return
    
    # Validate quantity
    if quantity < 1 or quantity > MAX_QUANTITY:
        await update.message.reply_text(
            f"❌ Invalid quantity! Please provide a number between 1 and {MAX_QUANTITY:,}."
        )
        return
    
    # Validate domain
    if not is_valid_domain(domain):
        await update.message.reply_text(
            "❌ Invalid domain format! Please provide a valid domain.\n"
            "Example: `company.com`, `example.org`",
            parse_mode='Markdown'
        )
        return
    
    # Validate password (basic check for custom password)
    if len(context.args) == 3 and len(password.strip()) < 1:
        await update.message.reply_text(
            "❌ Invalid password! Password cannot be empty.\n"
            "Example: `/g 100 company.com MyPassword123`",
            parse_mode='Markdown'
        )
        return
    
    # Check if names database is loaded
    if not names_database:
        await update.message.reply_text(
            "❌ Error: Names database not loaded. Please contact the administrator."
        )
        return
    
    # Determine if using default or custom password
    is_default_password = len(context.args) == 2
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        f"🔄 Generating CSV file with {quantity:,} users for domain `{domain}`...\n"
        f"Password: `{'Default (Soller123@)' if is_default_password else 'Custom'}`\n"
        f"Please wait, this may take a moment.",
        parse_mode='Markdown'
    )
    
    try:
        # Generate CSV file
        start_time = time.time()
        filepath = generate_csv_file(quantity, domain, password)
        generation_time = time.time() - start_time
        
        # Get file size
        file_size = os.path.getsize(filepath)
        file_size_mb = file_size / (1024 * 1024)
        
        # Check Telegram file size limit (50 MB)
        if file_size_mb > 50:
            await processing_msg.edit_text(
                f"❌ Generated file is too large ({file_size_mb:.1f} MB). "
                f"Telegram has a 50 MB limit. Please reduce the quantity."
            )
            # Clean up the file
            os.remove(filepath)
            return
        
        # Send the file
        with open(filepath, 'rb') as file:
            await update.message.reply_document(
                document=file,
                filename=os.path.basename(filepath),
                caption=f"✅ **CSV Generated Successfully!**\n\n"
                       f"📊 **Details:**\n"
                       f"• Users: {quantity:,}\n"
                       f"• Domain: `{domain}`\n"
                       f"• File size: {file_size_mb:.2f} MB\n"
                       f"• Generation time: {generation_time:.2f}s\n"
                       f"• Password: `{'Soller123@' if is_default_password else 'Custom'}`\n\n"
                       f"📝 **Format:** Google Workspace bulk import",
                parse_mode='Markdown'
            )
        
        # Delete the processing message
        await processing_msg.delete()
        
        # Clean up the generated file
        os.remove(filepath)
        
        logger.info(f"Generated CSV for user {user_id}: {quantity} users for {domain} with {'default' if is_default_password else 'custom'} password")
        
    except Exception as e:
        logger.error(f"Error generating CSV: {e}")
        await processing_msg.edit_text(
            "❌ An error occurred while generating the CSV file. Please try again later."
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors."""
    logger.error(f"Update {update} caused error {context.error}")


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /menu command - Show main menu with inline keyboard."""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"
    
    # Check if user should be auto-authorized by username
    if username != "Unknown" and not is_authorized(user_id):
        was_authorized = check_and_authorize_username(username, user_id)
        if was_authorized:
            await update.message.reply_text(
                f"🎉 **Automatically Authorized!**\n\n"
                f"Welcome @{username}! You have been automatically authorized.\n\n"
                f"Showing you the bot menu...",
                parse_mode='Markdown'
            )
    
    if not is_authorized(user_id):
        await update.message.reply_text(
            "🚫 **Access Denied**\n\n"
            f"Your user ID: `{user_id}`\n"
            f"Username: @{username}\n\n"
            "You are not authorized to use this bot. Please contact an administrator to request access.",
            parse_mode='Markdown'
        )
        return
    
    # Create main menu keyboard
    keyboard = [
        [
            InlineKeyboardButton("📊 Generate CSV", callback_data="menu_generate"),
            InlineKeyboardButton("❓ Help", callback_data="menu_help")
        ],
        [
            InlineKeyboardButton("📋 Status", callback_data="menu_status"),
            InlineKeyboardButton("📖 Examples", callback_data="menu_examples")
        ]
    ]
    
    # Add admin menu for admins
    if is_admin(user_id):
        keyboard.append([
            InlineKeyboardButton("👑 Admin Panel", callback_data="menu_admin")
        ])
    
    keyboard.append([
        InlineKeyboardButton("🔄 Refresh Menu", callback_data="menu_main")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    admin_status = "👑 Admin" if is_admin(user_id) else "👤 User"
    
    menu_text = f"""
🤖 **CSV Generator Bot Menu**

Welcome back! 👋
Status: {admin_status}
User ID: `{user_id}`

Choose an option from the menu below:
    """
    
    await update.message.reply_text(
        menu_text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries from inline keyboards."""
    query = update.callback_query
    user_id = query.from_user.id
    
    # Answer the callback query to remove loading state
    await query.answer()
    
    if not is_authorized(user_id):
        await query.edit_message_text(
            "🚫 You are not authorized to use this bot. Please contact an administrator."
        )
        return
    
    data = query.data
    
    if data == "menu_main":
        await show_main_menu(query, user_id)
    elif data == "menu_generate":
        await show_generate_menu(query)
    elif data == "menu_help":
        await show_help_menu(query, user_id)
    elif data == "menu_status":
        await show_status_menu(query, user_id)
    elif data == "menu_examples":
        await show_examples_menu(query)
    elif data == "menu_admin" and is_admin(user_id):
        await show_admin_menu(query)
    elif data == "admin_users":
        await show_admin_users_menu(query)
    elif data == "admin_usernames":
        await show_admin_usernames_menu(query)
    elif data == "admin_stats":
        await show_admin_stats_menu(query, user_id)
    elif data == "back_to_main":
        await show_main_menu(query, user_id)
    elif data == "back_to_admin":
        await show_admin_menu(query)


async def show_main_menu(query, user_id: int) -> None:
    """Show the main menu."""
    keyboard = [
        [
            InlineKeyboardButton("📊 Generate CSV", callback_data="menu_generate"),
            InlineKeyboardButton("❓ Help", callback_data="menu_help")
        ],
        [
            InlineKeyboardButton("📋 Status", callback_data="menu_status"),
            InlineKeyboardButton("📖 Examples", callback_data="menu_examples")
        ]
    ]
    
    if is_admin(user_id):
        keyboard.append([
            InlineKeyboardButton("👑 Admin Panel", callback_data="menu_admin")
        ])
    
    keyboard.append([
        InlineKeyboardButton("🔄 Refresh Menu", callback_data="menu_main")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    admin_status = "👑 Admin" if is_admin(user_id) else "👤 User"
    
    text = f"""
🤖 **CSV Generator Bot Menu**

Welcome back! 👋
Status: {admin_status}
User ID: `{user_id}`

Choose an option from the menu below:
    """
    
    await query.edit_message_text(
        text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


async def show_generate_menu(query) -> None:
    """Show the generate CSV menu."""
    keyboard = [
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = """
📊 **Generate CSV File**

To generate a CSV file, use this command format:

`/g <quantity> <domain> [password]`

**Parameters:**
• `quantity` - Number of users (1-10,000)
• `domain` - Email domain (e.g., company.com)
• `password` - Optional custom password

**Quick Examples:**
• `/g 100 company.com` (default password)
• `/g 500 test.org MyPassword123` (custom password)

**Default Password:** Soller123@

Just type your command in the chat!
    """
    
    await query.edit_message_text(
        text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


async def show_help_menu(query, user_id: int) -> None:
    """Show the help menu."""
    keyboard = [
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = """
❓ **Help & Information**

**Main Command:**
`/g <quantity> <domain> [password]`

**Available Commands:**
• `/menu` - Show this menu
• `/start` - Bot introduction
• `/help` - Detailed help
• `/status` - Your access status
• `/g` - Generate CSV file

**Limits:**
• Max 10,000 users per file
• Max 5 requests per minute
• Files auto-deleted after sending

**Support:**
Contact bot administrator for assistance.
    """
    
    if is_admin(user_id):
        text += """

**Admin Commands:**
• `/adduser <id>` - Add user by ID
• `/addusername <name>` - Add user by username
• `/removeuser <id>` - Remove user
• `/listusers` - List all users
• `/stats` - Bot statistics
"""
    
    await query.edit_message_text(
        text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


async def show_status_menu(query, user_id: int) -> None:
    """Show the status menu."""
    keyboard = [
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    username = query.from_user.username or "Unknown"
    
    text = f"""
📋 **Your Status**

**User Information:**
• User ID: `{user_id}`
• Username: @{username}
• Authorization: ✅ Authorized
• Admin: {"👑 Yes" if is_admin(user_id) else "👤 No"}

**Bot Statistics:**
• Total Authorized Users: {len(authorized_users)}
• Pending Usernames: {len(pending_usernames)}
• Names in Database: {len(names_database):,}

**Your Limits:**
• Max quantity: {MAX_QUANTITY:,} users per file
• Rate limit: {RATE_LIMIT_PER_MINUTE} requests per minute
    """
    
    await query.edit_message_text(
        text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


async def show_examples_menu(query) -> None:
    """Show the examples menu."""
    keyboard = [
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = """
📖 **Command Examples**

**Basic Usage:**
• `/g 50 company.com`
  → 50 users with default password

• `/g 1000 example.org`
  → 1000 users with default password

**Custom Password:**
• `/g 100 test.com MyPass123`
  → 100 users with custom password

• `/g 500 corp.net SecurePass!`
  → 500 users with custom password

**Common Domains:**
• `.com` - Commercial
• `.org` - Organization
• `.net` - Network
• `.edu` - Educational
• `.gov` - Government

**Tips:**
• Use realistic quantities (10-1000 typical)
• Domain must be valid format
• Custom passwords override default
• Files are automatically formatted for Google Workspace
    """
    
    await query.edit_message_text(
        text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


async def show_admin_menu(query) -> None:
    """Show the admin menu."""
    keyboard = [
        [
            InlineKeyboardButton("👥 Manage Users", callback_data="admin_users"),
            InlineKeyboardButton("📝 Manage Usernames", callback_data="admin_usernames")
        ],
        [
            InlineKeyboardButton("📊 Statistics", callback_data="admin_stats")
        ],
        [
            InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    admin_count = len([uid for uid in authorized_users if uid in ADMIN_IDS])
    regular_count = len(authorized_users) - admin_count
    
    text = f"""
👑 **Admin Panel**

**Quick Overview:**
• Total Users: {len(authorized_users)}
• Admins: {admin_count}
• Regular Users: {regular_count}
• Pending Usernames: {len(pending_usernames)}

**Available Actions:**
Choose an option below to manage the bot.
    """
    
    await query.edit_message_text(
        text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


async def show_admin_users_menu(query) -> None:
    """Show the admin users management menu."""
    keyboard = [
        [InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="back_to_admin")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    admin_users = [uid for uid in authorized_users if uid in ADMIN_IDS]
    regular_users = [uid for uid in authorized_users if uid not in ADMIN_IDS]
    
    text = "👥 **User Management**\n\n"
    
    if admin_users:
        text += "👑 **Admins:**\n"
        for admin_id in sorted(admin_users):
            text += f"• `{admin_id}`\n"
        text += "\n"
    
    if regular_users:
        text += "👤 **Regular Users:**\n"
        for reg_id in sorted(regular_users):
            text += f"• `{reg_id}`\n"
        text += "\n"
    
    text += f"**Total:** {len(authorized_users)} users\n\n"
    text += "**Commands:**\n"
    text += "• `/adduser <user_id>` - Add user by ID\n"
    text += "• `/removeuser <user_id>` - Remove user\n"
    text += "• `/listusers` - Detailed list"
    
    await query.edit_message_text(
        text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


async def show_admin_usernames_menu(query) -> None:
    """Show the admin usernames management menu."""
    keyboard = [
        [InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="back_to_admin")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = "📝 **Username Management**\n\n"
    
    if pending_usernames:
        text += "⏳ **Pending Usernames:**\n"
        for username in sorted(pending_usernames):
            text += f"• `@{username}`\n"
        text += "\n"
    else:
        text += "⏳ **Pending Usernames:** None\n\n"
    
    text += f"**Total:** {len(pending_usernames)} pending usernames\n\n"
    text += "**Commands:**\n"
    text += "• `/addusername <username>` - Add pending username\n"
    text += "• `/removeusername <username>` - Remove pending username\n"
    text += "• `/pendingusers` - Detailed list\n\n"
    text += "**Note:** Users with pending usernames will be auto-authorized when they first interact with the bot."
    
    await query.edit_message_text(
        text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


async def show_admin_stats_menu(query, user_id: int) -> None:
    """Show the admin statistics menu."""
    keyboard = [
        [InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="back_to_admin")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    admin_count = len([uid for uid in authorized_users if uid in ADMIN_IDS])
    regular_count = len(authorized_users) - admin_count
    
    text = f"""
📊 **Bot Statistics**

**Users:**
• Total Authorized: {len(authorized_users)}
• Admins: {admin_count}
• Regular Users: {regular_count}
• Pending Usernames: {len(pending_usernames)}

**Database:**
• Names in database: {len(names_database):,}
• Active request tracking: {len(user_requests)} users

**Configuration:**
• Max quantity per request: {MAX_QUANTITY:,}
• Rate limit: {RATE_LIMIT_PER_MINUTE} requests/minute
• Output directory: `{OUTPUT_DIR}`

**Files:**
• Authorization file: `{AUTH_FILE}`
• Pending usernames: `{PENDING_USERNAMES_FILE}`
• Names database: `name_us.json`
    """
    
    await query.edit_message_text(
        text,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


def main() -> None:
    """Main function to run the bot."""
    # Check bot token
    if BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        logger.error("Please set your TELEGRAM_BOT_TOKEN environment variable!")
        print("❌ Error: Please set your TELEGRAM_BOT_TOKEN environment variable!")
        print("You can get a bot token from @BotFather on Telegram.")
        return
    
    # Load authorized users and pending usernames
    load_authorized_users()
    load_pending_usernames()
    
    # Load names database
    if not load_names_database():
        logger.error("Failed to load names database!")
        print("❌ Error: Failed to load name_us.json file!")
        print("Make sure the name_us.json file exists in the same directory.")
        return
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add message handler for auto-authentication (should be first)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("g", g_command))
    
    # Admin commands
    application.add_handler(CommandHandler("adduser", adduser_command))
    application.add_handler(CommandHandler("addusername", addusername_command))
    application.add_handler(CommandHandler("removeuser", removeuser_command))
    application.add_handler(CommandHandler("removeusername", removeusername_command))
    application.add_handler(CommandHandler("listusers", listusers_command))
    application.add_handler(CommandHandler("pendingusers", pendingusers_command))
    application.add_handler(CommandHandler("stats", stats_command))
    
    # Add callback query handler for inline keyboards
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start the bot
    logger.info("Starting Telegram Bot CSV Generator...")
    print("🤖 Starting Telegram Bot CSV Generator...")
    print(f"📊 Loaded {len(names_database):,} names from database")
    print(f"👥 Loaded {len(authorized_users)} authorized users")
    print(f"⏳ Loaded {len(pending_usernames)} pending usernames")
    print(f"👑 Admin IDs: {', '.join(map(str, ADMIN_IDS))}")
    print(f"📁 Output directory: {OUTPUT_DIR}")
    print(f"⚡ Rate limit: {RATE_LIMIT_PER_MINUTE} requests per minute")
    print(f"📝 Max quantity: {MAX_QUANTITY:,} users per file")
    print("🚀 Bot is running! Press Ctrl+C to stop.")
    print("📋 Available commands: /menu, /g, /start, /help, /status")
    print("🔧 Admin commands: /adduser, /addusername, /removeuser, /removeusername, /listusers, /pendingusers, /stats")
    
    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main() 