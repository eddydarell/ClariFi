#!/bin/bash

# ClariFi Tab Completion Setup Script
# Installs bash and zsh tab completion for ClariFi commands

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPLETION_DIR="$HOME/.local/share/bash-completion/completions"
ZSH_COMPLETION_DIR="$HOME/.local/share/zsh/site-functions"

echo "🚀 ClariFi Tab Completion Setup"
echo "==============================="

# Function to detect shell
detect_shell() {
    if [[ -n "$ZSH_VERSION" ]]; then
        echo "zsh"
    elif [[ -n "$BASH_VERSION" ]]; then
        echo "bash"
    else
        echo "unknown"
    fi
}

# Function to setup bash completion
setup_bash_completion() {
    echo "📝 Setting up Bash completion..."

    # Create completion directory if it doesn't exist
    mkdir -p "$COMPLETION_DIR"

    # Copy the bash completion file
    cp "$SCRIPT_DIR/_clarifi_completion.bash" "$COMPLETION_DIR/clarifi"
    cp "$SCRIPT_DIR/_clarifi_completion.bash" "$COMPLETION_DIR/run.sh"

    # Add to .bashrc if not already present
    if ! grep -q "clarifi completion" "$HOME/.bashrc" 2>/dev/null; then
        echo "" >> "$HOME/.bashrc"
        echo "# ClariFi completion" >> "$HOME/.bashrc"
        echo "source $COMPLETION_DIR/clarifi" >> "$HOME/.bashrc"
    fi

    echo "✅ Bash completion installed!"
    echo "   - Completion files: $COMPLETION_DIR/clarifi"
    echo "   - Added to ~/.bashrc"
}

# Function to setup zsh completion
setup_zsh_completion() {
    echo "📝 Setting up Zsh completion..."

    # Create completion directory if it doesn't exist
    mkdir -p "$ZSH_COMPLETION_DIR"

    # Copy the zsh completion file
    cp "$SCRIPT_DIR/_clarifi_completion.zsh" "$ZSH_COMPLETION_DIR/_clarifi"

    # Add to .zshrc if not already present
    if ! grep -q "clarifi completion" "$HOME/.zshrc" 2>/dev/null; then
        echo "" >> "$HOME/.zshrc"
        echo "# ClariFi completion" >> "$HOME/.zshrc"
        echo "fpath=($ZSH_COMPLETION_DIR \$fpath)" >> "$HOME/.zshrc"
        echo "autoload -U compinit && compinit" >> "$HOME/.zshrc"
    fi

    echo "✅ Zsh completion installed!"
    echo "   - Completion file: $ZSH_COMPLETION_DIR/_clarifi"
    echo "   - Added to ~/.zshrc"
}

# Function to setup for current shell
setup_current_shell() {
    local shell=$(detect_shell)

    case $shell in
        bash)
            setup_bash_completion
            echo ""
            echo "🔄 To activate completion in current session, run:"
            echo "   source $COMPLETION_DIR/clarifi"
            ;;
        zsh)
            setup_zsh_completion
            echo ""
            echo "🔄 To activate completion in current session, run:"
            echo "   source ~/.zshrc"
            ;;
        *)
            echo "⚠️  Unknown shell. Setting up both bash and zsh completions..."
            setup_bash_completion
            setup_zsh_completion
            ;;
    esac
}

# Function to setup for all shells
setup_all_shells() {
    echo "📦 Installing completions for all shells..."
    setup_bash_completion
    echo ""
    setup_zsh_completion
}

# Function to test completion
test_completion() {
    echo ""
    echo "🧪 Testing completion setup..."

    local shell=$(detect_shell)
    case $shell in
        bash)
            if [[ -f "$COMPLETION_DIR/clarifi" ]]; then
                echo "✅ Bash completion file exists"
                source "$COMPLETION_DIR/clarifi"
                echo "✅ Bash completion loaded successfully"
            else
                echo "❌ Bash completion file not found"
            fi
            ;;
        zsh)
            if [[ -f "$ZSH_COMPLETION_DIR/_clarifi" ]]; then
                echo "✅ Zsh completion file exists"
            else
                echo "❌ Zsh completion file not found"
            fi
            ;;
    esac
}

# Function to remove completion
remove_completion() {
    echo "🗑️  Removing ClariFi tab completion..."

    # Remove files
    rm -f "$COMPLETION_DIR/clarifi"
    rm -f "$COMPLETION_DIR/run.sh"
    rm -f "$ZSH_COMPLETION_DIR/_clarifi"

    # Remove from .bashrc
    if [[ -f "$HOME/.bashrc" ]]; then
        sed -i '/# ClariFi completion/,+1d' "$HOME/.bashrc" 2>/dev/null
    fi

    # Remove from .zshrc
    if [[ -f "$HOME/.zshrc" ]]; then
        sed -i '/# ClariFi completion/,+2d' "$HOME/.zshrc" 2>/dev/null
    fi

    echo "✅ ClariFi completion removed!"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  --install, -i    Install completion for current shell"
    echo "  --all, -a        Install completion for all shells"
    echo "  --test, -t       Test completion setup"
    echo "  --remove, -r     Remove completion"
    echo "  --help, -h       Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 --install     # Install for current shell"
    echo "  $0 --all         # Install for all shells"
    echo "  $0 --test        # Test current setup"
}

# Main execution
case "${1:-}" in
    --install|-i)
        setup_current_shell
        test_completion
        ;;
    --all|-a)
        setup_all_shells
        test_completion
        ;;
    --test|-t)
        test_completion
        ;;
    --remove|-r)
        remove_completion
        ;;
    --help|-h)
        show_usage
        ;;
    *)
        echo "🎯 ClariFi Tab Completion Setup"
        echo ""
        show_usage
        echo ""
        echo "💡 Quick start: $0 --install"
        ;;
esac

echo ""
echo "🎉 Setup complete! Available completions:"
echo "   - ./run.sh [TAB]         # Complete main commands"
echo "   - ./run.sh analyze [TAB] # Complete command options"
echo "   - python3 clarifi_engine/main.py [TAB] # Complete Python script"
echo ""
echo "📚 Example usage:"
echo "   ./run.sh ana[TAB] → ./run.sh analyze"
echo "   ./run.sh analyze --pe[TAB] → ./run.sh analyze --period"
echo "   ./run.sh screen [TAB] → gainers/losers/actives/new"
echo "   ./run.sh portfolio [TAB] → create/list/add/remove/etc."
