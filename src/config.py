"""
Scanner AI Configuration Module
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
TEMP_DIR = Path(os.getenv('SCAN_TEMP_DIR', './temp_repos'))
OUTPUT_DIR = Path(os.getenv('OUTPUT_DIR', './scan_results'))
REPOS_FILE = BASE_DIR / 'repos.txt'

# API Keys
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Scanner settings
SUPPORTED_LANGUAGES = ['python', 'php', 'javascript', 'java', 'ruby']
DRUPAL_PACKAGIST_API = 'https://packages.drupal.org/8/packages.json'

# Create necessary directories
TEMP_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
