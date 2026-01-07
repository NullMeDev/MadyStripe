# Changelog

All notable changes to MadyStripe will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-15

### Added
- **Multi-Gateway Support**
  - Stripe Direct API integration
  - Shopify Products.json API flow with 204 pre-validated stores
  - Braintree payment processing
  - Square payment integration
  - Pipeline multi-stage verification
  - CC Foundation validation gateway

- **Telegram Bot**
  - Full-featured Telegram bot interface
  - Commands: `/chk`, `/mass`, `/gates`, `/setgate`, `/stats`
  - File upload support for mass checking
  - Real-time status updates

- **Shopify API Gateway**
  - Pre-validated store database (204 stores)
  - Automatic store cycling
  - Variant ID pre-fetching
  - Cart API integration

- **Security Features**
  - Secure credential management with `.secrets.local.json`
  - Environment variable support
  - Comprehensive `.gitignore`
  - Proxy support and rotation

- **Documentation**
  - Professional README with badges
  - Quick start guide
  - API reference
  - Gateway configuration guide

### Changed
- Reorganized project structure for better maintainability
- Moved all documentation to `docs/` folder
- Improved error handling and detection
- Enhanced logging system

### Security
- Removed hardcoded credentials
- Added `.env.example` template
- Implemented secure secrets management
- Added security audit documentation

## [0.9.0] - 2025-01-10

### Added
- Initial Shopify integration
- Basic Stripe gateway
- Telegram bot foundation

### Changed
- Refactored gateway architecture
- Improved async processing

## [0.8.0] - 2025-01-05

### Added
- Core checker module
- Gateway manager system
- CLI interface

### Fixed
- Various bug fixes and improvements

---

## Version History Summary

| Version | Date | Highlights |
|---------|------|------------|
| 1.0.0 | 2025-01-15 | Full release with multi-gateway support |
| 0.9.0 | 2025-01-10 | Shopify integration |
| 0.8.0 | 2025-01-05 | Core architecture |

---

## Upgrade Guide

### From 0.9.x to 1.0.0

1. **Update configuration files**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

2. **Move secrets to local file**
   ```bash
   # Create .secrets.local.json with your actual credentials
   # This file is gitignored
   ```

3. **Update imports**
   ```python
   # Old
   from core.gateways import GatewayManager
   
   # New
   from src.core.gateways import get_gateway_manager
   ```

---

## Deprecation Notices

### Deprecated in 1.0.0
- `secrets.json` - Use `.secrets.local.json` instead
- `mady_config.json` - Use `.env` file instead
- Old gateway files in root directory - Use `src/core/` modules

---

[1.0.0]: https://github.com/NullMeDev/MadyStripe/releases/tag/v1.0.0
[0.9.0]: https://github.com/NullMeDev/MadyStripe/releases/tag/v0.9.0
[0.8.0]: https://github.com/NullMeDev/MadyStripe/releases/tag/v0.8.0
