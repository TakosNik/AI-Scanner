"""
Drupal Module Checker - Checks for outdated Drupal contrib modules
"""
import logging
import json
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional
from packaging import version

logger = logging.getLogger(__name__)


class DrupalModuleChecker:
    """Checks Drupal composer.json for outdated contrib modules"""
    
    def __init__(self):
        self.packagist_url = 'https://packages.drupal.org/8/packages.json'
        self.package_cache = None
    
    def check_repository(self, repo_path: Path) -> Optional[Dict[str, Any]]:
        """Check if repository is a Drupal project and analyze modules"""
        composer_file = repo_path / 'composer.json'
        
        if not composer_file.exists():
            logger.info(f"No composer.json found in {repo_path.name}")
            return None
        
        try:
            with open(composer_file, 'r') as f:
                composer_data = json.load(f)
            
            # Check if this is a Drupal project
            if not self._is_drupal_project(composer_data):
                logger.info(f"{repo_path.name} is not a Drupal project")
                return None
            
            logger.info(f"Analyzing Drupal modules in {repo_path.name}")
            
            results = {
                'repo_name': repo_path.name,
                'is_drupal': True,
                'drupal_version': self._get_drupal_version(composer_data),
                'modules': [],
                'outdated_modules': [],
                'total_modules': 0
            }
            
            # Analyze contrib modules
            modules = self._extract_drupal_modules(composer_data)
            results['total_modules'] = len(modules)
            
            # Get all modules with their GitHub URLs
            results['modules'] = self._get_all_modules_info(modules)
            results['outdated_modules'] = self._check_outdated_modules(modules)
            
            return results
            
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in composer.json for {repo_path.name}")
            return None
        except Exception as e:
            logger.error(f"Error analyzing Drupal modules: {e}")
            return None
    
    def _is_drupal_project(self, composer_data: Dict) -> bool:
        """Check if composer.json indicates a Drupal project"""
        require = composer_data.get('require', {})
        
        # Check for Drupal core
        drupal_indicators = [
            'drupal/core',
            'drupal/core-recommended',
            'drupal/core-composer-scaffold'
        ]
        
        return any(indicator in require for indicator in drupal_indicators)
    
    def _get_drupal_version(self, composer_data: Dict) -> str:
        """Extract Drupal core version"""
        require = composer_data.get('require', {})
        
        for core_package in ['drupal/core', 'drupal/core-recommended']:
            if core_package in require:
                return require[core_package]
        
        return 'unknown'
    
    def _extract_drupal_modules(self, composer_data: Dict) -> Dict[str, str]:
        """Extract Drupal contrib modules from composer.json"""
        modules = {}
        require = composer_data.get('require', {})
        
        for package, version_constraint in require.items():
            # Drupal contrib modules follow the pattern drupal/module_name
            if package.startswith('drupal/') and package not in [
                'drupal/core',
                'drupal/core-recommended',
                'drupal/core-composer-scaffold',
                'drupal/core-dev'
            ]:
                modules[package] = version_constraint
        
        return modules
    
    def _get_all_modules_info(self, modules: Dict[str, str]) -> List[Dict[str, Any]]:
        """Get information for all modules including repository URLs"""
        modules_info = []
        
        # Load Drupal package data if not already loaded
        if not self.package_cache:
            self._load_package_data()
        
        for module_name, current_version in modules.items():
            repo_url = self._get_module_github_url(module_name)
            latest = self._get_latest_version(module_name)
            
            modules_info.append({
                'module': module_name,
                'current_version': current_version,
                'latest_version': latest or 'unknown',
                'repository_url': repo_url
            })
        
        return modules_info
    
    def _check_outdated_modules(self, modules: Dict[str, str]) -> List[Dict[str, Any]]:
        """Check which modules have newer versions available"""
        outdated = []
        
        # Load Drupal package data
        if not self.package_cache:
            self._load_package_data()
        
        if not self.package_cache:
            logger.warning("Could not load Drupal package data")
            return outdated
        
        for module_name, current_version in modules.items():
            latest = self._get_latest_version(module_name)
            repo_url = self._get_module_github_url(module_name)
            
            if latest:
                try:
                    # Clean version strings for comparison
                    current = self._clean_version(current_version)
                    if current and self._is_outdated(current, latest):
                        outdated.append({
                            'module': module_name,
                            'current_version': current_version,
                            'latest_version': latest,
                            'severity': self._calculate_update_severity(current, latest),
                            'repository_url': repo_url
                        })
                except Exception as e:
                    logger.debug(f"Could not compare versions for {module_name}: {e}")
        
        return outdated
    
    def _load_package_data(self):
        """Load Drupal package data from packages.drupal.org"""
        try:
            logger.info("Fetching Drupal package data...")
            # Note: The new Drupal packages API uses individual package files
            # We'll fetch them on-demand instead of loading everything at once
            self.package_cache = {}  # We'll use this as a flag that we tried to load
        except Exception as e:
            logger.error(f"Failed to initialize Drupal package data: {e}")
            self.package_cache = None
    
    def _fetch_module_versions(self, module_name: str) -> Optional[list]:
        """Fetch version data for a specific module from Drupal packages API"""
        try:
            # Use the p2 endpoint format
            # https://packages.drupal.org/files/packages/8/p2/drupal/MODULE_NAME.json
            module_short_name = module_name.replace('drupal/', '')
            url = f"https://packages.drupal.org/files/packages/8/p2/drupal/{module_short_name}.json"
            
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'packages' in data and module_name in data['packages']:
                    return data['packages'][module_name]
            return None
        except Exception as e:
            logger.debug(f"Failed to fetch versions for {module_name}: {e}")
            return None
    
    def _get_module_github_url(self, module_name: str) -> Optional[str]:
        """Get the GitHub or Drupal.org repository URL for a module"""
        # Try to get from API
        versions_list = self._fetch_module_versions(module_name)
        if versions_list and len(versions_list) > 0:
            # Check the first version for source URL
            for ver_data in versions_list[:5]:  # Check first few versions
                if isinstance(ver_data, dict):
                    source = ver_data.get('source', {})
                    if source.get('type') == 'git':
                        url = source.get('url', '')
                        if url:
                            # Convert git URL to https URL if needed
                            if 'github.com' in url:
                                if url.startswith('git@github.com:'):
                                    url = url.replace('git@github.com:', 'https://github.com/')
                                if url.endswith('.git'):
                                    url = url[:-4]
                                return url
                            # Handle Drupal.org Git URLs
                            elif 'git.drupalcode.org' in url:
                                if url.endswith('.git'):
                                    url = url[:-4]
                                # Convert to Drupal.org project page
                                module_short_name = module_name.replace('drupal/', '')
                                return f"https://www.drupal.org/project/{module_short_name}"
                            else:
                                # Return any other Git URL as-is
                                if url.endswith('.git'):
                                    url = url[:-4]
                                return url
        
        # Fallback: construct Drupal.org project URL
        module_short_name = module_name.replace('drupal/', '')
        return f"https://www.drupal.org/project/{module_short_name}"
    
    def _get_latest_version(self, module_name: str) -> Optional[str]:
        """Get the latest stable version of a module"""
        versions_list = self._fetch_module_versions(module_name)
        
        if not versions_list:
            return None
        
        # Filter and collect stable versions
        stable_versions = []
        for ver_data in versions_list:
            if isinstance(ver_data, dict) and 'version' in ver_data:
                ver_string = ver_data['version']
                # Skip dev, alpha, beta, rc versions
                ver_lower = ver_string.lower()
                if any(unstable in ver_lower for unstable in ['dev', 'alpha', 'beta', 'rc', 'x-dev']):
                    continue
                stable_versions.append(ver_string)
        
        if stable_versions:
            # Sort versions and return the latest
            try:
                stable_versions.sort(key=lambda v: version.parse(v), reverse=True)
                return stable_versions[0]
            except Exception as e:
                logger.debug(f"Error sorting versions for {module_name}: {e}")
                # Fallback: return the first version found
                return stable_versions[0] if stable_versions else None
        
        return None
    
    def _is_outdated(self, current: str, latest: str) -> bool:
        """Check if current version is outdated"""
        try:
            return version.parse(current) < version.parse(latest)
        except:
            return False
    
    def _calculate_update_severity(self, current: str, latest: str) -> str:
        """Calculate the severity of the update needed"""
        try:
            curr = version.parse(current)
            late = version.parse(latest)
            
            # Compare major, minor, patch versions
            if hasattr(curr, 'major') and hasattr(late, 'major'):
                if late.major > curr.major:
                    return 'major'
                elif late.minor > curr.minor:
                    return 'minor'
                else:
                    return 'patch'
        except:
            pass
        
        return 'unknown'
