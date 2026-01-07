<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/python-3.8+-green.svg" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-yellow.svg" alt="License">
  <img src="https://img.shields.io/badge/build-passing-brightgreen.svg" alt="Build">
  <img src="https://img.shields.io/badge/security-audited-purple.svg" alt="Security">
</p>

<h1 align="center">🔐 MadyStripe</h1>

<p align="center">
  <strong>Advanced Payment Gateway Integration Framework</strong>
</p>

<p align="center">
  A powerful, modular payment processing toolkit with multi-gateway support including Stripe, Shopify, Braintree, and more.
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#documentation">Documentation</a> •
  <a href="#contributing">Contributing</a>
</p>

---

## 📋 Table of Contents

- [Features](#-features)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [Gateways](#-gateways)
- [Telegram Bot](#-telegram-bot)
- [API Reference](#-api-reference)
- [Documentation](#-documentation)
- [Security](#-security)
- [Contributing](#-contributing)
- [License](#-license)
- [Contact](#-contact)

---

## ✨ Features

### Core Features
- **Multi-Gateway Support** - Stripe, Shopify, Braintree, Square, and more
- **Telegram Bot Integration** - Full-featured bot for remote management
- **Async Processing** - High-performance asynchronous card processing
- **Smart Store Cycling** - Automatic rotation through 200+ pre-validated stores
- **Proxy Support** - Built-in proxy rotation and management
- **Error Detection** - Advanced error parsing and categorization

### Gateway Support
| Gateway | Status | Description |
|---------|--------|-------------|
| Stripe | ✅ Active | Direct Stripe API integration |
| Shopify | ✅ Active | Products.json API flow |
| Braintree | ✅ Active | PayPal/Braintree processing |
| Square | ✅ Active | Square payment processing |
| Pipeline | ✅ Active | Multi-stage verification |

### Security Features
- 🔒 Secure credential management
- 🛡️ Rate limiting and anti-detection
- 🔐 Encrypted configuration storage
- 📝 Comprehensive audit logging

---

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Virtual environment (recommended)

### Quick Install

```bash
# Clone the repository
git clone https://github.com/NullMeDev/MadyStripe.git
cd MadyStripe

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Configure your credentials
nano .env  # or use your preferred editor
```

### Dependencies

```bash
pip install aiohttp asyncio requests pyTelegramBotAPI selenium
```

---

## 🚀 Quick Start

### 1. Configure Credentials

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your actual values:
```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_GROUP_ID=your_group_id
```

### 2. Run the Telegram Bot

```bash
python3 interfaces/telegram_bot_enhanced.py
```

### 3. Use the CLI

```bash
python3 madystripe.py --help
```

### 4. Check a Card

```python
from src.core.gateways import get_gateway_manager

gm = get_gateway_manager()
status, message, card_type = gm.check_card("4242424242424242|12|25|123", gateway_id=1)
print(f"Status: {status}, Message: {message}")
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELEGRAM_BOT_TOKEN` | Telegram bot API token | Yes |
| `TELEGRAM_GROUP_ID` | Target group/channel ID | Yes |
| `BLACKBOX_API_KEY` | Blackbox API key | Optional |
| `PROXY_HOST` | Proxy server host | Optional |
| `PROXY_PORT` | Proxy server port | Optional |

### Configuration Files

```
MadyStripe/
├── .env                    # Environment variables (not tracked)
├── .env.example            # Environment template
├── .secrets.local.json     # Local secrets (not tracked)
└── config/
    └── config.example.json # Configuration template
```

---

## 🔌 Gateways

### Available Gateways

```python
from src.core.gateways import get_gateway_manager

gm = get_gateway_manager()
gateways = gm.list_gateways()

for gw in gateways:
    print(f"[{gw['id']}] {gw['name']} - {gw['description']}")
```

### Gateway List

| ID | Name | Type | Status |
|----|------|------|--------|
| 1 | Stripe Direct | Payment | Active |
| 2 | Stripe Checkout | Payment | Active |
| 3 | Braintree | Payment | Active |
| 4 | Square | Payment | Active |
| 5 | Pipeline | Multi-stage | Active |
| 6 | CC Foundation | Validation | Active |
| 7 | Shopify Simple | E-commerce | Active |
| 8 | Shopify Dynamic | E-commerce | Active |
| 9 | Shopify API | E-commerce | Active |

---

## 🤖 Telegram Bot

### Commands

| Command | Description |
|---------|-------------|
| `/start` | Initialize the bot |
| `/help` | Show help message |
| `/chk <card>` | Check a single card |
| `/mass` | Mass check cards (reply to file) |
| `/gates` | List available gateways |
| `/setgate <id>` | Set active gateway |
| `/stats` | Show statistics |

### Usage Example

```
/chk 4242424242424242|12|25|123
```

---

## 📚 Documentation

Detailed documentation is available in the `docs/` folder:

- [Quick Start Guide](docs/QUICK_START.md)
- [Gateway Configuration](docs/GATEWAY_CONFIGURATION.md)
- [Shopify Integration](docs/SHOPIFY_INTEGRATION_GUIDE.md)
- [API Reference](docs/API_REFERENCE.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

---

## 🔒 Security

### Reporting Vulnerabilities

If you discover a security vulnerability, please send an email to security@example.com. All security vulnerabilities will be promptly addressed.

### Security Best Practices

1. **Never commit credentials** - Use `.env` files and `.gitignore`
2. **Rotate API keys regularly** - Update credentials periodically
3. **Use proxies** - Protect your IP address
4. **Enable logging** - Monitor for suspicious activity

See [SECURITY.md](SECURITY.md) for more details.

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/MadyStripe.git

# Create a feature branch
git checkout -b feature/your-feature-name

# Make your changes and commit
git commit -m "Add your feature"

# Push and create a pull request
git push origin feature/your-feature-name
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📞 Contact

- **Author**: NullMe
- **Telegram**: [@MissNullMe](https://t.me/MissNullMe)
- **GitHub**: [NullMeDev](https://github.com/NullMeDev)

---

## ⭐ Star History

If you find this project useful, please consider giving it a star! ⭐

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/NullMeDev">NullMe</a>
</p>
