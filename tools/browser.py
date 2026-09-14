"""
JARVIS Tools - Browser Automation
Selenium Webdriver YouTube auto-play & Google search
"""
import time
import urllib.parse
from typing import Optional

_driver = None

def get_driver():
    global _driver
    if _driver is None:
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options
            from webdriver_manager.chrome import ChromeDriverManager
            
            options = Options()
            options.add_argument("--start-maximized")
            options.add_argument("--disable-notifications")
            options.add_experimental_option("detach", True)
            
            service = Service(ChromeDriverManager().install())
            _driver = webdriver.Chrome(service=service, options=options)
        except Exception as e:
            print(f"[Browser Init Error]: {e}")
            _driver = None
    return _driver

def search_web(query: str) -> str:
    if not query:
        return "No search query provided."
    
    driver = get_driver()
    if driver:
        try:
            url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
            driver.get(url)
            time.sleep(1)
            driver.execute_script("window.scrollBy(0, 300);")
            return f"Searched Google for '{query}', sir."
        except Exception as e:
            print(f"[Browser Search Error]: {e}")
    
    import webbrowser
    webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(query)}")
    return f"Opened Google search for '{query}', sir."

def play_youtube(query: str = "") -> str:
    clean_q = (query or "").strip()
    import webbrowser
    if not clean_q:
        webbrowser.open("https://www.youtube.com")
        return "Opening YouTube, sir."

    encoded = urllib.parse.quote(clean_q)
    webbrowser.open(f"https://www.youtube.com/results?search_query={encoded}")
    return f"Opening '{clean_q}' on YouTube, sir."

def close_browser() -> str:
    global _driver
    if _driver:
        try:
            _driver.quit()
            _driver = None
            return "Browser closed, sir."
        except Exception as e:
            return f"Error closing browser: {e}"
    return "No active browser session."

def browser_navigate(url: str) -> str:
    """Navigates the automated browser to a specific URL."""
    if not url:
        return "No URL provided, sir."
    clean_url = url if url.startswith("http") else f"https://{url}"
    driver = get_driver()
    if driver:
        try:
            driver.get(clean_url)
            return f"Navigated to {clean_url}, sir."
        except Exception as e:
            return f"Navigation error: {e}"
    import webbrowser
    webbrowser.open(clean_url)
    return f"Opened {clean_url} in default browser, sir."

def browser_click_element(selector_or_text: str) -> str:
    """Clicks a button, link, or element by CSS selector, XPath, or inner text."""
    driver = get_driver()
    if not driver:
        return "No active browser session to click elements in, sir."
    try:
        from selenium.webdriver.common.by import By
        # Try finding by text or xpath
        elems = driver.find_elements(By.XPATH, f"//*[contains(text(), '{selector_or_text}')]")
        if not elems:
            elems = driver.find_elements(By.CSS_SELECTOR, selector_or_text)
        if elems:
            elems[0].click()
            return f"Clicked element matching '{selector_or_text}', sir."
        return f"Could not find element '{selector_or_text}' on page."
    except Exception as e:
        return f"Click error: {e}"

def browser_type_text(selector: str, text: str) -> str:
    """Types text into an input field or text area identified by CSS selector."""
    driver = get_driver()
    if not driver:
        return "No active browser session to type in, sir."
    try:
        from selenium.webdriver.common.by import By
        elem = driver.find_element(By.CSS_SELECTOR, selector)
        elem.clear()
        elem.send_keys(text)
        return f"Typed text into '{selector}', sir."
    except Exception as e:
        return f"Typing error: {e}"

def browser_capture_page(filename: str = "web_capture.png") -> str:
    """Captures a screenshot of the active browser page into the sandbox directory."""
    driver = get_driver()
    if not driver:
        return "No active browser session to capture, sir."
    try:
        from pathlib import Path
        import config
        sandbox = Path(config.SANDBOX_DIR).resolve()
        sandbox.mkdir(parents=True, exist_ok=True)
        out_path = sandbox / filename
        driver.save_screenshot(str(out_path))
        return f"Browser screenshot captured to `{out_path}`, sir."
    except Exception as e:
        return f"Capture error: {e}"

def browser_extract_text() -> str:
    """Extracts visible text content from the current web page."""
    driver = get_driver()
    if not driver:
        return "No active browser session to extract text from, sir."
    try:
        from selenium.webdriver.common.by import By
        body = driver.find_element(By.TAG_NAME, "body")
        text = body.text.strip()
        preview = text[:1500] + ("\n...[Truncated]" if len(text) > 1500 else "")
        return f"Page Content Excerpt:\n\n{preview}"
    except Exception as e:
        return f"Text extraction error: {e}"


if __name__ == "__main__":
    print(search_web("iron man jarvis"))
    time.sleep(2)
    print(play_youtube("ac dc thunderstruck"))