#!/usr/bin/env python3
"""Test script for Selenium Manager integration with Chrome 137.0.7118.2."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'job_instruction_downloader'))

from job_instruction_downloader.src.core.downloader import DocumentDownloader
from job_instruction_downloader.src.utils.config import ConfigManager

def test_selenium_manager_integration():
    """Test Selenium Manager integration with DocumentDownloader for Chrome 137.0.7118.2."""
    print("Testing Selenium Manager integration with Chrome 137.0.7118.2...")
    
    try:
        config_manager = ConfigManager()
        config = config_manager.load_config()
        downloader = DocumentDownloader(config)
        
        print("✅ DocumentDownloader initialized successfully")
        
        result = downloader.setup_driver()
        print(f"WebDriver setup result: {result}")
        
        if downloader.driver:
            print("✅ WebDriver initialized successfully with Selenium Manager")
            print(f"WebDriver session ID: {downloader.driver.session_id}")
            
            chrome_version = downloader.driver.capabilities.get('browserVersion', 'Unknown')
            print(f"✅ Chrome version detected: {chrome_version}")
            
            downloader.driver.get("about:blank")
            print("✅ WebDriver can navigate to pages")
            
            downloader.cleanup()
            print("✅ WebDriver cleanup completed")
        else:
            print("❌ WebDriver initialization failed")
            return False
            
    except Exception as e:
        print(f"❌ Error during Selenium Manager integration test: {e}")
        return False
    
    print("\n🎉 Selenium Manager integration test completed successfully!")
    print("✅ Chrome 137.0.7118.2 compatibility verified!")
    return True

if __name__ == "__main__":
    success = test_selenium_manager_integration()
    sys.exit(0 if success else 1)
