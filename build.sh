#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "--- Starting Custom Build Script ---"

# 1. Install all dependencies from requirements.txt
echo "--- Installing dependencies ---"
pip install -r requirements.txt

# 2. Run our Python build script to compile the .so library
echo "--- Building tree-sitter library ---"
python build.py

# 3. THE CRITICAL FIX: Clean up the large parser source directories
#    that tree-sitter-languages leaves behind.
echo "--- Cleaning up build-time bloat ---"
# This command finds all directories named 'tree-sitter-*' within the installed packages
# and deletes them to reduce the final function size.
find . -type d -name "tree-sitter-*" -exec rm -rf {} +

echo "--- Custom Build Script Finished ---"