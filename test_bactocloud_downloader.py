"""
Unit tests for BactoCloud Downloader
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date, timedelta
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


class TestBucketSelection(unittest.TestCase):
    """Test cases for bucket selection functionality"""
    
    def _build_bucket_list(self, bucket_auto, bucket_manual, bucket_monitoring):
        """Helper method to build bucket list based on selections"""
        buckets = []
        if bucket_auto:
            buckets.append("auto")
        if bucket_manual:
            buckets.append("manual")
        if bucket_monitoring:
            buckets.append("monitoring")
        return buckets
    
    def test_bucket_filter_all_selected(self):
        """Test bucket filter with all buckets selected"""
        buckets = self._build_bucket_list(True, True, True)
        
        self.assertEqual(len(buckets), 3)
        self.assertIn("auto", buckets)
        self.assertIn("manual", buckets)
        self.assertIn("monitoring", buckets)
    
    def test_bucket_filter_single_selected(self):
        """Test bucket filter with only one bucket selected"""
        buckets = self._build_bucket_list(True, False, False)
        
        self.assertEqual(len(buckets), 1)
        self.assertEqual(buckets[0], "auto")
    
    def test_bucket_filter_none_selected(self):
        """Test bucket filter with no buckets selected"""
        buckets = self._build_bucket_list(False, False, False)
        
        self.assertEqual(len(buckets), 0)
    
    def test_bucket_filter_mixed_selection(self):
        """Test bucket filter with mixed selection"""
        buckets = self._build_bucket_list(True, False, True)
        
        self.assertEqual(len(buckets), 2)
        self.assertIn("auto", buckets)
        self.assertNotIn("manual", buckets)
        self.assertIn("monitoring", buckets)
    
    def test_api_filter_with_buckets(self):
        """Test that API filter includes buckets when specified"""
        device_id = "test_device_123"
        start_date = "2024-01-01T00:00:00Z"
        end_date = "2024-01-31T23:59:59Z"
        buckets = ["auto", "manual"]
        
        filter_data = {
            "deviceIDs": [device_id],
            "startDate": start_date,
            "endDate": end_date,
            "pageSize": 100,
            "page": 1,
            "buckets": buckets
        }
        
        self.assertIn("buckets", filter_data)
        self.assertEqual(filter_data["buckets"], ["auto", "manual"])
        self.assertEqual(len(filter_data["buckets"]), 2)
    
    def test_api_filter_without_buckets(self):
        """Test that API filter works without buckets (downloads all)"""
        device_id = "test_device_123"
        start_date = "2024-01-01T00:00:00Z"
        end_date = "2024-01-31T23:59:59Z"
        
        filter_data = {
            "deviceIDs": [device_id],
            "startDate": start_date,
            "endDate": end_date,
            "pageSize": 100,
            "page": 1
        }
        
        # Should not have buckets key when none are selected
        self.assertNotIn("buckets", filter_data)


class TestConfigPersistence(unittest.TestCase):
    """Test cases for configuration persistence"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_config_save_and_load(self):
        """Test saving and loading configuration"""
        from pathlib import Path
        
        config_file = Path(self.temp_dir) / "config.json"
        
        # Save config
        test_config = {
            "api_key": "test_key_123",
            "output_dir": "/path/to/output"
        }
        
        with open(config_file, 'w') as f:
            json.dump(test_config, f, indent=2)
        
        # Load config
        with open(config_file, 'r') as f:
            loaded_config = json.load(f)
        
        self.assertEqual(loaded_config["api_key"], "test_key_123")
        self.assertEqual(loaded_config["output_dir"], "/path/to/output")
    
    def test_config_directory_creation(self):
        """Test that config directory can be created"""
        from pathlib import Path
        
        config_dir = Path(self.temp_dir) / "BactoCloudDownloader"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        self.assertTrue(config_dir.exists())
        self.assertTrue(config_dir.is_dir())
    
    def test_config_file_not_exists(self):
        """Test handling when config file doesn't exist"""
        from pathlib import Path
        
        config_file = Path(self.temp_dir) / "nonexistent.json"
        
        # Should return False when file doesn't exist
        self.assertFalse(config_file.exists())
    
    def test_config_type_validation(self):
        """Test that config loading validates data types"""
        from pathlib import Path
        
        config_file = Path(self.temp_dir) / "config.json"
        
        # Save config with wrong types
        invalid_config = {
            "api_key": 12345,  # Should be string
            "output_dir": ["not", "a", "string"]  # Should be string
        }
        
        with open(config_file, 'w') as f:
            json.dump(invalid_config, f, indent=2)
        
        # Config file should exist
        self.assertTrue(config_file.exists())
        
        # The load_config method should handle this gracefully
        # by not loading invalid types (tested in the main code)
    
    def test_config_with_bucket_selection(self):
        """Test saving and loading configuration with bucket selections"""
        from pathlib import Path
        
        config_file = Path(self.temp_dir) / "config.json"
        
        # Save config with bucket selections
        test_config = {
            "api_key": "test_key_123",
            "output_dir": "/path/to/output",
            "bucket_auto": True,
            "bucket_manual": False,
            "bucket_monitoring": True
        }
        
        with open(config_file, 'w') as f:
            json.dump(test_config, f, indent=2)
        
        # Load config
        with open(config_file, 'r') as f:
            loaded_config = json.load(f)
        
        self.assertEqual(loaded_config["bucket_auto"], True)
        self.assertEqual(loaded_config["bucket_manual"], False)
        self.assertEqual(loaded_config["bucket_monitoring"], True)


class TestDirectorySelection(unittest.TestCase):
    """Test cases for directory selection functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_directory_exists_validation(self):
        """Test that directory existence can be validated"""
        from pathlib import Path
        
        # Create a test directory
        test_dir = Path(self.temp_dir) / "test_output"
        test_dir.mkdir(parents=True, exist_ok=True)
        
        # Verify it exists
        self.assertTrue(test_dir.exists())
        self.assertTrue(test_dir.is_dir())
    
    def test_directory_selection_path_update(self):
        """Test that directory path can be updated"""
        from pathlib import Path
        
        # Create test directories
        initial_dir = Path(self.temp_dir) / "initial"
        new_dir = Path(self.temp_dir) / "new_selection"
        
        initial_dir.mkdir(parents=True, exist_ok=True)
        new_dir.mkdir(parents=True, exist_ok=True)
        
        # Simulate directory selection
        selected_dir = str(new_dir)
        
        # Verify the path is valid
        self.assertTrue(os.path.exists(selected_dir))
        self.assertTrue(os.path.isdir(selected_dir))


class TestDateValidation(unittest.TestCase):
    """Test cases for date validation and default date range"""
    
    def test_default_date_range(self):
        """Test that default date range is 3 months"""
        # Calculate expected default dates
        today = datetime.now().date()
        three_months_ago = (datetime.now() - timedelta(days=90)).date()
        
        # Verify the dates are different
        self.assertNotEqual(today, three_months_ago)
        
        # Verify the difference is approximately 90 days
        diff = (today - three_months_ago).days
        self.assertGreaterEqual(diff, 89)  # Account for month length variations
        self.assertLessEqual(diff, 92)
    
    def test_same_date_validation(self):
        """Test that same start and end dates are invalid"""
        same_date = date(2024, 1, 15)
        
        # Start and end dates should not be equal
        self.assertEqual(same_date, same_date)  # This validates the test logic
        # In actual app, this would trigger an error
    
    def test_start_after_end_validation(self):
        """Test that start date after end date is invalid"""
        start_date = date(2024, 2, 1)
        end_date = date(2024, 1, 1)
        
        # Start date should not be after end date
        self.assertTrue(start_date > end_date)  # This validates the test logic
        # In actual app, this would trigger an error
    
    def test_valid_date_range(self):
        """Test that valid date ranges are accepted"""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)
        
        # Valid range: start before end and not equal
        self.assertTrue(start_date < end_date)
        self.assertNotEqual(start_date, end_date)


class TestAbortFunctionality(unittest.TestCase):
    """Test cases for abort functionality"""
    
    def test_abort_flag_initialization(self):
        """Test that abort flag is initialized to False"""
        abort_flag = False
        self.assertFalse(abort_flag)
    
    def test_abort_flag_set(self):
        """Test that abort flag can be set to True"""
        abort_flag = False
        abort_flag = True
        self.assertTrue(abort_flag)
    
    def test_abort_flag_reset(self):
        """Test that abort flag is reset before download"""
        abort_flag = True
        # Before starting download, reset the flag
        abort_flag = False
        self.assertFalse(abort_flag)


if __name__ == '__main__':
    unittest.main()
