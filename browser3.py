import subprocess
import time
import os
import tempfile
import json
from typing import Optional, List, Dict

class PowerShellSelenium:
    """
    A Python class that uses PowerShell to automate browsers
    with a Selenium-like API
    """
    
    def __init__(self, browser='edge', headless=False):
        self.browser = browser
        self.headless = headless
        self.session_id = None
        self._driver_started = False
        
    def _start_driver(self):
        """Start the WebDriver service"""
        if self._driver_started:
            return
            
        ps_script = f'''
        # Check if driver is running
        $driverProcess = Get-Process -Name "*driver" -ErrorAction SilentlyContinue
        if (-not $driverProcess) {{
            if ("{self.browser}" -eq "edge") {{
                Start-Process msedgedriver -NoNewWindow
            }} elseif ("{self.browser}" -eq "chrome") {{
                Start-Process chromedriver -NoNewWindow
            }}
            Start-Sleep -Seconds 3
        }}
        '''
        subprocess.run(['powershell', '-Command', ps_script], capture_output=True)
        self._driver_started = True
        time.sleep(2)
    
    def get(self, url: str):
        """Navigate to a URL"""
        self._start_driver()
        
        ps_script = f'''
        # Create new session
        $caps = @{{
            "capabilities" = @{{
                "alwaysMatch" = @{{
                    "browserName" = "{self.browser}"
                }}
            }}
        }} | ConvertTo-Json -Depth 10
        
        $response = Invoke-RestMethod -Method Post `
            -Uri "http://localhost:9515/session" `
            -Body $caps -ContentType "application/json"
        
        $sessionId = $response.value.sessionId
        
        # Navigate
        $navBody = @{{"url" = "{url}"}} | ConvertTo-Json
        Invoke-RestMethod -Method Post `
            -Uri "http://localhost:9515/session/$sessionId/url" `
            -Body $navBody -ContentType "application/json"
        
        # Wait for page to load
        Start-Sleep -Seconds 2
        
        $sessionId
        '''
        
        result = subprocess.run(['powershell', '-Command', ps_script], 
                              capture_output=True, text=True)
        self.session_id = result.stdout.strip()
        return self.session_id
    
    def find_element(self, by: str, value: str):
        """Find an element on the page"""
        if not self.session_id:
            raise Exception("No session. Call get() first.")
            
        strategies = {
            'id': 'css selector',
            'class': 'css selector',
            'xpath': 'xpath',
            'css': 'css selector',
            'tag': 'tag name'
        }
        
        ps_script = f'''
        $element = Invoke-RestMethod -Method Post `
            -Uri "http://localhost:9515/session/{self.session_id}/element" `
            -Body @{{"using" = "{strategies.get(by, 'css selector')}", "value" = "{value}"}} `
            -ContentType "application/json"
        $element.value.ELEMENT
        '''
        
        result = subprocess.run(['powershell', '-Command', ps_script], 
                              capture_output=True, text=True)
        return result.stdout.strip()
    
    def click(self, element_id: str):
        """Click an element"""
        if not self.session_id:
            raise Exception("No session. Call get() first.")
            
        ps_script = f'''
        Invoke-RestMethod -Method Post `
            -Uri "http://localhost:9515/session/{self.session_id}/element/{element_id}/click"
        '''
        subprocess.run(['powershell', '-Command', ps_script], check=True)
    
    def send_keys(self, element_id: str, text: str):
        """Send text to an element"""
        if not self.session_id:
            raise Exception("No session. Call get() first.")
            
        ps_script = f'''
        $body = @{{"text" = "{text}"}} | ConvertTo-Json
        Invoke-RestMethod -Method Post `
            -Uri "http://localhost:9515/session/{self.session_id}/element/{element_id}/value" `
            -Body $body -ContentType "application/json"
        '''
        subprocess.run(['powershell', '-Command', ps_script], check=True)
    
    def get_page_source(self) -> str:
        """Get the page source"""
        if not self.session_id:
            raise Exception("No session. Call get() first.")
            
        ps_script = f'''
        $response = Invoke-RestMethod -Method Get `
            -Uri "http://localhost:9515/session/{self.session_id}/source"
        $response.value
        '''
        
        result = subprocess.run(['powershell', '-Command', ps_script], 
                              capture_output=True, text=True)
        return result.stdout
    
    def execute_script(self, script: str) -> str:
        """Execute JavaScript"""
        if not self.session_id:
            raise Exception("No session. Call get() first.")
            
        ps_script = f'''
        $body = @{{"script" = "{script.replace('"', '`"')}", "args" = @()}} | ConvertTo-Json
        $response = Invoke-RestMethod -Method Post `
            -Uri "http://localhost:9515/session/{self.session_id}/execute/sync" `
            -Body $body -ContentType "application/json"
        $response.value
        '''
        
        result = subprocess.run(['powershell', '-Command', ps_script], 
                              capture_output=True, text=True)
        return result.stdout
    
    def close(self):
        """Close the browser session"""
        if self.session_id:
            ps_script = f'''
            Invoke-RestMethod -Method Delete -Uri "http://localhost:9515/session/{self.session_id}"
            '''
            subprocess.run(['powershell', '-Command', ps_script], check=True)
            self.session_id = None
            self._driver_started = False

# Example: Complete automation workflow
if __name__ == "__main__":
    # This requires WebDriver to be installed
    print("Advanced Browser Automation with PowerShell")
    print("=" * 50)
    
    browser = PowerShellSelenium(browser='edge')
    
    try:
        print("1. Opening Google...")
        browser.get("https://www.google.com")
        time.sleep(2)
        
        print("2. Finding search box...")
        # Note: This is a simplified example - you'd need the actual element ID
        search_box = browser.find_element('css', 'input[name="q"]')
        print(f"Found element: {search_box}")
        
        print("3. Typing search query...")
        browser.send_keys(search_box, "Python programming")
        time.sleep(1)
        
        print("4. Getting page info...")
        title = browser.execute_script("return document.title")
        print(f"Page title: {title}")
        
        print("5. Closing browser...")
        browser.close()
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure the appropriate WebDriver is installed and in PATH")
        print("For Edge: https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/")
        print("For Chrome: https://chromedriver.chromium.org/")