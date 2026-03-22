#!/bin/sh
# scripts/install-hooks.sh
# Run this once after cloning the repository to set up the pre-commit hook.

echo "Installing git hooks..."

cp scripts/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

echo "✅ Git hooks installed successfully."
