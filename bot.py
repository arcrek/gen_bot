#!/usr/bin/env python3
"""
Telegram Bot CSV Generator
Generates CSV files with random user data for Google Workspace bulk import.
Command: /gen <quantity> <domain>
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
from typing import Dict, List, Optional

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Configuration
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '7855180309:AAHimWXNYVXA6bEOKyneLkmkHps_XuFyhXc')
MAX_QUANTITY = 10000
RATE_LIMIT_PER_MINUTE = 5
OUTPUT_DIR = "generated_files"

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

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


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


def generate_random_user_data(domain: str) -> Dict[str, str]:
    """Generate random user data for one person."""
    if not names_database:
        raise ValueError("Names database not loaded")
    
    # Select random first and last names
    first_name = random.choice(names_database).title()
    last_name = random.choice(names_database).title()
    
    # Generate 3-digit random number (001-999)
    random_number = random.randint(1, 999)
    
    # Create email address
    email = f"{first_name.lower()}{last_name.lower()}{random_number:03d}@{domain}"
    
    return {
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'password': 'Soller123@',
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


def generate_csv_file(quantity: int, domain: str) -> str:
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
            user_data = generate_random_user_data(domain)
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


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    welcome_message = """
🤖 **Welcome to CSV Generator Bot!**

This bot generates CSV files with random user data for Google Workspace bulk import.

**Commands:**
• `/gen <quantity> <domain>` - Generate CSV file
• `/help` - Show detailed help

**Example:**
`/gen 100 company.com`

This will generate a file named `100-company.com.csv` with 100 random users.

**Limits:**
• Maximum 10,000 users per request
• Maximum 5 requests per minute per user

Ready to generate some user data? 🚀
    """
    await update.message.reply_text(welcome_message, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    help_message = """
📋 **CSV Generator Bot Help**

**Command Format:**
`/gen <quantity> <domain>`

**Parameters:**
• `quantity` - Number of users to generate (1-10,000)
• `domain` - Email domain (e.g., company.com)

**Examples:**
• `/gen 50 example.com`
• `/gen 1000 mycompany.org`
• `/gen 5 test.co.uk`

**Output Format:**
The CSV file includes these fields:
- First Name, Last Name
- Email Address (format: firstnamelastname123@domain)
- Password (default: Soller123@)
- Org Unit Path (default: /)
- And 25 other Google Workspace fields

**Rate Limits:**
• Maximum 10,000 users per file
• Maximum 5 requests per minute
• Files are automatically cleaned up after generation

**File Naming:**
Generated files are named: `<quantity>-<domain>.csv`

Need help? Contact the bot administrator.
    """
    await update.message.reply_text(help_message, parse_mode='Markdown')


async def gen_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /gen command to generate CSV files."""
    user_id = update.effective_user.id
    
    # Check rate limiting
    if not check_rate_limit(user_id):
        await update.message.reply_text(
            "⚠️ Rate limit exceeded! You can make maximum 5 requests per minute. Please wait and try again."
        )
        return
    
    # Validate arguments
    if len(context.args) != 2:
        await update.message.reply_text(
            "❌ Invalid command format!\n\n"
            "Correct usage: `/gen <quantity> <domain>`\n"
            "Example: `/gen 100 company.com`",
            parse_mode='Markdown'
        )
        return
    
    # Parse arguments
    try:
        quantity = int(context.args[0])
        domain = context.args[1].lower()
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid quantity! Please provide a valid number.\n"
            "Example: `/gen 100 company.com`",
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
    
    # Check if names database is loaded
    if not names_database:
        await update.message.reply_text(
            "❌ Error: Names database not loaded. Please contact the administrator."
        )
        return
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        f"🔄 Generating CSV file with {quantity:,} users for domain `{domain}`...\n"
        f"Please wait, this may take a moment.",
        parse_mode='Markdown'
    )
    
    try:
        # Generate CSV file
        start_time = time.time()
        filepath = generate_csv_file(quantity, domain)
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
                       f"• Generation time: {generation_time:.2f}s\n\n"
                       f"📝 **Format:** Google Workspace bulk import\n"
                       f"🔒 **Password:** Soller123@",
                parse_mode='Markdown'
            )
        
        # Delete the processing message
        await processing_msg.delete()
        
        # Clean up the generated file
        os.remove(filepath)
        
        logger.info(f"Generated CSV for user {user_id}: {quantity} users for {domain}")
        
    except Exception as e:
        logger.error(f"Error generating CSV: {e}")
        await processing_msg.edit_text(
            "❌ An error occurred while generating the CSV file. Please try again later."
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors."""
    logger.error(f"Update {update} caused error {context.error}")


def main() -> None:
    """Main function to run the bot."""
    # Check bot token
    if BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
        logger.error("Please set your TELEGRAM_BOT_TOKEN environment variable!")
        print("❌ Error: Please set your TELEGRAM_BOT_TOKEN environment variable!")
        print("You can get a bot token from @BotFather on Telegram.")
        return
    
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
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("gen", gen_command))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start the bot
    logger.info("Starting Telegram Bot CSV Generator...")
    print("🤖 Starting Telegram Bot CSV Generator...")
    print(f"📊 Loaded {len(names_database):,} names from database")
    print(f"📁 Output directory: {OUTPUT_DIR}")
    print(f"⚡ Rate limit: {RATE_LIMIT_PER_MINUTE} requests per minute")
    print(f"📝 Max quantity: {MAX_QUANTITY:,} users per file")
    print("🚀 Bot is running! Press Ctrl+C to stop.")
    
    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main() 