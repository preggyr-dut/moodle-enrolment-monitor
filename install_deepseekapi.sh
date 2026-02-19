#!/bin/bash
# install_deepseek_api.sh
echo "Installing DeepSeek API-based code assistance..."

# Install VS Code if needed
if ! command -v code &> /dev/null; then
    echo "Installing VS Code..."
    sudo snap install code --classic
fi

# Install DeepSeek extension
echo "Installing DeepSeek Coder extension..."
code --install-extension DeepSeek.deepseek-coder

# Cleanup
echo "Cleaning up cache..."
sudo apt clean
rm -rf ~/.cache/pip/*

echo "✅ Setup complete!"
echo "1. Open VS Code"
echo "2. Go to Extensions → DeepSeek Coder"
echo "3. Enter your API key from: https://platform.deepseek.com"
echo "4. Start coding with AI assistance!"