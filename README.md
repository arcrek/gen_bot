# Telegram CSV Generator Bot

A powerful Telegram bot that generates CSV files with random user data for Google Workspace bulk import. Features admin-controlled authentication, username-based authorization, interactive menu system, and customizable password options.

## 🚀 Features

### Core Functionality
- **CSV Generation**: Generate CSV files with random user data
- **Google Workspace Compatible**: Perfect format for bulk user import
- **Custom Passwords**: Support for default or custom passwords
- **Flexible Email Format**: Uses realistic year-based email addresses (1950-2100)

### User Interface
- **Interactive Menu System**: Easy-to-use inline keyboard navigation
- **Button-Based Navigation**: Intuitive menu system with emoji icons
- **Mobile-Friendly**: Optimized for mobile Telegram usage
- **Quick Actions**: Direct access to common functions from start screen

### Authentication & Security
- **Admin Control**: Two hardcoded admin users with full control
- **User Authentication**: Only authorized users can use the bot
- **Username-based Auth**: Admins can authorize users by Telegram username
- **Auto-Authorization**: Users get automatically authorized when they first interact
- **Rate Limiting**: 5 requests per minute per user
- **Access Logging**: All unauthorized access attempts are logged

### Admin Features
- **Admin Panel**: Dedicated admin interface with organized sections
- **User Management**: Add/remove users by ID or username through menu
- **Pending System**: Pre-authorize users by username before they use the bot
- **Statistics Dashboard**: View bot usage and user statistics in organized format
- **User Lists**: View all authorized and pending users with navigation

## 📋 Commands

### User Commands
| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Show welcome message with quick action buttons | `/start` |
| `/menu` | **Open interactive menu system** | `/menu` |
| `/help` | Display detailed help information | `/help` |
| `/status` | Check your access status | `/status` |
| `/g <quantity> <domain> [password]` | Generate CSV file | `/g 100 company.com` |

### Admin Commands
| Command | Description | Example |
|---------|-------------|---------|
| `/adduser <user_id>` | Grant access to user by ID | `/adduser 123456789` |
| `/addusername <username>` | Grant access by username | `/addusername johndoe` |
| `/removeuser <user_id>` | Remove user access by ID | `/removeuser 123456789` |
| `/removeusername <username>` | Remove pending username | `/removeusername johndoe` |
| `/listusers` | List all authorized users | `/listusers` |
| `/pendingusers` | List pending usernames | `/pendingusers` |
| `/stats` | View bot statistics | `/stats` |

## 🎛️ Interactive Menu System

### Main Menu Features
- **📊 Generate CSV**: Step-by-step instructions with examples
- **❓ Help**: Comprehensive help with command reference
- **📋 Status**: Your authorization status and bot statistics
- **📖 Examples**: Detailed command examples and usage tips
- **👑 Admin Panel**: Admin-only section (for authorized administrators)

### Admin Panel (Admin Users Only)
- **👥 Manage Users**: View and manage authorized users
- **📝 Manage Usernames**: Handle pending username authorizations
- **📊 Statistics**: Detailed bot statistics and configuration info

### Navigation Features
- **🔙 Back Buttons**: Easy navigation between menu sections
- **🔄 Refresh**: Update menu with current information
- **Inline Keyboards**: Tap buttons instead of typing commands
- **Context-Aware**: Menus adapt based on user permissions

## 📊 CSV Output Format

The generated CSV files include 29 fields compatible with Google Workspace:

```csv
First Name [Required],Last Name [Required],Email Address [Required],Password [Required],...
Matthew,Young,matthewyoung1987@company.com,Soller123@,,/,,,,,,,,,,,,,,,,,,,,,,,
```

### Email Format
- **Pattern**: `<firstname><lastname><year>@<domain>`
- **Year Range**: 1950-2100
- **Examples**: 
  - `johndoe1965@company.com`
  - `janesmith2034@example.org`

## 🛠️ Setup & Installation

### Prerequisites
- Python 3.8 or higher
- Telegram Bot Token (from @BotFather)

### Installation Steps

1. **Clone or download the project files**
   ```bash
   git clone <repository-url>
   cd gen_bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your bot token**
   ```bash
   # Windows PowerShell
   $env:TELEGRAM_BOTCSV_TOKEN="YOUR_BOT_TOKEN_HERE"
   
   # Or edit bot.py and replace the token directly
   ```

4. **Ensure name_us.json exists**
   - The bot requires `name_us.json` file with an array of names
   - This file should contain a JSON array of names for random generation

5. **Run the bot**
   ```bash
   python bot.py
   ```

## 📁 File Structure

```
gen_bot/
├── bot.py                    # Main bot application
├── requirements.txt          # Python dependencies
├── name_us.json             # Names database (required)
├── authorized_users.json    # Authorized users (auto-created)
├── pending_usernames.json   # Pending usernames (auto-created)
├── generated_files/         # Output directory (auto-created)
└── README.md               # This file
```

## ⚙️ Configuration

### Admin Users
The following user IDs are hardcoded as administrators:
- `1241761975`
- `1355685828`

### Bot Settings
| Setting | Default Value | Description |
|---------|---------------|-------------|
| `MAX_QUANTITY` | 10,000 | Maximum users per CSV file |
| `RATE_LIMIT_PER_MINUTE` | 5 | Requests per minute per user |
| `OUTPUT_DIR` | `generated_files` | Directory for generated files |

### Environment Variables
| Variable | Description | Required |
|----------|-------------|----------|
| `TELEGRAM_BOTCSV_TOKEN` | Your Telegram bot token | Yes |

## 🔐 Authentication System

### Two Authorization Methods

#### 1. Direct Authorization (Immediate)
```bash
/adduser 123456789
```
- Admin adds user by Telegram ID
- User is immediately authorized
- Can use bot right away

#### 2. Username Authorization (Deferred)
```bash
/addusername johndoe
```
- Admin adds user by Telegram username
- User gets authorized when they first interact with the bot
- Automatic welcome message sent upon authorization

### Access Control Flow
1. User tries to use the bot
2. Bot checks if user is in authorized list
3. If not authorized, checks if username is in pending list
4. If in pending list, automatically authorizes and removes from pending
5. If not in either list, denies access with contact admin message

## 📱 How to Use the Bot

### Quick Start (Recommended)
1. Send `/start` to the bot
2. Click **📋 Open Menu** button
3. Navigate using the interactive menu system
4. Click **📊 Generate CSV** for instructions
5. Type your `/g` command directly in chat

### Traditional Method
1. Send `/menu` for the main menu
2. Use commands directly: `/g 100 company.com`
3. Use `/help` for detailed information

### Menu Navigation Tips
- **Tap buttons** instead of typing commands
- Use **🔙 Back** buttons to navigate between sections
- **Admin users** get additional menu options
- All information is **organized and easy to find**

## 📝 Usage Examples

### Using the Menu System
```
1. Send: /menu
2. Tap: 📊 Generate CSV
3. Read instructions
4. Type: /g 100 company.com
```

### Generate CSV with Default Password
```bash
/g 100 company.com
```
- Creates: `100-company.com.csv`
- Password: `Soller123@`
- Contains: 100 random users

### Generate CSV with Custom Password
```bash
/g 50 example.org MySecurePass123
```
- Creates: `50-example.org.csv`
- Password: `MySecurePass123`
- Contains: 50 random users

### Admin: Using Admin Panel
```
1. Send: /menu
2. Tap: 👑 Admin Panel
3. Choose: 👥 Manage Users or 📝 Manage Usernames
4. View information and use commands as needed
```

### Admin: Authorize User by Username
```bash
/addusername johndoe
```
- Adds @johndoe to pending list
- When @johndoe sends any message, they're automatically authorized

## 🚫 Rate Limiting & Security

### Rate Limits
- **5 requests per minute** per user
- Automatic cleanup of old request timestamps
- Rate limit applies to CSV generation only

### Security Features
- **Authentication Required**: Only authorized users can generate CSVs
- **Admin Protection**: Admin users cannot be removed
- **Access Logging**: Unauthorized attempts are logged
- **File Cleanup**: Generated files are automatically deleted after sending
- **Input Validation**: All user inputs are validated
- **Menu Security**: Inline keyboard callbacks respect user permissions

## 🔧 Troubleshooting

### Common Issues

#### Bot doesn't start
- Check if `TELEGRAM_BOTCSV_TOKEN` environment variable is set
- Verify bot token is valid
- Ensure `name_us.json` file exists

#### User can't access bot
- Check if user is authorized: `/listusers` (admin only)
- Add user: `/adduser <user_id>` or `/addusername <username>`
- Check user's exact ID in their `/status` command
- Try using the `/menu` command for easier navigation

#### Menu buttons don't work
- Ensure user is authorized to use the bot
- Try refreshing with `/menu` command
- Check if there are any error messages

#### CSV generation fails
- Verify domain format is valid
- Check quantity is between 1 and 10,000
- Ensure user hasn't exceeded rate limit
- Use the menu system for examples and help

### Log Files
The bot logs important events including:
- User authorizations
- CSV generation requests
- Error conditions
- Admin actions
- Menu interactions

## 📦 Dependencies

The bot requires the following Python packages:

```txt
python-telegram-bot>=20.0
```

**Note**: `python-dotenv` is no longer required as the bot uses direct environment variable access.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support or questions:
1. Use the **interactive menu system** (`/menu`) for guidance
2. Check this README
3. Contact the bot administrators
4. Check the bot logs for error messages

## 🔄 Version History

### Latest Version
- ✅ **Interactive menu system with inline keyboards**
- ✅ **Enhanced user interface with navigation buttons**
- ✅ **Admin panel with organized sections**
- ✅ Username-based authentication
- ✅ Auto-authorization system
- ✅ Email format with years (1950-2100)
- ✅ Comprehensive admin controls
- ✅ Rate limiting and security
- ✅ Google Workspace CSV format
- ✅ Mobile-optimized interface

---

**Note**: This bot is designed for Google Workspace user management. Use the interactive menu system (`/menu`) for the best experience. Always test with small quantities first and ensure you have proper authorization before bulk importing users into your organization. 