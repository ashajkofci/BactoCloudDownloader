#!/usr/bin/env python3
"""
Release script for BactoCloud Downloader

This script automates the release process:
1. Determines the current version from git tags
2. Prompts for version bump type (major, minor, patch)
3. Creates and pushes a new version tag
4. Triggers GitHub Actions to build and release installers for all platforms
"""

import subprocess
import sys
import re
from typing import Tuple, Optional


def run_command(command: list, check: bool = True) -> Tuple[int, str, str]:
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=check
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout.strip(), e.stderr.strip()


def get_latest_version() -> Optional[str]:
    """Get the latest version tag from git"""
    returncode, stdout, stderr = run_command(
        ['git', 'tag', '-l', 'v*', '--sort=-v:refname'],
        check=False
    )
    
    if returncode != 0:
        print(f"Warning: Could not get git tags: {stderr}")
        return None
    
    tags = stdout.split('\n')
    for tag in tags:
        if tag and re.match(r'^v\d+\.\d+\.\d+$', tag):
            return tag
    
    return None


def parse_version(version_tag: str) -> Tuple[int, int, int]:
    """Parse version tag (e.g., 'v1.2.3') into components"""
    match = re.match(r'^v(\d+)\.(\d+)\.(\d+)$', version_tag)
    if not match:
        raise ValueError(f"Invalid version format: {version_tag}")
    
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def bump_version(version: Tuple[int, int, int], bump_type: str) -> Tuple[int, int, int]:
    """Bump version based on type (major, minor, patch)"""
    major, minor, patch = version
    
    if bump_type == 'major':
        return major + 1, 0, 0
    elif bump_type == 'minor':
        return major, minor + 1, 0
    elif bump_type == 'patch':
        return major, minor, patch + 1
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")


def version_to_tag(version: Tuple[int, int, int]) -> str:
    """Convert version tuple to tag string"""
    return f"v{version[0]}.{version[1]}.{version[2]}"


def confirm_action(message: str) -> bool:
    """Ask user for confirmation"""
    while True:
        response = input(f"{message} (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("Please enter 'y' or 'n'")


def main():
    """Main release process"""
    print("=" * 60)
    print("BactoCloud Downloader Release Script")
    print("=" * 60)
    print()
    
    # Check if we're in a git repository
    returncode, _, stderr = run_command(['git', 'rev-parse', '--git-dir'], check=False)
    if returncode != 0:
        print("Error: Not in a git repository")
        sys.exit(1)
    
    # Check for uncommitted changes
    returncode, stdout, _ = run_command(['git', 'status', '--porcelain'], check=False)
    if stdout:
        print("Warning: You have uncommitted changes:")
        print(stdout)
        if not confirm_action("Do you want to continue anyway?"):
            print("Aborted.")
            sys.exit(0)
        print()
    
    # Get current version
    current_version_tag = get_latest_version()
    if current_version_tag:
        current_version = parse_version(current_version_tag)
        print(f"Current version: {current_version_tag}")
    else:
        current_version = (0, 0, 0)
        print("No previous version found, starting from v0.0.0")
    
    print()
    
    # Get version bump type
    print("Select version bump type:")
    print(f"  1. Major (current: {current_version[0]}) - Breaking changes")
    print(f"  2. Minor (current: {current_version[1]}) - New features")
    print(f"  3. Patch (current: {current_version[2]}) - Bug fixes")
    print()
    
    while True:
        choice = input("Enter choice (1/2/3): ").strip()
        if choice == '1':
            bump_type = 'major'
            break
        elif choice == '2':
            bump_type = 'minor'
            break
        elif choice == '3':
            bump_type = 'patch'
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3")
    
    # Calculate new version
    new_version = bump_version(current_version, bump_type)
    new_version_tag = version_to_tag(new_version)
    
    print()
    print(f"New version will be: {new_version_tag}")
    print()
    
    # Confirm release
    if not confirm_action(f"Create release {new_version_tag}?"):
        print("Aborted.")
        sys.exit(0)
    
    # Create tag
    print()
    print(f"Creating tag {new_version_tag}...")
    
    release_message = input("Enter release message (optional): ").strip()
    if not release_message:
        release_message = f"Release {new_version_tag}"
    
    tag_command = ['git', 'tag', '-a', new_version_tag, '-m', release_message]
    returncode, _, stderr = run_command(tag_command, check=False)
    
    if returncode != 0:
        print(f"Error creating tag: {stderr}")
        sys.exit(1)
    
    print(f"✓ Tag {new_version_tag} created successfully")
    print()
    
    # Push tag
    if confirm_action(f"Push tag {new_version_tag} to origin?"):
        print(f"Pushing tag {new_version_tag}...")
        returncode, _, stderr = run_command(['git', 'push', 'origin', new_version_tag], check=False)
        
        if returncode != 0:
            print(f"Error pushing tag: {stderr}")
            print(f"You can manually push the tag with: git push origin {new_version_tag}")
            sys.exit(1)
        
        print(f"✓ Tag {new_version_tag} pushed successfully")
        print()
        print("=" * 60)
        print("Release process completed!")
        print("=" * 60)
        print()
        print("GitHub Actions will now:")
        print("  1. Build Windows executable (.exe)")
        print("  2. Build Windows installer (Setup.exe)")
        print("  3. Build macOS application (.app)")
        print("  4. Build macOS installer (.dmg)")
        print("  5. Create GitHub release with all artifacts")
        print()
        print(f"View the release at:")
        print(f"  https://github.com/ashajkofci/BactoCloudDownloader/releases/tag/{new_version_tag}")
        print()
        print(f"Monitor the build at:")
        print(f"  https://github.com/ashajkofci/BactoCloudDownloader/actions")
    else:
        print()
        print(f"Tag {new_version_tag} created locally but not pushed.")
        print(f"To push manually, run: git push origin {new_version_tag}")
        print(f"To delete the tag, run: git tag -d {new_version_tag}")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAborted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
