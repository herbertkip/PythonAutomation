import subprocess
import time
import sys

class PowerShellBrowser:
    def __init__(self, headless=False):
        self.headless = headless
        
    def open_url(self, url):
        """Open a URL in Internet Explorer using PowerShell"""
        ps_script = f'''
        $ie = New-Object -ComObject InternetExplorer.Application
        $ie.Visible = {str(not self.headless).lower()}
        $ie.Navigate("{url}")
        while ($ie.Busy -eq $true -or $ie.ReadyState -ne 4) {{
            Start-Sleep -Milliseconds 100
        }}
        $ie
        '''
        result = subprocess.run(['powershell', '-Command', ps_script], 
                              capture_output=True, text=True)
        return result.stdout
    
    def get_page_title(self):
        """Get the current page title"""
        ps_script = '''
        $ie = New-Object -ComObject InternetExplorer.Application
        $ie.Visible = $true
        Start-Sleep -Seconds 2
        $ie.Document.Title
        '''
        result = subprocess.run(['powershell', '-Command', ps_script], 
                              capture_output=True, text=True)
        return result.stdout.strip()
    
    def get_page_source(self):
        """Get the current page HTML source"""
        ps_script = '''
        $ie = New-Object -ComObject InternetExplorer.Application
        $ie.Visible = $true
        Start-Sleep -Seconds 2
        $ie.Document.documentElement.outerHTML
        '''
        result = subprocess.run(['powershell', '-Command', ps_script], 
                              capture_output=True, text=True)
        return result.stdout
    
    def click_element(self, element_id):
        """Click an element by ID"""
        ps_script = f'''
        $ie = New-Object -ComObject InternetExplorer.Application
        $ie.Visible = $true
        Start-Sleep -Seconds 2
        $element = $ie.Document.getElementById("{element_id}")
        if ($element) {{
            $element.click()
        }}
        '''
        subprocess.run(['powershell', '-Command', ps_script], check=True)
    
    def fill_input(self, element_id, value):
        """Fill an input field by ID"""
        ps_script = f'''
        $ie = New-Object -ComObject InternetExplorer.Application
        $ie.Visible = $true
        Start-Sleep -Seconds 2
        $element = $ie.Document.getElementById("{element_id}")
        if ($element) {{
            $element.value = "{value}"
        }}
        '''
        subprocess.run(['powershell', '-Command', ps_script], check=True)

# Example usage
if __name__ == "__main__":
    browser = PowerShellBrowser(headless=False)
    
    # Open a website
    print("Opening Google...")
    browser.open_url("https://www.google.com")
    time.sleep(3)
    
    # Get page title
    title = browser.get_page_title()
    print(f"Page Title: {title}")
    
    # Get page source (first 500 chars)
    source = browser.get_page_source()
    print(f"Page Source (first 500 chars): {source[:500]}...")