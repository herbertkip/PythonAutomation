import subprocess
import json
import time
import os
from pathlib import Path

class PowerShellWebDriver:
    def __init__(self, browser="edge", headless=False):
        """
        Initialize browser automation using WebDriver
        browser: "edge" or "chrome"
        """
        self.browser = browser
        self.headless = headless
        self.driver_process = None
        
    def _get_driver_command(self):
        """Get the appropriate WebDriver command"""
        if self.browser.lower() == "edge":
            return "Start-Process msedgedriver -NoNewWindow"
        else:  # chrome
            return "Start-Process chromedriver -NoNewWindow"
    
    def open_url_with_webdriver(self, url):
        """
        Open URL using WebDriver with PowerShell
        """
        ps_script = f'''
        # Import required assemblies
        Add-Type -AssemblyName System.Net.Http
        
        # Start WebDriver
        $driverProcess = {self._get_driver_command()}
        Start-Sleep -Seconds 2
        
        # Create a session with WebDriver
        $session = Invoke-RestMethod -Method Post -Uri "http://localhost:9515/session" `
            -Body '{{"capabilities": {{"alwaysMatch": {{"browserName": "{self.browser}"}}}}}}' `
            -ContentType "application/json"
        
        $sessionId = $session.value.sessionId
        
        # Navigate to URL
        $navBody = @{{"url" = "{url}"}} | ConvertTo-Json
        Invoke-RestMethod -Method Post -Uri "http://localhost:9515/session/$sessionId/url" `
            -Body $navBody -ContentType "application/json"
        
        # Return session ID for further operations
        $sessionId
        '''
        
        result = subprocess.run(['powershell', '-Command', ps_script], 
                              capture_output=True, text=True)
        return result.stdout.strip()
    
    def execute_js(self, session_id, js_code):
        """Execute JavaScript code in the browser"""
        ps_script = f'''
        $jsBody = @{{"script" = "{js_code.replace('"', '`"')}", "args" = @()}} | ConvertTo-Json
        $result = Invoke-RestMethod -Method Post `
            -Uri "http://localhost:9515/session/{session_id}/execute/sync" `
            -Body $jsBody -ContentType "application/json"
        $result.value
        '''
        
        result = subprocess.run(['powershell', '-Command', ps_script], 
                              capture_output=True, text=True)
        return result.stdout
    
    def close_session(self, session_id):
        """Close the WebDriver session"""
        ps_script = f'''
        Invoke-RestMethod -Method Delete -Uri "http://localhost:9515/session/{session_id}"
        '''
        subprocess.run(['powershell', '-Command', ps_script], check=True)

# Example usage with modern browsers
if __name__ == "__main__":
    print("Option 1: Using Internet Explorer (legacy)")
    ie_browser = PowerShellBrowser()
    ie_browser.open_url("https://www.python.org")
    time.sleep(3)
    
    print("\nOption 2: Using WebDriver (requires drivers installed)")
    print("Note: You need to install WebDriver for Edge or Chrome")
    web_browser = PowerShellWebDriver(browser="edge")
    
    # This requires msedgedriver.exe in PATH or current directory
    # Download from: https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/
    try:
        session_id = web_browser.open_url_with_webdriver("https://www.python.org")
        print(f"Session ID: {session_id}")
        time.sleep(3)
        
        # Execute JavaScript to get page info
        title = web_browser.execute_js(session_id, "return document.title")
        print(f"Page title: {title}")
        
        # Close session
        web_browser.close_session(session_id)
    except Exception as e:
        print(f"WebDriver method failed: {e}")
        print("Make sure WebDriver is installed and in PATH")