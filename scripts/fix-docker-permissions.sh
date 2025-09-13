#!/bin/bash

# Fix Docker Permissions Script
# Run this once to fix Docker permissions permanently

echo "🔧 Fixing Docker Permissions"
echo "============================"

# Add user to docker group
sudo usermod -aG docker $USER

# Fix socket permissions temporarily
sudo chmod 666 /var/run/docker.sock

echo "✅ Docker permissions fixed!"
echo ""
echo "⚠️  IMPORTANT: You need to log out and log back in for the group changes to take effect."
echo "   Or restart your computer."
echo ""
echo "🔄 Alternative: Start a new terminal session and try again."
echo ""
echo "🌐 For web deployment without Docker issues, use:"
echo "   ./scripts/start-codeclinic-web.sh"
