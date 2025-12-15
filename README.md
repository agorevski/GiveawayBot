# 🎁 Discord Giveaway Bot

A feature-rich Discord bot for managing giveaways with two distinct modes: **Management Console** (admin commands) and **User Mode** (participant interactions).

## Features

### 🔧 Management Console Mode (Admin Commands)
- `/giveaway create` - Create new giveaways with customizable options
- `/giveaway end` - End a giveaway early and select winners
- `/giveaway cancel` - Cancel a giveaway without selecting winners
- `/giveaway reroll` - Reroll winners for ended giveaways
- `/giveaway list` - View all active giveaways
- `/giveaway config` - Configure admin roles for giveaway management

### 👤 User Mode
- `/giveaways` - View all active giveaways in the server
- `/myentries` - View your current giveaway entries
- **Button Entry** - Click to enter giveaways with a single button
- **Role Requirements** - Optional role restrictions for entry

### ✨ Additional Features
- **Scheduled Giveaways** - Schedule giveaways to start at a specific time
- **Multiple Winners** - Support for 1-20 winners per giveaway
- **Automatic Endings** - Background task auto-ends giveaways at scheduled time
- **Winner DMs** - Automatic notifications sent to winners
- **Persistent Views** - Button entries work even after bot restarts
- **SQLite Storage** - Lightweight, file-based database

## Installation

### Prerequisites
- Python 3.10 or higher
- Discord Bot Token ([Create one here](https://discord.com/developers/applications))

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/agorevski/GiveawayBot.git
   cd GiveawayBot
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   .\venv\Scripts\activate
   
   # Linux/macOS
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   
   # For development (includes testing tools)
   pip install -r requirements-dev.txt
   ```

4. **Configure environment variables**
   ```bash
   # Copy the example file
   cp .env.example .env
   
   # Edit .env with your bot token
   # DISCORD_BOT_TOKEN=your_token_here
   ```

5. **Run the bot**
   ```bash
   python -m src.bot
   ```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DISCORD_BOT_TOKEN` | Your Discord bot token | Yes |
| `DATABASE_PATH` | Path to SQLite database (default: `data/giveaway.db`) | No |
| `LOG_LEVEL` | Logging level (default: `INFO`) | No |

### Bot Permissions

The bot requires the following Discord permissions:
- **Send Messages** - Post giveaway embeds
- **Embed Links** - Display rich giveaway embeds
- **Read Message History** - Edit giveaway messages
- **Use External Emojis** - Display emoji reactions

Required **Intents**:
- **Server Members** - For validating winners are still in server
- **Guilds** - For basic server operations

## Usage

### Creating a Giveaway

```
/giveaway create prize:"Steam Game Key" duration:1d winners:2
```

**Options:**
- `prize` - Description of what's being given away (required)
- `duration` - How long the giveaway lasts (e.g., `1h`, `30m`, `1d`, `1w`)
- `winners` - Number of winners (default: 1, max: 20)
- `required_role` - Role required to enter (optional)
- `channel` - Channel to post in (default: current channel)

### Duration Format

| Format | Example | Description |
|--------|---------|-------------|
| Seconds | `30s`, `30 seconds` | 30 seconds |
| Minutes | `5m`, `5min`, `5 minutes` | 5 minutes |
| Hours | `2h`, `2hr`, `2 hours` | 2 hours |
| Days | `1d`, `1 day` | 1 day |
| Weeks | `1w`, `1 week` | 1 week |
| Combined | `1d 2h 30m` | 1 day, 2 hours, 30 minutes |

### Configuring Admin Roles

By default, only Discord administrators can manage giveaways. You can add additional roles:

```
/giveaway config action:Add admin role role:@Moderators
/giveaway config action:List admin roles
/giveaway config action:Remove admin role role:@Moderators
```

## Project Structure

```
GiveawayBot/
├── src/
│   ├── __init__.py
│   ├── bot.py              # Main bot entry point
│   ├── config.py           # Configuration management
│   ├── models/
│   │   ├── __init__.py
│   │   ├── giveaway.py     # Giveaway data model
│   │   └── guild_config.py # Guild configuration model
│   ├── services/
│   │   ├── __init__.py
│   │   ├── giveaway_service.py  # Giveaway business logic
│   │   ├── storage_service.py   # Database operations
│   │   └── winner_service.py    # Winner selection logic
│   ├── cogs/
│   │   ├── __init__.py
│   │   ├── admin.py        # Admin commands
│   │   ├── giveaway.py     # User commands
│   │   └── tasks.py        # Background tasks
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── buttons.py      # Discord buttons
│   │   └── embeds.py       # Embed builders
│   └── utils/
│       ├── __init__.py
│       ├── permissions.py  # Permission utilities
│       └── validators.py   # Input validation
├── tests/
│   ├── __init__.py
│   ├── conftest.py         # Pytest fixtures
│   ├── unit/
│   │   ├── test_giveaway_model.py
│   │   ├── test_giveaway_service.py
│   │   ├── test_permissions.py
│   │   └── test_validators.py
│   └── integration/
│       └── test_storage.py
├── .env.example
├── .gitignore
├── pytest.ini
├── requirements.txt
└── requirements-dev.txt
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run specific test file
pytest tests/unit/test_validators.py -v
```

## Development

### Code Style

This project follows PEP 8 guidelines. Linting is done with `flake8`:

```bash
flake8 src tests
```

### Type Checking

Type hints are used throughout. Check with `mypy`:

```bash
mypy src
```

### Adding New Features

1. Create models in `src/models/`
2. Add business logic to `src/services/`
3. Create Discord commands in `src/cogs/`
4. Add UI components in `src/ui/`
5. Write tests in `tests/`

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [discord.py](https://github.com/Rapptz/discord.py)
- Async SQLite with [aiosqlite](https://github.com/omnilib/aiosqlite)
