"""
AI-Powered Report Analyzer
Uses AI to analyze scan results and provide insights
"""
import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class AIAnalyzer:
    """Uses AI to analyze security scan results"""
    
    def __init__(self, provider: str = 'openai', model: str = None, base_url: str = None):
        self.provider = provider
        self.model = model or os.getenv('OPENAI_MODEL', 'gpt-4')
        self.base_url = base_url or os.getenv('OPENAI_BASE_URL')
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize AI client based on provider"""
        try:
            if self.provider == 'openai':
                api_key = os.getenv('OPENAI_API_KEY', 'not-needed')
                
                try:
                    import openai
                    
                    # Support for local OpenAI-compatible API
                    if self.base_url:
                        self.client = openai.OpenAI(
                            api_key=api_key,
                            base_url=self.base_url
                        )
                        logger.info(f"OpenAI client initialized with local endpoint: {self.base_url}")
                        logger.info(f"Using model: {self.model}")
                    else:
                        self.client = openai.OpenAI(api_key=api_key)
                        logger.info("OpenAI client initialized with cloud endpoint")
                        
                except Exception as e:
                    logger.error(f"Failed to initialize OpenAI client: {e}")
                    self.client = None
            elif self.provider == 'anthropic':
                api_key = os.getenv('ANTHROPIC_API_KEY')
                if api_key:
                    import anthropic
                    self.client = anthropic.Anthropic(api_key=api_key)
                    logger.info("Anthropic client initialized")
                else:
                    logger.warning("ANTHROPIC_API_KEY not set")
        except ImportError as e:
            logger.warning(f"AI provider {self.provider} not available: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize AI client: {e}")
    
    def analyze_scan_results(self, scan_results: Dict[str, Any]) -> Optional[str]:
        """Analyze scan results using AI and provide insights"""
        if not self.client:
            logger.warning("AI client not available, skipping analysis")
            return None
        
        try:
            # Prepare the prompt
            prompt = self._prepare_analysis_prompt(scan_results)
            
            # Get AI analysis
            if self.provider == 'openai':
                return self._analyze_with_openai(prompt)
            elif self.provider == 'anthropic':
                return self._analyze_with_anthropic(prompt)
            
        except Exception as e:
            logger.error(f"Error during AI analysis: {e}")
            return None
    
    def _prepare_analysis_prompt(self, scan_results: Dict[str, Any]) -> str:
        """Prepare a prompt for AI analysis"""
        prompt = "Analyze the following security scan results and provide:\n"
        prompt += "1. Summary of critical issues\n"
        prompt += "2. Prioritized recommendations\n"
        prompt += "3. Risk assessment\n\n"
        prompt += "Scan Results:\n"
        prompt += f"Repository: {scan_results.get('repo_name', 'Unknown')}\n\n"
        
        # Vulnerability findings
        vuln_results = scan_results.get('vulnerability_scan', {})
        if vuln_results:
            prompt += "Vulnerabilities:\n"
            
            python_vulns = vuln_results.get('python_dependencies', [])
            if python_vulns:
                prompt += f"- Python dependency vulnerabilities: {len(python_vulns)} found\n"
            
            bandit_issues = vuln_results.get('bandit_issues', [])
            if bandit_issues:
                prompt += f"- Bandit security issues: {len(bandit_issues)} found\n"
                # Add severity breakdown
                severity_counts = {}
                for issue in bandit_issues:
                    sev = issue.get('issue_severity', 'UNKNOWN')
                    severity_counts[sev] = severity_counts.get(sev, 0) + 1
                prompt += f"  Severity breakdown: {severity_counts}\n"
            
            common_issues = vuln_results.get('common_issues', [])
            if common_issues:
                prompt += f"- Common security issues: {len(common_issues)} found\n"
        
        # Drupal module findings
        drupal_results = scan_results.get('drupal_check', {})
        if drupal_results and drupal_results.get('is_drupal'):
            prompt += f"\nDrupal Analysis:\n"
            prompt += f"- Drupal version: {drupal_results.get('drupal_version', 'unknown')}\n"
            prompt += f"- Total modules: {drupal_results.get('total_modules', 0)}\n"
            
            outdated = drupal_results.get('outdated_modules', [])
            if outdated:
                prompt += f"- Outdated modules: {len(outdated)}\n"
                # Group by severity
                severity_groups = {}
                for module in outdated:
                    sev = module.get('severity', 'unknown')
                    severity_groups.setdefault(sev, []).append(module['module'])
                
                for sev, mods in severity_groups.items():
                    prompt += f"  {sev.upper()}: {len(mods)} modules\n"
        
        prompt += "\nProvide a concise security analysis and recommendations."
        return prompt
    
    def _analyze_with_openai(self, prompt: str) -> str:
        """Get analysis from OpenAI or OpenAI-compatible API"""
        try:
            logger.info(f"Requesting AI analysis using model: {self.model}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a security analyst expert. Provide concise, actionable security recommendations."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return None
    
    def _analyze_with_anthropic(self, prompt: str) -> str:
        """Get analysis from Anthropic Claude"""
        try:
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return None
