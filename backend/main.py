import sys
import os

# Ensure the project root is on sys.path so "server" package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server.main import app
