#!/usr/bin/env python3
"""Test script for webdriver-manager integration."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'job_instruction_downloader'))

from job_instruction_downloader.src.core.downloader import DocumentDownloader
from job_instruction_downloader.src.utils.config import ConfigManager

def test_webdriver_manager_integration():
    """Test webdriver-manager integration with DocumentDownloader."""
    print("Testing webdriver-manager integration...")
    
    try:
        config_manager = ConfigManager()
        config = config_manager.load_config()
        downloader = DocumentDownloader(config)
        
        print("✅ DocumentDownloader initialized successfully")
        
        result = downloader.setup_driver()
        print(f"WebDriver setup result: {result}")
        
        if downloader.driver:
            print("✅ WebDriver initialized successfully with webdriver-manager")
            print(f"WebDriver session ID: {downloader.driver.session_id}")
            
            downloader.driver.get("about:blank")
            print("✅ WebDriver can navigate to pages")
            
            downloader.cleanup()
            print("✅ WebDriver cleanup completed")
        else:
            print("❌ WebDriver initialization failed")
            return False
            
    except Exception as e:
        print(f"❌ Error during webdriver-manager integration test: {e}")
        return False
    
    print("\n🎉 webdriver-manager integration test completed successfully!")
    return True

if __name__ == "__main__":
    success = test_webdriver_manager_integration()
    sys.exit(0 if success else 1)
