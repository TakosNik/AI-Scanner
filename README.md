# Scanner AI

An AI-powered security scanner that analyzes repositories for vulnerabilities and checks Drupal projects for outdated contrib modules.

## Features

- 🔍 **Vulnerability Scanning**: Scans repositories for security vulnerabilities
  - Python dependency vulnerability detection (using Safety)
  - Python code security analysis (using Bandit)
  - Common security misconfiguration detection

- 🔷 **Drupal Module Analysis**: Specifically for Drupal projects
  - Detects Drupal projects via `composer.json`
  - Identifies outdated contrib modules
  - Compares current versions with latest available versions
  - Categorizes updates by severity (major/minor/patch)

- 🤖 **AI-Powered Analysis**: Optional AI integration
  - Summarizes critical security issues
  - Provides prioritized recommendations
  - Offers risk assessment
  - Supports OpenAI and Anthropic Claude

- 📊 **Comprehensive Reporting**: Detailed JSON reports
  - Individual repository reports
  - Summary reports across all scanned repos
  - Console output with key findings

## Installation

1. Clone this repository:
```bash
git clone <your-repo-url>
cd "Scanner AI"
```

2. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

## Configuration

### Environment Variables

Edit the `.env` file:

```env
# AI API Configuration - Local Model
OPENAI_API_KEY=not-needed-for-local
OPENAI_BASE_URL=http://10.195.159.207:1234/v1
OPENAI_MODEL=gpt-oss-20b

# For cloud OpenAI (alternative)
# OPENAI_API_KEY=your_openai_api_key_here
# OPENAI_MODEL=gpt-4

# For Anthropic Claude (alternative)
# ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Scanner Configuration
SCAN_TEMP_DIR=./temp_repos
OUTPUT_DIR=./scan_results
LOG_LEVEL=INFO
```

**Note**: The project is pre-configured to use your local `gpt-oss-20b` model at `http://10.195.159.207:1234`. No API key is needed for local models.

### Repository List

Add repository URLs to `repos.txt` (one per line):

```
https://github.com/username/repo1.git
https://github.com/username/drupal-project.git
https://github.com/username/another-repo.git
```

## Usage

### Basic Scan

```bash
python src/scanner_agent.py
```

### Advanced Options

```bash
# Disable AI analysis
python src/scanner_agent.py --no-ai

# Keep cloned repositories (don't cleanup)
python src/scanner_agent.py --no-cleanup

# Use Anthropic Claude instead of local model
python src/scanner_agent.py --ai-provider anthropic

# Use a different model or endpoint
python src/scanner_agent.py --ai-model gpt-4 --ai-base-url http://localhost:8000/v1
```

## Output

Results are saved to the `scan_results/` directory:

- **Individual reports**: `{repo_name}_{timestamp}.json` - Detailed scan results for each repository
- **Summary report**: `summary_report_{timestamp}.json` - Aggregated results from all scans

### Example Output Structure

```json
{
  "repo_url": "https://github.com/username/project.git",
  "repo_name": "project",
  "scan_time": "2025-12-23T10:30:00",
  "status": "completed",
  "vulnerability_scan": {
    "python_dependencies": [...],
    "bandit_issues": [...],
    "common_issues": [...]
  },
  "drupal_check": {
    "is_drupal": true,
    "drupal_version": "^9.5",
    "total_modules": 25,
    "outdated_modules": [...]
  },
  "ai_analysis": "..."
}
```

## Project Structure

```
Scanner AI/
├── src/
│   ├── __init__.py
│   ├── scanner_agent.py       # Main orchestrator
│   ├── repository_manager.py  # Git operations
│   ├── vulnerability_scanner.py # Security scanning
│   ├── drupal_checker.py      # Drupal module analysis
│   ├── ai_analyzer.py         # AI-powered insights
│   └── config.py              # Configuration
├── repos.txt                  # List of repositories to scan
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
├── .gitignore
└── README.md
```

## Dependencies

- **GitPython**: Repository cloning and management
- **requests**: HTTP requests for package data
- **python-dotenv**: Environment variable management
- **PyYAML**: YAML configuration parsing
- **packaging**: Version comparison utilities
- **bandit**: Python code security scanner
- **safety**: Python dependency vulnerability checker
- **openai** (optional): OpenAI API client
- **anthropic** (optional): Anthropic Claude API client

## Scanning Details

### Vulnerability Scanner

The vulnerability scanner checks for:

1. **Python Dependencies**: Uses Safety to check `requirements.txt` against known vulnerability databases
2. **Code Security**: Uses Bandit to analyze Python code for security issues
3. **Common Issues**: Checks for exposed sensitive files (.env, credentials, etc.)

### Drupal Module Checker

For Drupal projects (identified by `composer.json`):

1. Extracts all `drupal/*` contrib modules from composer dependencies
2. Queries packages.drupal.org for latest versions
3. Compares installed vs. available versions
4. Categorizes updates by severity:
   - **Major**: Breaking changes, significant updates
   - **Minor**: New features, backward compatible
   - **Patch**: Bug fixes and security patches

## AI Analysis

When enabled, the AI analyzer:

1. Reviews all scan findings
2. Identifies critical security issues
3. Provides prioritized recommendations
4. Offers risk assessment and remediation guidance

Supports:
- **OpenAI GPT-4**: Set `OPENAI_API_KEY`
- **Anthropic Claude**: Set `ANTHROPIC_API_KEY`

## Troubleshooting

### Missing Dependencies

If you see "Safety not installed" or "Bandit not installed":
```bash
pip install safety bandit
```

### Git Clone Failures

- Ensure you have Git installed
- Check repository URLs are correct
- For private repos, ensure SSH keys or credentials are configured

### AI Analysis Not Working

- Verify API keys are set in `.env`
- Check API key has sufficient credits/quota
- Try with `--no-ai` flag to run without AI

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - feel free to use this project for your needs.

## Security Note

This tool is designed to help identify security issues. Always:
- Review scan results carefully
- Test updates in development environments first
- Keep your API keys secure
- Don't commit `.env` file to version control

---

**Happy Scanning! 🔍🛡️**
