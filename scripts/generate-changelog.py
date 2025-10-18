#!/usr/bin/env python3
"""
Fancy Changelog Generator for AeNux
Generates beautiful changelogs with emojis, categories, and formatting
"""

import os
import sys
import subprocess
import re
from datetime import datetime
from typing import List, Dict, Any

class ChangelogGenerator:
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path
        self.categories = {
            'feat': {'emoji': '✨', 'title': 'Features', 'description': 'New features and enhancements'},
            'fix': {'emoji': '🐛', 'title': 'Bug Fixes', 'description': 'Bug fixes and corrections'},
            'perf': {'emoji': '⚡', 'title': 'Performance', 'description': 'Performance improvements'},
            'refactor': {'emoji': '♻️', 'title': 'Refactoring', 'description': 'Code refactoring and cleanup'},
            'docs': {'emoji': '📚', 'title': 'Documentation', 'description': 'Documentation updates'},
            'style': {'emoji': '💄', 'title': 'Styling', 'description': 'Code style and formatting changes'},
            'test': {'emoji': '🧪', 'title': 'Testing', 'description': 'Test additions and improvements'},
            'build': {'emoji': '🔨', 'title': 'Build System', 'description': 'Build system and CI/CD changes'},
            'ci': {'emoji': '👷', 'title': 'CI/CD', 'description': 'Continuous integration changes'},
            'chore': {'emoji': '🔧', 'title': 'Chores', 'description': 'Maintenance and housekeeping'},
            'security': {'emoji': '🔒', 'title': 'Security', 'description': 'Security improvements'},
            'breaking': {'emoji': '💥', 'title': 'Breaking Changes', 'description': 'Breaking changes that require attention'}
        }

    def get_git_log(self, from_tag: str = None, to_tag: str = "HEAD") -> List[str]:
        """Get git log between tags or commits"""
        cmd = ["git", "log", "--pretty=format:%H|%s|%b|%an|%ae|%ad", "--date=short"]
        
        if from_tag:
            cmd.append(f"{from_tag}..{to_tag}")
        else:
            cmd.append(to_tag)
            
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.repo_path)
            if result.returncode != 0:
                return []
            return [line for line in result.stdout.strip().split('\n') if line]
        except Exception:
            return []

    def parse_commit(self, commit_line: str) -> Dict[str, Any]:
        """Parse a single commit line"""
        parts = commit_line.split('|', 5)
        if len(parts) < 6:
            return None
            
        commit_hash, subject, body, author, email, date = parts
        
        # Parse conventional commit format
        type_match = re.match(r'^(\w+)(?:\(([^)]+)\))?: (.+)$', subject)
        
        commit_type = 'chore'
        scope = None
        description = subject
        
        if type_match:
            commit_type = type_match.group(1).lower()
            scope = type_match.group(2)
            description = type_match.group(3)
        
        return {
            'hash': commit_hash,
            'type': commit_type,
            'scope': scope,
            'description': description,
            'body': body,
            'author': author,
            'email': email,
            'date': date,
            'is_breaking': '!' in subject or 'BREAKING CHANGE' in body
        }

    def categorize_commits(self, commits: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize commits by type"""
        categorized = {key: [] for key in self.categories.keys()}
        
        for commit in commits:
            commit_type = commit['type']
            if commit['is_breaking']:
                categorized['breaking'].append(commit)
            elif commit_type in categorized:
                categorized[commit_type].append(commit)
            else:
                categorized['chore'].append(commit)
        
        return categorized

    def format_commit(self, commit: Dict[str, Any]) -> str:
        """Format a single commit for display"""
        scope = f"**{commit['scope']}**: " if commit['scope'] else ""
        description = commit['description']
        
        # Add breaking change indicator
        if commit['is_breaking']:
            description = f"💥 **BREAKING**: {description}"
        
        return f"- {scope}{description}"

    def generate_changelog(self, version: str, from_tag: str = None, to_tag: str = "HEAD") -> str:
        """Generate a complete changelog"""
        commits = self.get_git_log(from_tag, to_tag)
        parsed_commits = [self.parse_commit(commit) for commit in commits if self.parse_commit(commit)]
        categorized = self.categorize_commits(parsed_commits)
        
        # Get version info
        version_clean = version.lstrip('v')
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Start building changelog
        changelog = f"""# AeNux v{version_clean} Release Notes

<div align="center">

![AeNux Logo](https://github.com/cutefishaep/AeNux/blob/main/asset/logo.png)

**Release Date**: {current_date}  
**Version**: {version_clean}

[![Linux Compatible](https://img.shields.io/badge/Linux-Compatible-brightgreen?style=for-the-badge&logo=linux)](https://www.linux.org)
[![Wine](https://img.shields.io/badge/Wine-Compatible-7e0202?style=for-the-badge&logo=wine)](https://www.winehq.org)
[![Qt6](https://img.shields.io/badge/Qt6-GUI-41cd52?style=for-the-badge&logo=qt)](https://www.qt.io)

</div>

---

## 🎉 What's New

"""
        
        # Add categorized changes
        for category, info in self.categories.items():
            commits_in_category = categorized[category]
            if commits_in_category:
                changelog += f"### {info['emoji']} {info['title']}\n\n"
                changelog += f"*{info['description']}*\n\n"
                
                for commit in commits_in_category:
                    changelog += f"{self.format_commit(commit)}\n"
                
                changelog += "\n"
        
        # Add package information
        changelog += """## 📦 Package Information

### DEB Package (Ubuntu/Debian)
```bash
sudo dpkg -i aenux_{version}_amd64.deb
sudo apt-get install -f  # Install dependencies if needed
```

### AppImage (Any Linux)
```bash
chmod +x aenux-{version}-x86_64.AppImage
./aenux-{version}-x86_64.AppImage
```

## 🔧 System Requirements

- **OS**: Linux (Ubuntu 20.04+, Debian 11+, Elementary OS 6+, etc.)
- **Python**: 3.8+ (included in packages)
- **Wine**: 6.0+ (install separately)
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space

## 🐛 Known Issues

- Hardware acceleration limited on some systems
- Occasional UI flickering with certain plugins
- Memory management issues on some distributions

## 📊 Statistics

- **Total Commits**: {total_commits}
- **Contributors**: {contributors}
- **Files Changed**: {files_changed}

---

<div align="center">

**Full Changelog**: https://github.com/cutefishaep/AeNux/compare/{from_tag}...{to_tag}

Made with 🎃 by [cutefishaep](https://github.com/cutefishaep)

</div>
""".format(
            version=version_clean,
            total_commits=len(parsed_commits),
            contributors=len(set(commit['author'] for commit in parsed_commits)),
            files_changed="N/A",  # Could be calculated with git diff --stat
            from_tag=from_tag or "initial",
            to_tag=to_tag
        )
        
        return changelog

    def save_changelog(self, changelog: str, filename: str = "CHANGELOG.md"):
        """Save changelog to file"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(changelog)
        print(f"Changelog saved to {filename}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate-changelog.py <version> [from_tag] [to_tag]")
        print("Example: python generate-changelog.py v1.9.0 v1.8.0 HEAD")
        sys.exit(1)
    
    version = sys.argv[1]
    from_tag = sys.argv[2] if len(sys.argv) > 2 else None
    to_tag = sys.argv[3] if len(sys.argv) > 3 else "HEAD"
    
    generator = ChangelogGenerator()
    changelog = generator.generate_changelog(version, from_tag, to_tag)
    generator.save_changelog(changelog)
    
    print("🎉 Fancy changelog generated successfully!")
    print(f"📝 Version: {version}")
    print(f"📅 From: {from_tag or 'initial'}")
    print(f"📅 To: {to_tag}")

if __name__ == "__main__":
    main()
