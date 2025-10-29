# Release Guide

## How to Create a Release

### Using GitHub Actions UI (Easiest Method)

1. **Navigate to Actions Tab**
   - Go to your repository on GitHub
   - Click the "Actions" tab at the top

2. **Select Build Workflow**
   - In the left sidebar, click on "Build"
   
3. **Run the Workflow**
   - Click the "Run workflow" dropdown button (on the right side)
   - You'll see two input fields:

4. **Choose Version Bump Type**
   - Select from the dropdown:
     - **patch** - Bug fixes (e.g., v1.0.0 → v1.0.1)
     - **minor** - New features (e.g., v1.0.0 → v1.1.0)
     - **major** - Breaking changes (e.g., v1.0.0 → v2.0.0)

5. **Optional: Custom Version**
   - Leave blank to auto-increment based on bump type
   - Or enter a specific version like `v1.2.3` or `1.2.3`
   - Custom version overrides the bump type selection

6. **Start the Build**
   - Click the green "Run workflow" button
   - The workflow will:
     - Calculate the new version
     - Create and push a git tag
     - Build Windows and macOS installers
     - Create a GitHub release with all artifacts

7. **Monitor Progress**
   - Watch the workflow run in real-time
   - Once complete, check the "Releases" section for your new release

### Release Artifacts

Each release includes:

**Windows:**
- `BactoCloudDownloader-vX.X.X-Windows.exe` - Standalone executable
- `BactoCloudDownloader-vX.X.X-Setup.exe` - Windows installer (Inno Setup)

**macOS:**
- `BactoCloudDownloader-vX.X.X-macOS` - Standalone executable
- `BactoCloudDownloader-vX.X.X.dmg` - macOS disk image installer

### Using the Command Line Script

Alternatively, you can use the Python script:

```bash
python release.py
```

This provides an interactive prompt to:
1. View current version
2. Select bump type (major/minor/patch)
3. Confirm the new version
4. Create and push the tag

The GitHub Actions workflow will automatically trigger when the tag is pushed.

## Version Numbering

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR** version (X.0.0) - Incompatible API changes
- **MINOR** version (0.X.0) - Add functionality in a backwards compatible manner
- **PATCH** version (0.0.X) - Backwards compatible bug fixes

## Troubleshooting

**Q: The workflow failed to create a tag**
- A: Make sure you have write permissions to the repository

**Q: I want to delete a release**
- A: Go to Releases, click on the release, then "Delete this release"
- A: To delete the tag: `git tag -d vX.X.X && git push origin :refs/tags/vX.X.X`

**Q: The version number is wrong**
- A: Use the custom version field to specify the exact version you want
