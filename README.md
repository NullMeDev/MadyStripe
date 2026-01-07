# MadyStripe

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/NullMeDev/MadyStripe)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/NullMeDev/MadyStripe/actions)
[![Code Quality](https://img.shields.io/badge/code%20quality-A+-brightgreen.svg)](https://github.com/NullMeDev/MadyStripe)

> Advanced Payment Gateway Integration System with Stripe & Shopify Support

MadyStripe is a comprehensive payment processing solution that integrates multiple gateway providers including Stripe, Shopify, Braintree, and Square. Built with enterprise-grade reliability and extensive testing coverage.

## ✨ Features

### 🚀 Core Capabilities
- **Multi-Gateway Support**: Stripe, Shopify, Braintree, Square, PayPal
- **Advanced Proxy Management**: Built-in proxy rotation and validation
- **Real-time Monitoring**: Live status tracking and performance metrics
- **Auto-Recovery**: Intelligent retry mechanisms and fallback systems
- **Rate Limiting**: Built-in protection against API throttling
- **Comprehensive Logging**: Detailed transaction logs and error tracking

### 🔧 Technical Features
- **Async Architecture**: High-performance asynchronous processing
- **Modular Design**: Clean separation of concerns with extensible architecture
- **Database Integration**: SQLite with migration support
- **RESTful API**: Clean API endpoints for external integrations
- **CLI Interface**: Command-line tools for administration
- **Telegram Bot**: User-friendly bot interface for management

### 🛡️ Security & Reliability
- **Encrypted Storage**: Secure credential management
- **Input Validation**: Comprehensive data sanitization
- **Error Handling**: Graceful failure recovery
- **Rate Limiting**: DDoS protection and abuse prevention
- **Audit Trails**: Complete transaction history

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Git

### Quick Start
```bash
# Clone the repository
git clone https://github.com/NullMeDev/MadyStripe.git
cd MadyStripe

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp config.example.json config.json
# Edit config.json with your settings

# Run setup
python setup.py

# Start the system
python main.py
```

### Docker Deployment
```bash
# Build and run with Docker
docker build -t madystripe .
docker run -p 8000:8000 madystripe
```

## 🚀 Usage

### Basic Usage
```python
from madystripe import PaymentProcessor

# Initialize processor
processor = PaymentProcessor()

# Process a payment
result = await processor.process_payment({
    'card': '4111111111111111|12|2025|123',
    'amount': '10.00',
    'gateway': 'stripe'
})

print(f"Payment Status: {result['status']}")
```

### Telegram Bot
```bash
# Start the bot
python interfaces/telegram_bot.py

# Available commands:
/start - Initialize bot
/addsh <url> - Add Shopify store
/shopify - List stores
/check <card> - Check card validity
/status - System status
```

### CLI Interface
```bash
# Check card
python interfaces/cli.py check "4111111111111111|12|2025|123"

# Add proxy
python interfaces/cli.py proxy add "ip:port:user:pass"

# View logs
python interfaces/cli.py logs --tail 50
```

## 📁 Project Structure

```
MadyStripe/
├── src/                          # Source code
│   ├── core/                     # Core business logic
│   │   ├── checker.py           # Card validation engine
│   │   ├── gateways.py          # Gateway management
│   │   └── __init__.py
│   ├── gateways/                # Payment gateways
│   │   ├── stripe.py            # Stripe integration
│   │   ├── shopify.py           # Shopify integration
│   │   ├── braintree.py         # Braintree integration
│   │   └── square.py            # Square integration
│   ├── commands/                # Bot commands
│   │   ├── shopify.py           # Shopify commands
│   │   ├── admin.py             # Admin commands
│   │   └── start.py             # Start command
│   ├── interfaces/              # User interfaces
│   │   ├── telegram_bot.py      # Telegram bot
│   │   ├── cli.py               # Command line interface
│   │   └── web.py               # Web interface
│   └── utils/                   # Utilities
│       ├── proxy_manager.py     # Proxy management
│       ├── logger.py            # Logging utilities
│       └── helpers.py           # Helper functions
├── tests/                       # Test suites
│   ├── integration/             # Integration tests
│   ├── unit/                    # Unit tests
│   └── functional/              # Functional tests
├── config/                      # Configuration files
├── docs/                        # Documentation
│   ├── guides/                  # User guides
│   ├── reports/                 # Test reports
│   └── development/             # Development docs
├── examples/                    # Usage examples
├── requirements.txt             # Python dependencies
├── setup.py                     # Setup script
├── Dockerfile                   # Docker configuration
└── README.md                    # This file
```

## 🔧 Configuration

### Environment Variables
```bash
# Database
export DATABASE_URL="sqlite:///madystripe.db"

# Telegram Bot
export TELEGRAM_TOKEN="your_bot_token"

# Stripe
export STRIPE_PUBLISHABLE_KEY="pk_live_..."
export STRIPE_SECRET_KEY="sk_live_..."

# Shopify
export SHOPIFY_API_KEY="your_api_key"
export SHOPIFY_API_SECRET="your_api_secret"

# Proxy Settings
export PROXY_LIST="proxies.txt"
export PROXY_ROTATION="true"
```

### Configuration File
```json
{
  "database": {
    "url": "sqlite:///madystripe.db",
    "migrate": true
  },
  "gateways": {
    "stripe": {
      "enabled": true,
      "api_key": "sk_live_...",
      "webhook_secret": "whsec_..."
    },
    "shopify": {
      "enabled": true,
      "api_key": "your_api_key",
      "api_secret": "your_api_secret"
    }
  },
  "telegram": {
    "token": "your_bot_token",
    "admin_ids": [123456789]
  },
  "proxy": {
    "enabled": true,
    "list_file": "proxies.txt",
    "rotation_interval": 300
  }
}
```

## 🧪 Testing

### Run Test Suite
```bash
# Run all tests
python -m pytest

# Run specific test categories
python -m pytest tests/unit/
python -m pytest tests/integration/
python -m pytest tests/functional/

# Run with coverage
python -m pytest --cov=src --cov-report=html
```

### Integration Testing
```bash
# Test gateway integrations
python tests/integration/test_gateways.py

# Test bot commands
python tests/integration/test_bot_commands.py

# Test CLI interface
python tests/integration/test_cli.py
```

## 📊 Monitoring & Analytics

### Health Checks
```bash
# System health
curl http://localhost:8000/health

# Gateway status
curl http://localhost:8000/status/gateways

# Performance metrics
curl http://localhost:8000/metrics
```

### Logging
```bash
# View application logs
tail -f logs/application.log

# View payment logs
tail -f logs/payments.log

# Search logs
grep "ERROR" logs/*.log
```

## 🔒 Security

### Best Practices
- Never commit sensitive data to version control
- Use environment variables for secrets
- Regularly rotate API keys
- Enable 2FA on all accounts
- Monitor for suspicious activity

### Security Features
- **Input Sanitization**: All user inputs are validated and sanitized
- **Rate Limiting**: Prevents abuse and DDoS attacks
- **Encryption**: Sensitive data is encrypted at rest
- **Audit Logging**: All actions are logged for compliance
- **Access Control**: Role-based access control system

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](docs/development/CONTRIBUTING.md) for details.

### Development Setup
```bash
# Fork and clone
git clone https://github.com/yourusername/MadyStripe.git
cd MadyStripe

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest

# Start development server
python main.py --debug
```

### Code Standards
- Follow PEP 8 style guidelines
- Write comprehensive tests
- Update documentation
- Use type hints
- Keep commits atomic

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Thanks to all contributors
- Special thanks to the payment gateway providers
- Community support and feedback

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/NullMeDev/MadyStripe/issues)
- **Discussions**: [GitHub Discussions](https://github.com/NullMeDev/MadyStripe/discussions)
- **Email**: support@madystripe.dev

---

**Made with ❤️ by the MadyStripe Team**

[![GitHub Stars](https://img.shields.io/github/stars/NullMeDev/MadyStripe.svg)](https://github.com/NullMeDev/MadyStripe/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/NullMeDev/MadyStripe.svg)](https://github.com/NullMeDev/MadyStripe/network)
[![GitHub Issues](https://img.shields.io/github/issues/NullMeDev/MadyStripe.svg)](https://github.com/NullMeDev/MadyStripe/issues)
