This is Todo App built by ME usinf python HTML and CSS
# URL Payment Gateway Analysis Bot

A Telegram bot that analyzes URLs to detect payment gateways, security measures, and other payment-related features. Features MongoDB integration for scalable data storage, an elegant inline button interface, and rich media responses.

## Features

- **URL Analysis**
  - Analyze single URLs or multiple URLs from text files
  - Detect payment gateways like PayPal, Stripe, etc.
  - Check for captcha protection and Cloudflare protection
  - Identify 3D secure authentication
  - Detect OTP (One-Time Password) requirements
  - Real-time progress updates during analysis

- **Security Analysis**
  - SSL/TLS verification
  - HSTS implementation checking
  - XSS protection detection
  - Content Security Policy analysis
  - Frame protection verification
  - Secure cookie checking
  - Security header scanning

- **Threat Detection**
  - Phishing detection
  - Malware indicators
  - Suspicious redirects
  - Insecure forms identification
  - Browser fingerprinting detection
  - Data leakage risk assessment

- **User Management**
  - User registration and subscription system
  - Multiple subscription tiers with different durations
  - Admin broadcasting capabilities
  - User activity tracking
  - Group approval system for shared access

- **Data Storage**
  - MongoDB database integration with file fallback
  - Efficient caching with TTL expiration
  - Automatic data migration from files to MongoDB
  - Database maintenance and statistics
  - Robust file storage fallback with directory structure support

- **User Interface**
  - Rich media responses with formatted results
  - Modern inline button interface
  - Interactive expandable sections
  - Progress indicators with stage tracking
  - Emoji icons for better visual representation
  - Color-coded status indicators

- **Performance**
  - Asynchronous processing with threading
  - Optimized database queries with indexes
  - Memory management and resource optimization
  - Connection pooling for HTTP and MongoDB
  - Performance metrics tracking

## Setup

1. Clone this repository
2. Install requirements:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your configuration:
   ```
   # MongoDB Configuration
   MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/url_gateway_bot
   DB_NAME=url_gateway_bot

   # File Storage Configuration
   USE_FILE_STORAGE=false
   REGISTERED_USERS_FILE=data/registered_users.json
   SUBSCRIPTIONS_FILE=data/subscriptions.json
   CACHE_FILE=data/url_cache.json

   # Bot Configuration
   ADMIN_IDS=1234567890,9876543210
   SUPER_ADMIN_IDS=1234567890

   # Telegram Bot Settings
   API_TOKEN=your_bot_token_here

   # App Settings
   MAX_WORKERS=5

   # Other Settings
   LOG_LEVEL=INFO
   ```
4. Run the bot:
   ```
   python main.py
   ```

## User Commands

- `/start` - Start the bot with interactive inline menu
- `/register` - Register to use the bot
- `/check_subscription` - Check your subscription status
- `/myid` - Get your Telegram ID
- `.url <URL>` - Analyze a single URL
- `.murl <multiple URLs>` - Analyze multiple URLs (one per line)
- `/help` - Show help information
- `/stats` - View bot statistics

## Admin Commands

- `/broadcast <message>` - Send a message to all registered users
- `/adduser <user_id> <duration> <unit>` - Add a user with subscription (unit can be 'd', 'w', or 'm')
- `/approve <group_id>` - Approve a group to use the bot without individual subscriptions
- `/reset_stats` - Reset performance statistics
- `/dbstats` - View MongoDB database statistics
- `/dbmaintenance` - Perform database maintenance tasks

## Group Access System

The bot now supports a group approval system that allows all members of approved groups to use premium features:

- **For Group Admins**: Add the bot to your group and use the bot in the group
- **For Bot Admins**: Use `/approve <group_id>` to allow all members of a group to use the bot
- **For Users**: Members of approved groups can use all bot features without individual subscriptions
- **Technical Details**: The system checks both individual user subscriptions and group membership

## Interaction Methods

The bot features an elegant inline button interface for better user experience:

- **Start Menu**: Register, analyze URLs, view stats, and access help
- **Subscription Options**: Choose between day, week, or month subscriptions
- **Analysis Results**: View detailed information with expandable sections
  - 🔒 Security Details
  - 💳 Payment Gateways
  - ⚠️ Threat Analysis
  - ⚙️ Technical Details
- **Progress Tracking**: Real-time updates during URL analysis

## Modular Architecture

The bot is organized into modular components for better maintainability:

- `main.py` - Main bot code and entry point
- `database.py` - MongoDB integration and data operations
- `callbacks.py` - Callback handlers for inline buttons
- `utils.py` - Utility functions and helpers
- `config.py` - Configuration settings
- `mongo_helper.py` - Helper script for MongoDB connection management
- `test_mongo_connection.py` - Script to test MongoDB connectivity
- `user_management.py` - User management functions

## Database Integration

The bot uses MongoDB for data storage with automatic fallback to JSON files:

- **Users Collection**: Stores registered users with registration date and activity tracking
- **Subscriptions Collection**: Manages user subscription data with expiration dates
- **URL Analysis Collection**: Caches URL analysis results with TTL expiration
- **Metrics Collection**: Tracks performance metrics and usage statistics
- **Approved Groups Collection**: Stores group IDs approved for unrestricted access

### File Storage Fallback

The bot seamlessly falls back to file-based storage when MongoDB is unavailable:

- **Directory Structure**: Files are organized in a `data/` directory by default
- **Environment Control**: Use `USE_FILE_STORAGE=true` to force file storage mode
- **Automatic Fallback**: If MongoDB connection fails, the bot automatically uses file storage
- **Data Consistency**: Data is maintained consistently across storage modes
- **Migration Support**: Data can be migrated between storage systems

## Rich Result Display

Analysis results are presented in a user-friendly format:

- **Summary View**: Overview of key findings with emoji icons
- **Detailed Views**: Expandable sections for in-depth information
- **Visual Indicators**: Color-coded status markers (✅/❌)
- **Progress Updates**: Real-time progress bar during analysis
- **Formatted Text**: Markdown formatting for improved readability
- **Interactive Elements**: Buttons for navigation and actions

## Performance Optimizations

The bot includes several performance enhancements:

- **Asynchronous Processing**: Non-blocking operations using threading
- **Connection Pooling**: Efficient resource management for HTTP and MongoDB
- **Query Optimization**: Indexed collections for faster database operations
- **Tiered Caching**: Efficient data retrieval with TTL expiration
- **Memory Management**: Resource monitoring and optimization
- **Error Boundaries**: Comprehensive exception handling with fallbacks

## MongoDB vs File Storage

The bot automatically tries to use MongoDB for data storage with the following benefits:
- **Scalability**: Handles large numbers of users and data
- **Query Performance**: Faster data retrieval with indexes
- **Data Integrity**: ACID transactions for reliable operations
- **TTL Collections**: Automatic cleanup of expired data
- **Fallback System**: Falls back to JSON files when MongoDB is unavailable

## Troubleshooting

### MongoDB Connection Issues
- Ensure your MongoDB Atlas connection string is correct in the `.env` file
- Check that your IP address is whitelisted in MongoDB Atlas
- Make sure DNS resolution is working correctly for SRV records
- Install `dnspython` package with `pip install dnspython`
- Set `USE_FILE_STORAGE=true` if you prefer to use file storage only

### Group Approval Issues
- Make sure you're using the correct group ID (use `/myid` in a group)
- Ensure the bot has been added to the group
- Group IDs typically start with `-100` for supergroups
- Only super admins can approve groups

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
