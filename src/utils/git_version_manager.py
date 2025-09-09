#!/usr/bin/env python3
"""
Git Version Manager for TinderBot
Manages versions based on Git commits and detects changes
"""

import json
import os
import subprocess
import hashlib
from datetime import datetime
from pathlib import Path

class GitVersionManager:
    def __init__(self, repo_path="."):
        self.repo_path = Path(repo_path)
        self.version_file = self.repo_path / "version.json"
        self.last_commit_file = self.repo_path / ".last_commit"
        
    def is_git_repo(self):
        """Check if current directory is a Git repository"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def get_current_commit_hash(self):
        """Get current Git commit hash"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None
    
    def get_last_commit_hash(self):
        """Get last known commit hash"""
        if self.last_commit_file.exists():
            try:
                with open(self.last_commit_file, 'r') as f:
                    return f.read().strip()
            except:
                return None
        return None
    
    def save_current_commit_hash(self, commit_hash):
        """Save current commit hash"""
        try:
            with open(self.last_commit_file, 'w') as f:
                f.write(commit_hash)
            return True
        except Exception as e:
            print(f"Failed to save commit hash: {e}")
            return False
    
    def has_changes_since_last_check(self):
        """Check if there are changes since last check"""
        current_hash = self.get_current_commit_hash()
        last_hash = self.get_last_commit_hash()
        
        if not current_hash:
            return False
        
        if not last_hash:
            # First time running, save current hash
            self.save_current_commit_hash(current_hash)
            return False
        
        return current_hash != last_hash
    
    def get_git_status(self):
        """Get Git status information"""
        try:
            # Get current branch
            branch_result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            current_branch = branch_result.stdout.strip()
            
            # Get commit count
            commit_result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            commit_count = commit_result.stdout.strip()
            
            # Get last commit message
            message_result = subprocess.run(
                ["git", "log", "-1", "--pretty=format:%s"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            last_message = message_result.stdout.strip()
            
            return {
                "current_branch": current_branch,
                "commit_count": commit_count,
                "last_commit_message": last_message,
                "current_hash": self.get_current_commit_hash(),
                "last_hash": self.get_last_commit_hash()
            }
        except Exception as e:
            return {"error": str(e)}
    
    def generate_version_from_git(self):
        """Generate version number based on Git information"""
        try:
            # Get commit count as patch version
            commit_result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            commit_count = int(commit_result.stdout.strip())
            
            # Get current version from file
            current_version = self.get_current_version()
            major, minor, _ = map(int, current_version.split('.'))
            
            # Use commit count as patch version
            new_version = f"{major}.{minor}.{commit_count}"
            
            return new_version
        except Exception as e:
            print(f"Failed to generate version from Git: {e}")
            return None
    
    def get_current_version(self):
        """Get current version from version.json"""
        if self.version_file.exists():
            try:
                with open(self.version_file, 'r') as f:
                    version_data = json.load(f)
                    return version_data.get('version', '1.0.0')
            except:
                pass
        return '1.0.0'
    
    def update_version(self, new_version):
        """Update version in version.json"""
        try:
            if self.version_file.exists():
                with open(self.version_file, 'r') as f:
                    version_data = json.load(f)
            else:
                version_data = {}
            
            version_data['version'] = new_version
            version_data['last_updated'] = datetime.now().isoformat()
            version_data['git_commit'] = self.get_current_commit_hash()
            
            with open(self.version_file, 'w') as f:
                json.dump(version_data, f, indent=2)
            
            # Save current commit hash
            self.save_current_commit_hash(self.get_current_commit_hash())
            
            print(f"Version updated to {new_version}")
            return True
        except Exception as e:
            print(f"Failed to update version: {e}")
            return False
    
    def check_for_changes(self):
        """Check for changes and suggest version update"""
        if not self.is_git_repo():
            print("⚠️  Not a Git repository")
            return False
        
        if self.has_changes_since_last_check():
            current_hash = self.get_current_commit_hash()
            last_hash = self.get_last_commit_hash()
            
            print(f"Changes detected!")
            print(f"   Last commit: {last_hash[:8] if last_hash else 'None'}")
            print(f"   Current commit: {current_hash[:8] if current_hash else 'None'}")
            
            # Get Git status
            status = self.get_git_status()
            if 'error' not in status:
                print(f"   Branch: {status['current_branch']}")
                print(f"   Commit count: {status['commit_count']}")
                print(f"   Last message: {status['last_commit_message']}")
            
            return True
        else:
            print("No changes detected since last check")
            return False
    
    def auto_update_version(self):
        """Automatically update version based on Git changes"""
        if not self.check_for_changes():
            return False
        
        new_version = self.generate_version_from_git()
        if new_version:
            return self.update_version(new_version)
        
        return False
    
    def get_changelog_since_last_version(self):
        """Get changelog since last version"""
        try:
            last_hash = self.get_last_commit_hash()
            if not last_hash:
                return []
            
            # Get commits since last hash
            result = subprocess.run(
                ["git", "log", f"{last_hash}..HEAD", "--pretty=format:%h - %s (%an, %ar)"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            commits = result.stdout.strip().split('\n') if result.stdout.strip() else []
            return commits
        except Exception as e:
            print(f"Failed to get changelog: {e}")
            return []

def main():
    """Test Git version manager"""
    manager = GitVersionManager()
    
    print("Git Version Manager Test")
    print("=" * 40)
    
    if not manager.is_git_repo():
        print("Not a Git repository")
        return
    
    print("Git repository detected")
    
    status = manager.get_git_status()
    if 'error' not in status:
        print(f"Branch: {status['current_branch']}")
        print(f"Commits: {status['commit_count']}")
        print(f"Last message: {status['last_commit_message']}")
        print(f"Current hash: {status['current_hash'][:8]}")
    
    if manager.check_for_changes():
        print("\nChanges detected - suggesting version update")
        new_version = manager.generate_version_from_git()
        print(f"Suggested version: {new_version}")
        
        changelog = manager.get_changelog_since_last_version()
        if changelog:
            print("\nRecent changes:")
            for commit in changelog[:5]:  # Show last 5 commits
                print(f"  - {commit}")
    else:
        print("\nNo changes detected")

if __name__ == "__main__":
    main()
