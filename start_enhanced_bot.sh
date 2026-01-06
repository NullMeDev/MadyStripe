#!/bin/bash

# MadyStripe Enhanced Bot Startup Script

echo "=========================================="
echo "  MadyStripe Enhanced Bot v4.0"
echo "=========================================="
echo ""

# Check if old bot is running
OLD_PID=$(ps aux | grep "interfaces/telegram_bot.py" | grep -v grep | awk '{print $2}')

if [ ! -z "$OLD_PID" ]; then
    echo "⚠️  Old bot detected (PID: $OLD_PID)"
    read -p "Stop old bot and start enhanced version? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🛑 Stopping old bot..."
        kill $OLD_PID
        sleep 2
        echo "✅ Old bot stopped"
    else
        echo "❌ Cancelled. Please stop old bot manually:"
        echo "   kill $OLD_PID"
        exit 1
    fi
fi

echo ""
echo "🚀 Starting Enhanced Bot..."
echo ""
echo "Features:"
echo "  ✅ AUTH Gate (CC Foundation)"
echo "  ✅ CHARGE Gate (Pipeline)"
echo "  ✅ SHOPIFY Gate (HTTP)"
echo "  ✅ File Reply Support"
echo "  ✅ Mass Checking"
echo ""
echo "Commands:"
echo "  /auth - Quick validation"
echo "  /charge - Real charging"
echo "  /shopify - HTTP checking"
echo ""
echo "=========================================="
echo ""

# Start enhanced bot
cd /home/null/Desktop/MadyStripe
python3 interfaces/telegram_bot_enhanced.py
