"""
Repository Manager - Handles cloning and managing repositories
"""
import logging
import shutil
from pathlib import Path
from typing import List, Optional
from git import Repo, GitCommandError

logger = logging.getLogger(__name__)


class RepositoryManager:
    """Manages repository cloning and cleanup"""
    
    def __init__(self, temp_dir: Path):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(exist_ok=True)
        
    def read_repos_list(self, repos_file: Path) -> List[str]:
        """Read repository URLs from a text file"""
        repos = []
        try:
            with open(repos_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith('#'):
                        repos.append(line)
            logger.info(f"Found {len(repos)} repositories to scan")
            return repos
        except FileNotFoundError:
            logger.error(f"Repository list file not found: {repos_file}")
            return []
    
    def clone_repository(self, repo_url: str) -> Optional[Path]:
        """Clone a repository to the temporary directory"""
        try:
            # Extract repo name from URL
            repo_name = repo_url.rstrip('/').split('/')[-1].replace('.git', '')
            repo_path = self.temp_dir / repo_name
            
            # Remove existing directory if it exists
            if repo_path.exists():
                logger.info(f"Removing existing directory: {repo_path}")
                shutil.rmtree(repo_path)
            
            logger.info(f"Cloning repository: {repo_url}")
            Repo.clone_from(repo_url, repo_path)
            logger.info(f"Successfully cloned to: {repo_path}")
            return repo_path
            
        except GitCommandError as e:
            logger.error(f"Failed to clone {repo_url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error cloning {repo_url}: {e}")
            return None
    
    def cleanup_repository(self, repo_path: Path):
        """Remove a cloned repository"""
        try:
            if repo_path.exists():
                shutil.rmtree(repo_path)
                logger.info(f"Cleaned up repository: {repo_path}")
        except Exception as e:
            logger.error(f"Failed to cleanup {repo_path}: {e}")
    
    def cleanup_all(self):
        """Remove all cloned repositories"""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                self.temp_dir.mkdir(exist_ok=True)
                logger.info("Cleaned up all temporary repositories")
        except Exception as e:
            logger.error(f"Failed to cleanup all repositories: {e}")
