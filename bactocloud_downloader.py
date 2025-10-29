#!/usr/bin/env python3
"""
BactoCloud Downloader - GUI application for downloading measurement data from BactoCloud API
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
from datetime import datetime, time, timedelta
import threading
import requests
import json
import os
import platform
from pathlib import Path
from tkcalendar import DateEntry


class BactoCloudDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("BactoCloud Downloader")
        self.root.geometry("800x800")
        
        self.api_key = tk.StringVar(master=root)
        self.output_dir = tk.StringVar(master=root, value=os.path.join(os.getcwd(), "downloads"))
        self.devices = []
        self.selected_devices = []
        self.base_url = "https://api.bactocloud.com"
        self.abort_download = False
        
        # Bucket selection variables
        self.bucket_auto = tk.BooleanVar(master=root, value=True)
        self.bucket_manual = tk.BooleanVar(master=root, value=True)
        self.bucket_monitoring = tk.BooleanVar(master=root, value=True)
        
        self.setup_menu()
        self.setup_ui()
        self.load_config()
        
    def get_config_dir(self):
        """Get the configuration directory based on the OS"""
        system = platform.system()
        
        if system == "Windows":
            # Use AppData/Local on Windows
            base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
            config_dir = Path(base) / "BactoCloudDownloader"
        elif system == "Darwin":  # macOS
            # Use ~/Library/Application Support on macOS
            config_dir = Path.home() / "Library" / "Application Support" / "BactoCloudDownloader"
        else:  # Linux and others
            # Use XDG_CONFIG_HOME or ~/.config on Linux
            base = os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
            config_dir = Path(base) / "BactoCloudDownloader"
        
        # Create directory if it doesn't exist
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir
    
    def get_config_file(self):
        """Get the path to the configuration file"""
        return self.get_config_dir() / "config.json"
    
    def load_config(self):
        """Load saved configuration from file"""
        config_file = self.get_config_file()
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                # Load saved values with type validation
                if "api_key" in config and isinstance(config["api_key"], str):
                    self.api_key.set(config["api_key"])
                if "output_dir" in config and isinstance(config["output_dir"], str):
                    self.output_dir.set(config["output_dir"])
                
                # Load bucket selection preferences
                if "bucket_auto" in config and isinstance(config["bucket_auto"], bool):
                    self.bucket_auto.set(config["bucket_auto"])
                if "bucket_manual" in config and isinstance(config["bucket_manual"], bool):
                    self.bucket_manual.set(config["bucket_manual"])
                if "bucket_monitoring" in config and isinstance(config["bucket_monitoring"], bool):
                    self.bucket_monitoring.set(config["bucket_monitoring"])
                    
                # Only log if progress_text widget exists
                if hasattr(self, 'progress_text'):
                    self.log("Configuration loaded successfully")
            except Exception as e:
                # Only log if progress_text widget exists
                if hasattr(self, 'progress_text'):
                    self.log(f"Warning: Could not load configuration: {str(e)}")
    
    def save_config(self):
        """Save configuration to file"""
        config_file = self.get_config_file()
        
        try:
            config = {
                "api_key": self.api_key.get(),
                "output_dir": self.output_dir.get(),
                "bucket_auto": self.bucket_auto.get(),
                "bucket_manual": self.bucket_manual.get(),
                "bucket_monitoring": self.bucket_monitoring.get()
            }
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
                
            self.log("Configuration saved successfully")
        except Exception as e:
            self.log(f"Warning: Could not save configuration: {str(e)}")
    
    def setup_menu(self):
        """Setup the menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
    
    def show_about(self):
        """Show the About dialog"""
        about_text = (
            "BactoCloud Downloader\n\n"
            "Author: Adrian Shajkofci\n"
            "bNovate Technologies SA\n\n"
            "A tool for downloading measurement data from BactoCloud API"
        )
        messagebox.showinfo("About BactoCloud Downloader", about_text)
    
    def browse_directory(self):
        """Open a directory selector dialog"""
        initial_dir = self.output_dir.get()
        if not os.path.exists(initial_dir):
            initial_dir = os.getcwd()
        
        directory = filedialog.askdirectory(
            title="Select Output Directory",
            initialdir=initial_dir
        )
        
        if directory:
            self.output_dir.set(directory)
            self.save_config()
        
    def setup_ui(self):
        """Setup the user interface"""
        # API Key Section
        api_frame = ttk.LabelFrame(self.root, text="API Configuration", padding=10)
        api_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(api_frame, text="API Key:").grid(row=0, column=0, sticky="w", pady=5)
        api_entry = ttk.Entry(api_frame, textvariable=self.api_key, width=50, show="*")
        api_entry.grid(row=0, column=1, sticky="ew", pady=5, padx=5)
        
        ttk.Button(api_frame, text="Load Devices", command=self.load_devices).grid(
            row=0, column=2, pady=5, padx=5
        )
        
        api_frame.columnconfigure(1, weight=1)
        
        # Device Selection Section
        device_frame = ttk.LabelFrame(self.root, text="Device Selection", padding=10)
        device_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create a frame for the listbox and scrollbar
        list_frame = ttk.Frame(device_frame)
        list_frame.pack(fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.device_listbox = tk.Listbox(
            list_frame, 
            selectmode="multiple", 
            yscrollcommand=scrollbar.set,
            height=10
        )
        self.device_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.device_listbox.yview)
        
        # Bucket Selection Section
        bucket_frame = ttk.LabelFrame(self.root, text="Bucket Selection", padding=10)
        bucket_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(bucket_frame, text="Select measurement types to download:").grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 5)
        )
        
        ttk.Checkbutton(
            bucket_frame, 
            text="Auto (automatic measurements)", 
            variable=self.bucket_auto,
            command=self.save_config
        ).grid(row=1, column=0, sticky="w", padx=5, pady=2)
        
        ttk.Checkbutton(
            bucket_frame, 
            text="Manual (user-initiated measurements)", 
            variable=self.bucket_manual,
            command=self.save_config
        ).grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        ttk.Checkbutton(
            bucket_frame, 
            text="Monitoring (validation/calibration measurements)", 
            variable=self.bucket_monitoring,
            command=self.save_config
        ).grid(row=1, column=2, sticky="w", padx=5, pady=2)
        
        # Date Range Section
        date_frame = ttk.LabelFrame(self.root, text="Date Range", padding=10)
        date_frame.pack(fill="x", padx=10, pady=5)
        
        # Calculate default dates: start = 3 months ago, end = today
        default_end_date = datetime.now().date()
        default_start_date = (datetime.now() - timedelta(days=90)).date()
        
        ttk.Label(date_frame, text="Start Date:").grid(row=0, column=0, sticky="w", pady=5)
        self.start_date = DateEntry(date_frame, width=20, background='darkblue',
                                     foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.start_date.set_date(default_start_date)
        self.start_date.grid(row=0, column=1, sticky="w", pady=5, padx=5)
        
        ttk.Label(date_frame, text="End Date:").grid(row=1, column=0, sticky="w", pady=5)
        self.end_date = DateEntry(date_frame, width=20, background='darkblue',
                                   foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.end_date.set_date(default_end_date)
        self.end_date.grid(row=1, column=1, sticky="w", pady=5, padx=5)
        
        # Output Directory Section
        output_frame = ttk.LabelFrame(self.root, text="Output Directory", padding=10)
        output_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Entry(output_frame, textvariable=self.output_dir, width=50).pack(
            side="left", fill="x", expand=True, padx=5
        )
        
        ttk.Button(output_frame, text="Browse...", command=self.browse_directory).pack(
            side="right", padx=5
        )
        
        # Download and Abort Buttons
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=10)
        
        self.download_btn = ttk.Button(
            button_frame, 
            text="Download Data", 
            command=self.start_download,
            state="disabled"
        )
        self.download_btn.pack(side="left", padx=5)
        
        self.abort_btn = ttk.Button(
            button_frame,
            text="Abort",
            command=self.abort_download_process,
            state="disabled"
        )
        self.abort_btn.pack(side="left", padx=5)
        
        # Progress Section
        progress_frame = ttk.LabelFrame(self.root, text="Progress", padding=10)
        progress_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.progress_text = scrolledtext.ScrolledText(
            progress_frame, 
            height=8, 
            state="disabled",
            wrap="word"
        )
        self.progress_text.pack(fill="both", expand=True)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill="x", pady=5)
        
    def log(self, message):
        """Add a message to the progress log"""
        self.progress_text.config(state="normal")
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.progress_text.insert("end", f"[{timestamp}] {message}\n")
        self.progress_text.see("end")
        self.progress_text.config(state="disabled")
        self.root.update_idletasks()
        
    def get_headers(self):
        """Get API headers with authentication"""
        return {
            "Authorization": f"Bearer {self.api_key.get()}",
            "Content-Type": "application/json"
        }
        
    def load_devices(self):
        """Load devices from the API"""
        if not self.api_key.get():
            messagebox.showerror("Error", "Please enter an API key")
            return
            
        self.log("Loading devices...")
        self.device_listbox.delete(0, tk.END)
        
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/device",
                headers=self.get_headers(),
                params={"no_virtual": "true"}
            )
            
            if response.status_code == 200:
                self.devices = response.json()
                for device in self.devices:
                    serial = device.get("serial_number", "Unknown")
                    name = device.get("name", "Unnamed")
                    self.device_listbox.insert("end", f"{serial} - {name}")
                
                self.log(f"Loaded {len(self.devices)} devices")
                self.download_btn.config(state="normal")
                
                # Save configuration after successful device load
                self.save_config()
            else:
                error_msg = response.json().get("error", "Unknown error")
                self.log(f"Error loading devices: {error_msg}")
                messagebox.showerror("Error", f"Failed to load devices: {error_msg}")
        except Exception as e:
            self.log(f"Exception: {str(e)}")
            messagebox.showerror("Error", f"Failed to connect to API: {str(e)}")
            
    def abort_download_process(self):
        """Abort the ongoing download process"""
        self.abort_download = True
        self.log("Abort requested by user...")
        
    def start_download(self):
        """Start the download process in a background thread"""
        selected_indices = self.device_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Warning", "Please select at least one device")
            return
        
        # Check if at least one bucket is selected
        if not (self.bucket_auto.get() or self.bucket_manual.get() or self.bucket_monitoring.get()):
            messagebox.showwarning("Warning", "Please select at least one bucket type")
        # Validate that start date and end date are different
        start_dt = self.start_date.get_date()
        end_dt = self.end_date.get_date()
        
        if start_dt == end_dt:
            messagebox.showerror("Error", "Start date and end date cannot be the same. Please select a date range.")
            return
        
        if start_dt > end_dt:
            messagebox.showerror("Error", "Start date cannot be after end date.")
            return
            
        self.selected_devices = [self.devices[i] for i in selected_indices]
        
        # Reset abort flag
        self.abort_download = False
        
        # Disable download button and enable abort button during download
        self.download_btn.config(state="disabled")
        self.abort_btn.config(state="normal")
        self.progress_bar.start()
        
        # Run download in background thread
        thread = threading.Thread(target=self.download_data, daemon=True)
        thread.start()
        
    def download_data(self):
        """Download data for selected devices and date range"""
        try:
            # Create start and end datetime objects
            start_datetime = datetime.combine(self.start_date.get_date(), time(0, 0, 0))
            end_datetime = datetime.combine(self.end_date.get_date(), time(23, 59, 59))
            
            self.log(f"Date range: {start_datetime} to {end_datetime}")
            
            total_downloaded = 0
            
            for device in self.selected_devices:
                # Check if abort was requested
                if self.abort_download:
                    self.log("\n=== Download Aborted by User ===")
                    messagebox.showinfo("Aborted", f"Download aborted. {total_downloaded} measurements were downloaded before abort.")
                    break
                
                device_id = device.get("id")
                device_serial = device.get("serial_number", "Unknown")
                
                self.log(f"\nProcessing device: {device_serial}")
                
                # Build bucket list based on selection
                buckets = []
                if self.bucket_auto.get():
                    buckets.append("auto")
                if self.bucket_manual.get():
                    buckets.append("manual")
                if self.bucket_monitoring.get():
                    buckets.append("monitoring")
                
                # Log selected buckets
                self.log(f"  Buckets: {', '.join(buckets)}")
                
                # Prepare filter for data query
                filter_data = {
                    "device_ids": [device_id],
                    "start_date": start_datetime.isoformat() + "Z",
                    "end_date": end_datetime.isoformat() + "Z",
                    "page_size": 10000,
                    "with_computations": True,
                    "page": 0
                }
                
                # Add buckets filter if any are selected
                filter_data["buckets"] = buckets
                
                self.log("filtering data...")
                self.log(f"  Filter: {filter_data}")

                # Get data list
                response = requests.post(
                    f"{self.base_url}/api/v1/data/list",
                    headers=self.get_headers(),
                    json=filter_data
                )
                
                if response.status_code != 200:
                    error_msg = response.json().get("error", "Unknown error")
                    self.log(f"Error fetching data: {error_msg}")
                    continue
                
                result = response.json()
                data_list = result.get("data", [])
                if not data_list:
                    self.log("  No measurements found for this device in the specified date range and buckets.")
                    continue
                self.log(f"Found {len(data_list)} measurements")
                
                # Process each measurement
                for data_item in data_list:
                    # Check if abort was requested
                    if self.abort_download:
                        self.log("\n=== Download Aborted by User ===")
                        messagebox.showinfo("Aborted", f"Download aborted. {total_downloaded} measurements were downloaded before abort.")
                        return
                    
                    try:
                        self.process_measurement(data_item, device_serial)
                        total_downloaded += 1
                    except Exception as e:
                        self.log(f"Error processing measurement: {str(e)}")
            
            # Only show completion if not aborted
            if not self.abort_download:
                self.log(f"\n=== Download Complete ===")
                self.log(f"Total measurements downloaded: {total_downloaded}")
                messagebox.showinfo("Success", f"Downloaded {total_downloaded} measurements")
            
        except Exception as e:
            self.log(f"Error during download: {str(e)}")
            messagebox.showerror("Error", str(e))
        finally:
            self.progress_bar.stop()
            self.download_btn.config(state="normal")
            self.abort_btn.config(state="disabled")
            
    def process_measurement(self, data_item, device_serial):
        """Process a single measurement - download files and save JSON"""
        # Extract measurement info
        data_id = data_item.get("_id")
        timestamp = data_item.get("timestamp", "")
        name = data_item.get("name", "unnamed")
        
        # Parse timestamp for folder name and file prefix
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            date_str = dt.strftime("%Y-%m-%d_%H-%M-%S")
        except (ValueError, AttributeError, TypeError):
            date_str = "unknown_date"
        
        # Sanitize name for filesystem
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '_', '-')).strip()
        safe_name = safe_name or "unnamed"
        
        # Create folder structure: /device_serial/measurement_date_measurement_name/
        folder_name = f"{date_str}_{safe_name}"
        output_path = Path(self.output_dir.get()) / device_serial / folder_name
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Create file prefix for all files
        file_prefix = f"{date_str}_{safe_name}"
        
        self.log(f"  Processing: {folder_name}")
        
        # Save measurement data as JSON
        json_path = output_path / f"{file_prefix}_result.json"
        with open(json_path, 'w') as f:
            json.dump(data_item, f, indent=2)
        
        # Download files if available
        files = data_item.get("files", {})
        if files:
            # File type mapping: "10" = PNG, "20" = FCS, "30" = CSV
            file_types = {
                "10": ("png", "summary"),
                "20": ("fcs", "data"),
                "30": ("csv", "diagnostics")
            }
            
            for file_code, file_id in files.items():
                if file_code in file_types:
                    extension, file_type = file_types[file_code]
                    try:
                        file_response = requests.get(
                            f"{self.base_url}/api/v1/data/file/{file_id}",
                            headers=self.get_headers()
                        )
                        
                        if file_response.status_code == 200:
                            file_path = output_path / f"{file_prefix}_{file_type}.{extension}"
                            with open(file_path, 'wb') as f:
                                f.write(file_response.content)
                            self.log(f"    ✓ Downloaded {extension.upper()} file ({len(file_response.content)} bytes)")
                        else:
                            self.log(f"    ⚠ {extension.upper()} file not available (status: {file_response.status_code})")
                    except Exception as e:
                        self.log(f"    ⚠ Error downloading {extension.upper()}: {str(e)}")
        else:
            self.log(f"    ⚠ No files available for this measurement")


def main():
    root = tk.Tk()
    app = BactoCloudDownloader(root)
    root.mainloop()


if __name__ == "__main__":
    main()
