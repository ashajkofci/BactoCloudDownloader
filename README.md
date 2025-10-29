# BactoCloud Downloader

A Python GUI application for downloading measurement data from the BactoCloud API.

## Features

- **API Key Authentication**: Securely connect to BactoCloud using your organization API key
- **Device Selection**: Browse and select one or multiple devices from your organization
- **Date Range Filtering**: Select start and end dates for data retrieval (automatically sets time to 00:00 and 23:59)
- **Automatic File Organization**: Downloads are organized by device serial number and measurement date/name
- **FCS File Download**: Automatically downloads Flow Cytometry Standard (FCS) files in binary format
- **JSON Metadata Export**: Saves complete measurement data including computations in JSON format
- **Progress Tracking**: Real-time progress updates and logging during download

## Installation

### From Source

1. Clone this repository:
```bash
git clone https://github.com/ashajkofci/BactoCloudDownloader.git
cd BactoCloudDownloader
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python bactocloud_downloader.py
```

### Pre-built Binaries

Download the latest release for your platform from the [Releases](https://github.com/ashajkofci/BactoCloudDownloader/releases) page:

- **Windows**: `BactoCloudDownloader-Setup.exe` or `BactoCloudDownloader.exe`
- **macOS**: `BactoCloudDownloader.dmg` or `BactoCloudDownloader.app`

## Usage

1. **Enter API Key**: 
   - Obtain an API key from your BactoCloud organization settings
   - Enter the key in the "API Key" field
   - Click "Load Devices"

2. **Select Devices**:
   - Choose one or more devices from the list
   - Use Ctrl+Click (Cmd+Click on Mac) to select multiple devices

3. **Set Date Range**:
   - Click the calendar icon to select start and end dates
   - Start time is automatically set to 00:00:00
   - End time is automatically set to 23:59:59

4. **Configure Output**:
   - The default output directory is `./downloads`
   - You can modify the output directory path if needed

5. **Download**:
   - Click "Download Data" to begin
   - Monitor progress in the progress log
   - Files will be organized as: `downloads/[device_serial]/[date_time_name]/`

## Output Structure

Downloaded data is organized as follows:

```
downloads/
├── SN12345678/
│   ├── 2024-01-15_10-30-00_Water_Analysis/
│   │   ├── measurement.json      # Complete measurement data with computations
│   │   └── data.fcs              # Flow cytometry data (binary)
│   └── 2024-01-15_14-00-00_Sample_Test/
│       ├── measurement.json
│       └── data.fcs
└── SN87654321/
    └── 2024-01-16_09-00-00_Morning_Sample/
        ├── measurement.json
        └── data.fcs
```

## API Requirements

This application uses the BactoCloud Public API v1. Required API permissions:

- `PermDeviceView` - To list and view devices
- `PermDataView` - To query and download measurement data

## Development

### Running Tests

```bash
python -m unittest test_bactocloud_downloader.py -v
```

### Building from Source

**Windows:**
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name BactoCloudDownloader bactocloud_downloader.py
```

**macOS:**
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name BactoCloudDownloader bactocloud_downloader.py
```

## GitHub Actions

This repository includes automated workflows:

- **Tests**: Runs on every push and pull request across Python 3.9-3.12 on Windows, macOS, and Linux
- **Build**: Creates binaries and installers for Windows and macOS on version tags

## Requirements

- Python 3.9 or higher
- tkinter (usually included with Python)
- requests
- tkcalendar

## License

This project is provided as-is for use with BactoCloud API.

## Support

For API-related questions, contact BactoCloud support at support@bactocloud.com

For issues with this application, please open an issue on GitHub.