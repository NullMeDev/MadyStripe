#!/usr/bin/env python3
"""
Blackbox API Key Setup Script
Allows you to securely store your Blackbox API key for use in VSCode
"""

import os
import json
import getpass
from pathlib import Path

def setup_api_key():
    """Setup Blackbox API key for VSCode usage"""

    print("🔑 Blackbox API Key Setup for VSCode")
    print("=" * 50)

    # Check if key already exists
    config_file = Path.home() / ".blackbox" / "config.json"
    config_file.parent.mkdir(exist_ok=True)

    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                if 'api_key' in config and config['api_key']:
                    print("✅ API key already configured!")
                    print("   To update, run this script again.")
                    return
        except:
            pass

    print("\n📝 How to get your Blackbox API key:")
    print("   1. Go to https://www.blackbox.ai/")
    print("   2. Sign in to your account")
    print("   3. Go to Settings > API Keys")
    print("   4. Copy your API key")
    print()

    # Get API key from user
    while True:
        api_key = getpass.getpass("🔐 Enter your Blackbox API key: ").strip()

        if not api_key:
            print("❌ API key cannot be empty. Please try again.")
            continue

        if len(api_key) < 20:
            print("❌ API key seems too short. Please check and try again.")
            continue

        # Basic validation - should start with expected format
        if not api_key.startswith(('sk-', 'pk-', 'bb-')):
            print("⚠️  Warning: API key doesn't start with expected prefix (sk-, pk-, bb-)")
            confirm = input("   Continue anyway? (y/N): ").lower().strip()
            if confirm != 'y':
                continue

        break

    # Save to config file
    config = {
        'api_key': api_key,
        'created_at': str(Path.home()),
        'vscode_integration': True
    }

    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

        # Set file permissions to be readable only by owner
        config_file.chmod(0o600)

        print("✅ API key saved successfully!"        print(f"   Location: {config_file}")

    except Exception as e:
        print(f"❌ Failed to save API key: {e}")
        return

    print("\n🔧 VSCode Integration Setup:")
    print("   1. Open VSCode")
    print("   2. Install the 'Blackbox AI' extension")
    print("   3. The extension should automatically detect your API key")
    print("   4. If not, you can manually configure it in extension settings")
    print()

    print("📚 Usage in VSCode:")
    print("   - Use Ctrl+Shift+P (Cmd+Shift+P on Mac)")
    print("   - Type 'Blackbox' to see available commands")
    print("   - Your API key is now ready to use!")
    print()

    print("🔒 Security Notes:")
    print("   - Your API key is stored securely in your home directory")
    print("   - File permissions are set to owner-only access")
    print("   - Never share your API key or commit it to version control")
    print()

def show_current_config():
    """Show current configuration"""
    config_file = Path.home() / ".blackbox" / "config.json"

    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)

            print("📋 Current Configuration:")
            print(f"   Config file: {config_file}")
            print(f"   API key configured: {'Yes' if config.get('api_key') else 'No'}")
            print(f"   VSCode integration: {config.get('vscode_integration', False)}")
            print(f"   Created: {config.get('created_at', 'Unknown')}")

            if config.get('api_key'):
                masked_key = config['api_key'][:8] + "..." + config['api_key'][-4:]
                print(f"   API key (masked): {masked_key}")

        except Exception as e:
            print(f"❌ Error reading config: {e}")
    else:
        print("❌ No configuration found. Run setup first.")

def reset_config():
    """Reset/remove configuration"""
    config_file = Path.home() / ".blackbox" / "config.json"

    if config_file.exists():
        try:
            config_file.unlink()
            print("✅ Configuration reset successfully!")
        except Exception as e:
            print(f"❌ Failed to reset config: {e}")
    else:
        print("❌ No configuration found to reset.")

def main():
    """Main menu"""
    while True:
        print("\n🔑 Blackbox API Key Manager")
        print("=" * 30)
        print("1. Setup API Key")
        print("2. Show Current Config")
        print("3. Reset Configuration")
        print("4. Exit")

        choice = input("\nChoose an option (1-4): ").strip()

        if choice == '1':
            setup_api_key()
        elif choice == '2':
            show_current_config()
        elif choice == '3':
            confirm = input("Are you sure you want to reset? (y/N): ").lower().strip()
            if confirm == 'y':
                reset_config()
        elif choice == '4':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
