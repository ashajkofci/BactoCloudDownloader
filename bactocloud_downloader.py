#!/usr/bin/env python3
"""
BactoCloud Downloader - GUI application for downloading measurement data from BactoCloud API
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime, time
import threading
import requests
import json
import os
from pathlib import Path
from tkcalendar import DateEntry


class BactoCloudDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("BactoCloud Downloader")
        self.root.geometry("800x700")
        
        self.api_key = tk.StringVar(master=root)
        self.output_dir = tk.StringVar(master=root, value=os.path.join(os.getcwd(), "downloads"))
        self.devices = []
        self.selected_devices = []
        self.base_url = "https://api.bactocloud.com"
        
        self.setup_ui()
        
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
        
        # Date Range Section
        date_frame = ttk.LabelFrame(self.root, text="Date Range", padding=10)
        date_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(date_frame, text="Start Date:").grid(row=0, column=0, sticky="w", pady=5)
        self.start_date = DateEntry(date_frame, width=20, background='darkblue',
                                     foreground='white', borderwidth=2)
        self.start_date.grid(row=0, column=1, sticky="w", pady=5, padx=5)
        
        ttk.Label(date_frame, text="End Date:").grid(row=1, column=0, sticky="w", pady=5)
        self.end_date = DateEntry(date_frame, width=20, background='darkblue',
                                   foreground='white', borderwidth=2)
        self.end_date.grid(row=1, column=1, sticky="w", pady=5, padx=5)
        
        # Output Directory Section
        output_frame = ttk.LabelFrame(self.root, text="Output Directory", padding=10)
        output_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Entry(output_frame, textvariable=self.output_dir, width=50).pack(
            side="left", fill="x", expand=True, padx=5
        )
        
        # Download Button
        self.download_btn = ttk.Button(
            self.root, 
            text="Download Data", 
            command=self.start_download,
            state="disabled"
        )
        self.download_btn.pack(pady=10)
        
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
            else:
                error_msg = response.json().get("error", "Unknown error")
                self.log(f"Error loading devices: {error_msg}")
                messagebox.showerror("Error", f"Failed to load devices: {error_msg}")
        except Exception as e:
            self.log(f"Exception: {str(e)}")
            messagebox.showerror("Error", f"Failed to connect to API: {str(e)}")
            
    def start_download(self):
        """Start the download process in a background thread"""
        selected_indices = self.device_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Warning", "Please select at least one device")
            return
            
        self.selected_devices = [self.devices[i] for i in selected_indices]
        
        # Disable download button during download
        self.download_btn.config(state="disabled")
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
                device_id = device.get("_id")
                device_serial = device.get("serial_number", "Unknown")
                
                self.log(f"\nProcessing device: {device_serial}")
                
                # Prepare filter for data query
                filter_data = {
                    "deviceIDs": [device_id],
                    "startDate": start_datetime.isoformat() + "Z",
                    "endDate": end_datetime.isoformat() + "Z",
                    "pageSize": 100,
                    "page": 1
                }
                
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
                
                self.log(f"Found {len(data_list)} measurements")
                
                # Process each measurement
                for data_item in data_list:
                    try:
                        self.process_measurement(data_item, device_serial)
                        total_downloaded += 1
                    except Exception as e:
                        self.log(f"Error processing measurement: {str(e)}")
                        
            self.log(f"\n=== Download Complete ===")
            self.log(f"Total measurements downloaded: {total_downloaded}")
            messagebox.showinfo("Success", f"Downloaded {total_downloaded} measurements")
            
        except Exception as e:
            self.log(f"Error during download: {str(e)}")
            messagebox.showerror("Error", str(e))
        finally:
            self.progress_bar.stop()
            self.download_btn.config(state="normal")
            
    def process_measurement(self, data_item, device_serial):
        """Process a single measurement - download FCS and save JSON"""
        # Extract measurement info
        data_id = data_item.get("_id")
        timestamp = data_item.get("timestamp", "")
        name = data_item.get("name", "unnamed")
        
        # Parse timestamp for folder name
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
        
        self.log(f"  Processing: {folder_name}")
        
        # Save measurement data as JSON
        json_path = output_path / "measurement.json"
        with open(json_path, 'w') as f:
            json.dump(data_item, f, indent=2)
        
        # Download FCS file if available
        file_id = data_item.get("file_id")
        if file_id:
            try:
                fcs_response = requests.get(
                    f"{self.base_url}/api/v1/data/file/{file_id}",
                    headers=self.get_headers()
                )
                
                if fcs_response.status_code == 200:
                    fcs_path = output_path / "data.fcs"
                    with open(fcs_path, 'wb') as f:
                        f.write(fcs_response.content)
                    self.log(f"    ✓ Downloaded FCS file ({len(fcs_response.content)} bytes)")
                else:
                    self.log(f"    ⚠ FCS file not available (status: {fcs_response.status_code})")
            except Exception as e:
                self.log(f"    ⚠ Error downloading FCS: {str(e)}")


def main():
    root = tk.Tk()
    app = BactoCloudDownloader(root)
    root.mainloop()


if __name__ == "__main__":
    main()
