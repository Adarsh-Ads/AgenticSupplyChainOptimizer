import sys
import os

# Append current directory to path to ensure clean internal imports inside src/
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import and execute your main dashboard logic
from src.dashboard import *