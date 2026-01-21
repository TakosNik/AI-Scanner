"""
Main Scanner Agent - Orchestrates the scanning process
"""
import logging
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from config import TEMP_DIR, OUTPUT_DIR, REPOS_FILE, LOG_LEVEL, OPENAI_MODEL, OPENAI_BASE_URL
from repository_manager import RepositoryManager
from vulnerability_scanner import VulnerabilityScanner
from drupal_checker import DrupalModuleChecker
from ai_analyzer import AIAnalyzer

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('scanner.log')
    ]
)

logger = logging.getLogger(__name__)


class ScannerAgent:
    """Main AI agent that orchestrates repository scanning"""
    
    def __init__(self, use_ai: bool = True, ai_provider: str = 'openai', 
                 ai_model: str = None, ai_base_url: str = None):
        self.repo_manager = RepositoryManager(TEMP_DIR)
        self.vuln_scanner = VulnerabilityScanner()
        self.drupal_checker = DrupalModuleChecker()
        
        if use_ai:
            self.ai_analyzer = AIAnalyzer(
                provider=ai_provider,
                model=ai_model or OPENAI_MODEL,
                base_url=ai_base_url or OPENAI_BASE_URL
            )
        else:
            self.ai_analyzer = None
            
        self.results = []
        
    def run(self, cleanup: bool = True):
        """Main execution flow"""
        logger.info("=" * 60)
        logger.info("Starting Scanner AI Agent")
        logger.info("=" * 60)
        
        # Read repository list
        repos = self.repo_manager.read_repos_list(REPOS_FILE)
        
        if not repos:
            logger.error("No repositories to scan. Please add URLs to repos.txt")
            return
        
        # Process each repository
        for i, repo_url in enumerate(repos, 1):
            logger.info(f"\n[{i}/{len(repos)}] Processing: {repo_url}")
            self._process_repository(repo_url, cleanup)
        
        # Generate final report
        self._generate_report()
        
        logger.info("\n" + "=" * 60)
        logger.info("Scan complete!")
        logger.info(f"Results saved to: {OUTPUT_DIR}")
        logger.info("=" * 60)
    
    def _process_repository(self, repo_url: str, cleanup: bool = True):
        """Process a single repository"""
        # Clone repository
        repo_path = self.repo_manager.clone_repository(repo_url)
        
        if not repo_path:
            logger.error(f"Failed to clone repository: {repo_url}")
            self.results.append({
                'repo_url': repo_url,
                'status': 'failed',
                'error': 'Clone failed'
            })
            return
        
        try:
            # Run scans
            scan_result = {
                'repo_url': repo_url,
                'repo_name': repo_path.name,
                'scan_time': datetime.now().isoformat(),
                'status': 'completed'
            }
            
            # Vulnerability scan
            logger.info("Running vulnerability scan...")
            scan_result['vulnerability_scan'] = self.vuln_scanner.scan_repository(repo_path)
            
            # Drupal module check
            logger.info("Checking for Drupal modules...")
            drupal_result = self.drupal_checker.check_repository(repo_path)
            if drupal_result:
                scan_result['drupal_check'] = drupal_result
            
            # AI analysis
            if self.ai_analyzer:
                logger.info("Running AI analysis...")
                ai_analysis = self.ai_analyzer.analyze_scan_results(scan_result)
                if ai_analysis:
                    scan_result['ai_analysis'] = ai_analysis
            
            self.results.append(scan_result)
            
            # Save individual result
            self._save_individual_result(scan_result)
            
        except Exception as e:
            logger.error(f"Error processing repository: {e}", exc_info=True)
            self.results.append({
                'repo_url': repo_url,
                'status': 'error',
                'error': str(e)
            })
        
        finally:
            # Cleanup
            if cleanup:
                self.repo_manager.cleanup_repository(repo_path)
    
    def _save_individual_result(self, result: Dict[str, Any]):
        """Save individual repository scan result as readable text"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        repo_name = result.get('repo_name', 'unknown')
        filename = f"{repo_name}_{timestamp}.txt"
        filepath = OUTPUT_DIR / filename
        
        try:
            with open(filepath, 'w') as f:
                self._write_text_report(f, result)
            logger.info(f"Saved result to: {filepath}")
        except Exception as e:
            logger.error(f"Failed to save result: {e}")
    
    def _write_text_report(self, f, result: Dict[str, Any]):
        """Write scan result in human-readable text format"""
        f.write("=" * 80 + "\n")
        f.write(f"SECURITY SCAN REPORT: {result.get('repo_name', 'Unknown')}\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Repository URL: {result.get('repo_url', 'N/A')}\n")
        f.write(f"Scan Time: {result.get('scan_time', 'N/A')}\n")
        f.write(f"Status: {result.get('status', 'N/A').upper()}\n")
        f.write("\n" + "-" * 80 + "\n\n")
        
        # Vulnerability Scan Results
        vuln = result.get('vulnerability_scan', {})
        if vuln:
            f.write("VULNERABILITY SCAN RESULTS\n")
            f.write("-" * 80 + "\n\n")
            
            # Python Dependencies
            py_deps = vuln.get('python_dependencies', [])
            if py_deps:
                f.write(f"⚠️  PYTHON VULNERABILITIES ({len(py_deps)} found)\n\n")
                for dep in py_deps:
                    f.write(f"  • Package: {dep}\n")
                f.write("\n")
            else:
                f.write("✓ No Python dependency vulnerabilities found\n\n")
            
            # Bandit Issues
            bandit = vuln.get('bandit_issues', [])
            if bandit:
                f.write(f"⚠️  SECURITY CODE ISSUES ({len(bandit)} found)\n\n")
                for issue in bandit:
                    f.write(f"  • {issue}\n")
                f.write("\n")
            else:
                f.write("✓ No security code issues found\n\n")
            
            # Common Issues
            common = vuln.get('common_issues', [])
            if common:
                f.write(f"ℹ️  COMMON ISSUES ({len(common)} found)\n\n")
                for issue in common:
                    f.write(f"  • {issue}\n")
                f.write("\n")
            
            f.write("-" * 80 + "\n\n")
        
        # Drupal Check Results
        drupal = result.get('drupal_check', {})
        if drupal and drupal.get('is_drupal'):
            f.write("DRUPAL PROJECT ANALYSIS\n")
            f.write("-" * 80 + "\n\n")
            
            f.write(f"Drupal Version: {drupal.get('drupal_version', 'Unknown')}\n")
            f.write(f"Total Contrib Modules: {drupal.get('total_modules', 0)}\n\n")
            
            # All Modules
            modules = drupal.get('modules', [])
            if modules:
                f.write("INSTALLED MODULES:\n\n")
                for mod in modules:
                    f.write(f"  📦 {mod.get('module', 'Unknown')}\n")
                    f.write(f"     Current Version: {mod.get('current_version', 'N/A')}\n")
                    f.write(f"     Latest Version: {mod.get('latest_version', 'N/A')}\n")
                    if mod.get('repository_url'):
                        f.write(f"     Repository: {mod.get('repository_url')}\n")
                    f.write("\n")
            
            # Outdated Modules
            outdated = drupal.get('outdated_modules', [])
            if outdated:
                f.write(f"\n⚠️  OUTDATED MODULES ({len(outdated)} need updates):\n\n")
                for mod in outdated:
                    f.write(f"  📦 {mod.get('module', 'Unknown')}\n")
                    f.write(f"     Current: {mod.get('current_version', 'N/A')}\n")
                    f.write(f"     Latest: {mod.get('latest_version', 'N/A')}\n")
                    f.write(f"     Update Severity: {mod.get('severity', 'unknown').upper()}\n")
                    if mod.get('repository_url'):
                        f.write(f"     Repository: {mod.get('repository_url')}\n")
                    f.write("\n")
            else:
                f.write("✓ All modules are up to date\n\n")
            
            f.write("-" * 80 + "\n\n")
        
        # AI Analysis
        ai_analysis = result.get('ai_analysis')
        if ai_analysis:
            f.write("AI-POWERED SECURITY ANALYSIS\n")
            f.write("-" * 80 + "\n\n")
            f.write(ai_analysis)
            f.write("\n\n")
            f.write("-" * 80 + "\n\n")
        
        f.write("\nEnd of Report\n")
        f.write("=" * 80 + "\n")

    
    def _generate_report(self):
        """Generate summary report of all scans in text format"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = OUTPUT_DIR / f"summary_report_{timestamp}.txt"
        
        summary = {
            'scan_date': datetime.now().isoformat(),
            'total_repositories': len(self.results),
            'successful_scans': sum(1 for r in self.results if r.get('status') == 'completed'),
            'failed_scans': sum(1 for r in self.results if r.get('status') != 'completed'),
            'results': self.results
        }
        
        try:
            with open(report_file, 'w') as f:
                self._write_summary_report(f, summary)
            logger.info(f"\nSummary report saved to: {report_file}")
            
            # Print summary to console
            self._print_summary(summary)
            
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
    
    def _write_summary_report(self, f, summary: Dict[str, Any]):
        """Write summary report in text format"""
        f.write("=" * 80 + "\n")
        f.write("SECURITY SCAN SUMMARY REPORT\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Scan Date: {summary['scan_date']}\n")
        f.write(f"Total Repositories: {summary['total_repositories']}\n")
        f.write(f"Successful Scans: {summary['successful_scans']}\n")
        f.write(f"Failed Scans: {summary['failed_scans']}\n")
        f.write("\n" + "-" * 80 + "\n\n")
        
        for result in summary['results']:
            repo_name = result.get('repo_name', 'Unknown')
            status = result.get('status', 'unknown')
            
            f.write(f"\n📁 REPOSITORY: {repo_name}\n")
            f.write(f"   URL: {result.get('repo_url', 'N/A')}\n")
            f.write(f"   Status: {status.upper()}\n")
            
            if status == 'completed':
                # Vulnerability summary
                vuln = result.get('vulnerability_scan', {})
                if vuln:
                    py_vulns = len(vuln.get('python_dependencies', []))
                    bandit_issues = len(vuln.get('bandit_issues', []))
                    common_issues = len(vuln.get('common_issues', []))
                    
                    if py_vulns > 0:
                        f.write(f"   ⚠️  Python Vulnerabilities: {py_vulns}\n")
                    if bandit_issues > 0:
                        f.write(f"   ⚠️  Security Code Issues: {bandit_issues}\n")
                    if common_issues > 0:
                        f.write(f"   ℹ️  Common Issues: {common_issues}\n")
                
                # Drupal summary
                drupal = result.get('drupal_check', {})
                if drupal and drupal.get('is_drupal'):
                    total = drupal.get('total_modules', 0)
                    outdated = len(drupal.get('outdated_modules', []))
                    f.write(f"   🔷 Drupal Version: {drupal.get('drupal_version', 'Unknown')}\n")
                    f.write(f"   📦 Total Modules: {total}\n")
                    if outdated > 0:
                        f.write(f"   ⚠️  Outdated Modules: {outdated}\n")
            else:
                error = result.get('error', 'Unknown error')
                f.write(f"   ❌ Error: {error}\n")
            
            f.write("\n" + "-" * 80 + "\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("End of Summary Report\n")
        f.write("=" * 80 + "\n")

    
    def _print_summary(self, summary: Dict[str, Any]):
        """Print scan summary to console"""
        print("\n" + "=" * 60)
        print("SCAN SUMMARY")
        print("=" * 60)
        print(f"Total repositories scanned: {summary['total_repositories']}")
        print(f"Successful scans: {summary['successful_scans']}")
        print(f"Failed scans: {summary['failed_scans']}")
        print()
        
        for result in summary['results']:
            if result.get('status') == 'completed':
                print(f"\n📁 {result.get('repo_name', 'Unknown')}")
                print("-" * 40)
                
                # Vulnerability summary
                vuln = result.get('vulnerability_scan', {})
                if vuln:
                    py_vulns = len(vuln.get('python_dependencies', []))
                    bandit_issues = len(vuln.get('bandit_issues', []))
                    common_issues = len(vuln.get('common_issues', []))
                    
                    if py_vulns > 0:
                        print(f"  ⚠️  Python vulnerabilities: {py_vulns}")
                    if bandit_issues > 0:
                        print(f"  ⚠️  Bandit issues: {bandit_issues}")
                    if common_issues > 0:
                        print(f"  ℹ️  Common issues: {common_issues}")
                
                # Drupal summary
                drupal = result.get('drupal_check', {})
                if drupal and drupal.get('is_drupal'):
                    outdated = len(drupal.get('outdated_modules', []))
                    total = drupal.get('total_modules', 0)
                    print(f"  🔷 Drupal modules: {total}")
                    if outdated > 0:
                        print(f"  📦 Outdated modules: {outdated}")
        
        print("\n" + "=" * 60)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Repository Security Scanner')
    parser.add_argument('--no-ai', action='store_true', help='Disable AI analysis')
    parser.add_argument('--no-cleanup', action='store_true', help='Keep cloned repositories')
    parser.add_argument('--ai-provider', choices=['openai', 'anthropic'], 
                       default='openai', help='AI provider to use')
    parser.add_argument('--ai-model', type=str, help='AI model to use (e.g., gpt-oss-20b)')
    parser.add_argument('--ai-base-url', type=str, help='Base URL for AI API (for local models)')
    
    args = parser.parse_args()
    
    # Create and run scanner
    scanner = ScannerAgent(
        use_ai=not args.no_ai,
        ai_provider=args.ai_provider,
        ai_model=args.ai_model,
        ai_base_url=args.ai_base_url
    )
    scanner.run(cleanup=not args.no_cleanup)


if __name__ == '__main__':
    main()
