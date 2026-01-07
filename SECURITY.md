# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability within MadyStripe, please follow these steps:

### 1. Do NOT Create a Public Issue

Please do not report security vulnerabilities through public GitHub issues.

### 2. Contact Us Privately

Send a detailed report to:
- **Telegram**: [@MissNullMe](https://t.me/MissNullMe)
- **GitHub**: Create a private security advisory

### 3. Include the Following Information

- Type of vulnerability
- Full paths of source file(s) related to the vulnerability
- Location of the affected source code (tag/branch/commit or direct URL)
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

### 4. Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Resolution**: Depends on complexity, typically within 30 days

## Security Best Practices

### For Users

1. **Never Commit Credentials**
   ```bash
   # Always use .gitignore
   .env
   .secrets.local.json
   secrets.json
   mady_config.json
   ```

2. **Use Environment Variables**
   ```bash
   export TELEGRAM_BOT_TOKEN="your_token"
   export BLACKBOX_API_KEY="your_key"
   ```

3. **Rotate API Keys Regularly**
   - Change bot tokens every 30-90 days
   - Revoke compromised keys immediately

4. **Use Proxies**
   - Protect your IP address
   - Use rotating proxy services
   - Never use free public proxies

5. **Enable Logging**
   - Monitor for suspicious activity
   - Review logs regularly
   - Set up alerts for anomalies

### For Developers

1. **Code Review**
   - All PRs require security review
   - No hardcoded credentials
   - Input validation on all user inputs

2. **Dependencies**
   - Keep dependencies updated
   - Run `pip audit` regularly
   - Use `pip-compile` for reproducible builds

3. **Testing**
   - Include security tests
   - Test for injection vulnerabilities
   - Validate error handling

## Security Features

### Implemented

- ✅ Secure credential storage (`.secrets.local.json`)
- ✅ Environment variable support
- ✅ Comprehensive `.gitignore`
- ✅ Rate limiting
- ✅ Proxy support
- ✅ Error message sanitization

### Planned

- 🔄 Encrypted configuration files
- 🔄 Two-factor authentication for bot
- 🔄 Audit logging
- 🔄 IP whitelisting

## Secure Configuration

### Example Secure Setup

```bash
# 1. Clone repository
git clone https://github.com/NullMeDev/MadyStripe.git
cd MadyStripe

# 2. Create secure credentials file
cat > .secrets.local.json << 'EOF'
{
  "telegram_bot_token": "YOUR_TOKEN",
  "telegram_group_id": "YOUR_GROUP_ID"
}
EOF

# 3. Set restrictive permissions
chmod 600 .secrets.local.json

# 4. Verify .gitignore
grep ".secrets.local.json" .gitignore
```

### File Permissions

```bash
# Recommended permissions
chmod 600 .secrets.local.json  # Owner read/write only
chmod 600 .env                  # Owner read/write only
chmod 644 .env.example          # World readable (template)
```

## Vulnerability Disclosure

We follow responsible disclosure practices:

1. **Private Disclosure**: Report vulnerabilities privately
2. **Coordinated Fix**: Work together on a fix
3. **Public Disclosure**: After fix is released (typically 90 days)
4. **Credit**: Researchers credited in CHANGELOG

## Security Audit

Last security audit: **January 2025**

### Audit Scope
- Credential handling
- Input validation
- API security
- Dependency vulnerabilities

### Findings
- All critical issues resolved
- See `docs/SECURITY_AUDIT.md` for details

## Contact

- **Security Issues**: [@MissNullMe](https://t.me/MissNullMe)
- **General Questions**: GitHub Issues

---

Thank you for helping keep MadyStripe secure! 🔒
