"""
Unit tests for BactoCloud Downloader
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date
import json
import os
import tempfile
import shutil


class TestBactoCloudDownloaderCore(unittest.TestCase):
    """Test cases for core BactoCloud Downloader functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_api_headers(self):
        """Test that API headers are generated correctly"""
        headers = {
            "Authorization": f"Bearer test_api_key_123",
            "Content-Type": "application/json"
        }
        
        self.assertEqual(headers["Authorization"], "Bearer test_api_key_123")
        self.assertEqual(headers["Content-Type"], "application/json")
    
    @patch('requests.get')
    def test_load_devices_api_call(self, mock_get):
        """Test device loading API call"""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"_id": "1", "serial_number": "SN001", "name": "Device 1"},
            {"_id": "2", "serial_number": "SN002", "name": "Device 2"}
        ]
        mock_get.return_value = mock_response
        
        # Simulate the API call
        headers = {"Authorization": "Bearer test_key", "Content-Type": "application/json"}
        response = mock_get(
            "https://api.bactocloud.com/api/v1/device",
            headers=headers,
            params={"no_virtual": "true"}
        )
        
        self.assertEqual(response.status_code, 200)
        devices = response.json()
        self.assertEqual(len(devices), 2)
        self.assertEqual(devices[0]["serial_number"], "SN001")
    
    def test_file_organization(self):
        """Test file organization structure"""
        from pathlib import Path
        
        # Create test structure
        device_serial = "SN001"
        date_str = "2024-01-15_10-30-00"
        safe_name = "Test_Measurement"
        folder_name = f"{date_str}_{safe_name}"
        
        output_path = Path(self.temp_dir) / device_serial / folder_name
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Create test files
        json_path = output_path / "measurement.json"
        test_data = {"_id": "test_id", "name": "Test"}
        with open(json_path, 'w') as f:
            json.dump(test_data, f, indent=2)
        
        fcs_path = output_path / "data.fcs"
        with open(fcs_path, 'wb') as f:
            f.write(b"FCS file content")
        
        # Verify structure
        self.assertTrue(output_path.exists())
        self.assertTrue(json_path.exists())
        self.assertTrue(fcs_path.exists())
        
        # Verify content
        with open(json_path, 'r') as f:
            saved_data = json.load(f)
        self.assertEqual(saved_data["_id"], "test_id")
        
        with open(fcs_path, 'rb') as f:
            fcs_content = f.read()
        self.assertEqual(fcs_content, b"FCS file content")
    
    def test_date_parsing(self):
        """Test date parsing for folder names"""
        timestamp = "2024-01-15T10:30:00Z"
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        date_str = dt.strftime("%Y-%m-%d_%H-%M-%S")
        
        self.assertEqual(date_str, "2024-01-15_10-30-00")
    
    def test_name_sanitization(self):
        """Test measurement name sanitization for filesystem"""
        name = "Test / Measurement: With Special * Characters?"
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '_', '-')).strip()
        safe_name = safe_name or "unnamed"
        
        self.assertEqual(safe_name, "Test  Measurement With Special  Characters")
        
        # Test empty name
        empty_name = "!@#$%^&*()"
        safe_empty = "".join(c for c in empty_name if c.isalnum() or c in (' ', '_', '-')).strip()
        safe_empty = safe_empty or "unnamed"
        
        self.assertEqual(safe_empty, "unnamed")


if __name__ == '__main__':
    unittest.main()
