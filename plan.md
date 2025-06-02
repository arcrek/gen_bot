# Telegram Bot CSV Generator Plan

## Overview
Create a Telegram bot that generates CSV files containing user data for Google Workspace bulk import. The bot responds to `/gen <quantity> <domain>` command and creates a CSV file with randomized user information.

## Features
- **Command**: `/gen <quantity> <domain>`
- **Output**: `<quantity>-<domain>.csv` file
- **Data Source**: Random names from `name_us.json`
- **Format**: Google Workspace user import format

## Technical Requirements

### 1. Bot Setup
- **Platform**: Python with `python-telegram-bot` library
- **Environment Variables**:
  - `TELEGRAM_BOT_TOKEN`: Bot token from BotFather
- **Dependencies**:
  - `python-telegram-bot>=20.0`
  - `asyncio`
  - `json`
  - `random`
  - `csv`
  - `logging`

### 2. File Structure
```
gen_bot/
├── bot.py              # Main bot script
├── name_us.json        # Names database (existing)
├── config.py           # Configuration settings
├── csv_generator.py    # CSV generation logic
├── requirements.txt    # Python dependencies
├── .env               # Environment variables
└── generated_files/   # Output directory for CSV files
```

### 3. CSV Format Specification

#### Header (Line 1)
```
First Name [Required],Last Name [Required],Email Address [Required],Password [Required],Password Hash Function [UPLOAD ONLY],Org Unit Path [Required],New Primary Email [UPLOAD ONLY],Recovery Email,Home Secondary Email,Work Secondary Email,Recovery Phone [MUST BE IN THE E.164 FORMAT],Work Phone,Home Phone,Mobile Phone,Work Address,Home Address,Employee ID,Employee Type,Employee Title,Manager Email,Department,Cost Center,Building ID,Floor Name,Floor Section,Change Password at Next Sign-In,New Status [UPLOAD ONLY],New Licenses [UPLOAD ONLY],Advanced Protection Program enrollment
```

#### Data Lines (Starting Line 2)
```
<First name>,<Last name>,<firstname+lastname+3_digit_random_number>@<domain>,Soller123@,,/,,,,,,,,,,,,,,,,,,,,,,,
```

**Example**:
```
Matthew,Young,matthewyoung278@qu.io.vn,Soller123@,,/,,,,,,,,,,,,,,,,,,,,,,,
```

### 4. Implementation Details

#### 4.1 Name Generation Logic
1. Load `name_us.json` into memory on startup
2. For each user:
   - Randomly select first name from the JSON array
   - Randomly select last name from the JSON array
   - Generate 3-digit random number (001-999)
   - Create email: `<firstname><lastname><3digits>@<domain>`
   - Convert names to proper case (first letter uppercase)

#### 4.2 Bot Commands
- `/start` - Welcome message and usage instructions
- `/help` - Command help and CSV format explanation
- `/gen <quantity> <domain>` - Generate CSV file

#### 4.3 Input Validation
- **Quantity**: Must be integer between 1-10000
- **Domain**: Must be valid domain format (basic regex validation)
- **File Size**: Limit based on Telegram's file upload restrictions

#### 4.4 Error Handling
- Invalid command parameters
- File generation errors
- Telegram API errors
- JSON parsing errors

### 5. Security Considerations
- Rate limiting per user (max 5 requests per minute)
- File size limitations
- Input sanitization for domain names
- Temporary file cleanup

### 6. Development Steps

#### Phase 1: Basic Setup
1. Set up project structure
2. Install dependencies
3. Create bot token and test basic connectivity
4. Implement `/start` and `/help` commands

#### Phase 2: Core Functionality
1. Implement JSON name loading
2. Create CSV generation logic
3. Add `/gen` command handler
4. Test with small datasets

#### Phase 3: Enhancement
1. Add input validation
2. Implement error handling
3. Add rate limiting
4. File cleanup mechanisms

#### Phase 4: Testing & Deployment
1. Comprehensive testing with various inputs
2. Performance testing with large quantities
3. Deploy bot to production environment
4. Monitor and log usage

## Sample Code Structure

### bot.py (Main Entry Point)
```python
import asyncio
import logging
from telegram.ext import Application, CommandHandler
from config import BOT_TOKEN
from csv_generator import CSVGenerator

async def gen_command(update, context):
    # Parse command arguments
    # Validate inputs
    # Generate CSV
    # Send file to user

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("gen", gen_command))
    application.run_polling()
```

### csv_generator.py (CSV Logic)
```python
import json
import csv
import random
from pathlib import Path

class CSVGenerator:
    def __init__(self):
        self.load_names()
    
    def load_names(self):
        # Load name_us.json
    
    def generate_csv(self, quantity, domain):
        # Create CSV with header and data
        # Return file path
```

## Configuration

### Environment Variables
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
MAX_QUANTITY=10000
RATE_LIMIT_PER_MINUTE=5
OUTPUT_DIR=generated_files
```

### Requirements.txt
```
python-telegram-bot>=20.0
python-dotenv>=1.0.0
```

## Testing Strategy
1. Unit tests for CSV generation
2. Integration tests for bot commands
3. Load testing with maximum quantities
4. Edge case testing (invalid inputs, network errors)

## Deployment Options
1. **Local Development**: Run on local machine
2. **VPS/Cloud**: Deploy to DigitalOcean, AWS, or similar
3. **Container**: Docker deployment for consistency
4. **Serverless**: AWS Lambda with scheduled keepalive

## Monitoring & Maintenance
- Log all bot interactions
- Monitor file generation performance
- Track error rates and types
- Regular cleanup of generated files
- Update name database periodically

## Future Enhancements
- Multiple name databases (different countries)
- Custom CSV templates
- Bulk generation for multiple domains
- User management and quotas
- Web interface for non-Telegram users 