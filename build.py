# build.py (Temporary Diagnostic Script)
import os
import sys

print("--- STARTING CODECOMPASS DIAGNOSTIC SCRIPT ---")

# Command 1: Print the current working directory to know where we are.
print("\n--- [1] CURRENT WORKING DIRECTORY ---")
os.system("pwd")

# Command 2: List all files and folders with details to see everything.
print("\n--- [2] LISTING ALL FILES & FOLDERS ---")
os.system("ls -laR")

# Command 3: Find the top 30 largest files and directories.
# This will tell us what's taking up all the space.
print("\n--- [3] FINDING TOP 30 LARGEST ITEMS ---")
os.system("du -ah . | sort -rh | head -n 30")

print("\n--- DIAGNOSTIC SCRIPT COMPLETE ---")

# Intentionally fail the build so we can see the logs clearly.
sys.exit(1)