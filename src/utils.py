"""
Utility functions for Playo booking automation.
Contains browser setup, mouse cursor injection, and other helper functions.
"""

import asyncio
from typing import Dict


async def setup_browser_context(playwright, user_data_dir: str, geolocation: Dict):
    """
    Setup and return a browser context with proper configuration.
    
    Args:
        playwright: Playwright instance
        user_data_dir: Directory for persistent user data
        geolocation: Dictionary with latitude and longitude
        
    Returns:
        Browser context
    """
    context = await playwright.chromium.launch_persistent_context(
        user_data_dir,
        headless=False,
        geolocation=geolocation,
        permissions=["geolocation"]
    )
    
    print(f"✅ Browser context created with user data dir: {user_data_dir}")
    print(f"✅ Geolocation set to: {geolocation}")
    
    return context


async def add_mouse_cursor(page):
    """
    Add a visible red mouse cursor for debugging purposes.
    
    Args:
        page: Playwright page object
    """
    await page.add_init_script("""
(() => {
  const style = document.createElement('style');
  style.innerHTML = `
    .__playwright-mouse-pointer {
      pointer-events: none;
      position: fixed;
      z-index: 9999999999 !important;
      left: 0;
      top: 0;
      width: 20px;
      height: 20px;
      background: red;
      border: 2px solid white;
      border-radius: 10px;
      margin-left: -10px;
      margin-top: -10px;
      transition: background 0.2s, border 0.2s;
      opacity: 0.8;
    }
  `;
  document.head.appendChild(style);
  const pointer = document.createElement('div');
  pointer.classList.add('__playwright-mouse-pointer');
  document.body.appendChild(pointer);
  document.addEventListener('mousemove', event => {
    pointer.style.left = event.pageX + 'px';
    pointer.style.top = event.pageY + 'px';
  }, true);
})();
""")
    print("✅ Mouse cursor injected for visual debugging")


async def safe_click(page, element, description: str = "element", timeout: int = 5000):
    """
    Perform a safe click with both element.click and mouse.click fallback.
    
    Args:
        page: Playwright page object
        element: Element to click
        description: Description for logging
        timeout: Click timeout in milliseconds
        
    Returns:
        bool: True if click successful, False otherwise
    """
    try:
        box = await element.bounding_box()
        if not box:
            print(f"❌ Could not get bounding box for {description}")
            return False
        
        # Move mouse to element center
        center_x = box['x'] + box['width'] / 2
        center_y = box['y'] + box['height'] / 2
        await page.mouse.move(center_x, center_y)
        await asyncio.sleep(0.5)
        
        # Try element click first
        try:
            await element.click(force=True, timeout=timeout)
            print(f"✅ Clicked {description} with element.click")
            return True
        except Exception as e:
            print(f"⚠️ Element click failed for {description}: {e}")
            
            # Fallback to mouse click
            try:
                await page.mouse.click(center_x, center_y)
                print(f"✅ Clicked {description} with mouse.click")
                return True
            except Exception as e2:
                print(f"❌ Mouse click also failed for {description}: {e2}")
                return False
                
    except Exception as e:
        print(f"❌ Error during safe_click for {description}: {e}")
        return False


async def wait_and_click(page, selector: str, description: str = "", timeout: int = 10000):
    """
    Wait for selector and perform safe click.
    
    Args:
        page: Playwright page object
        selector: CSS selector
        description: Description for logging
        timeout: Wait timeout in milliseconds
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        await page.wait_for_selector(selector, timeout=timeout)
        element = await page.query_selector(selector)
        if element:
            return await safe_click(page, element, description or selector, timeout)
        else:
            print(f"❌ Element not found: {selector}")
            return False
    except Exception as e:
        print(f"❌ Error in wait_and_click for {selector}: {e}")
        return False


async def safe_fill(page, selector: str, value: str, description: str = ""):
    """
    Safely fill an input field with error handling.
    
    Args:
        page: Playwright page object
        selector: CSS selector for input field
        value: Value to fill
        description: Description for logging
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        await page.wait_for_selector(selector, timeout=10000)
        await page.fill(selector, value)
        print(f"✅ Filled {description or selector} with: {value}")
        return True
    except Exception as e:
        print(f"❌ Error filling {description or selector}: {e}")
        return False


def format_time_duration(hours: float) -> str:
    """
    Format duration in hours to a readable string.
    
    Args:
        hours: Duration in hours
        
    Returns:
        str: Formatted duration string
    """
    if hours == int(hours):
        return f"{int(hours)} hour{'s' if hours != 1 else ''}"
    else:
        whole_hours = int(hours)
        minutes = int((hours - whole_hours) * 60)
        if whole_hours == 0:
            return f"{minutes} minutes"
        elif minutes == 0:
            return f"{whole_hours} hour{'s' if whole_hours != 1 else ''}"
        else:
            return f"{whole_hours} hour{'s' if whole_hours != 1 else ''} {minutes} minutes"


def validate_date_format(date_string: str) -> bool:
    """
    Validate if date string is in YYYY-MM-DD format.
    
    Args:
        date_string: Date string to validate
        
    Returns:
        bool: True if valid format, False otherwise
    """
    try:
        parts = date_string.split('-')
        if len(parts) != 3:
            return False
        
        year, month, day = parts
        if len(year) != 4 or len(month) != 2 or len(day) != 2:
            return False
        
        # Basic range checks
        year_int = int(year)
        month_int = int(month)
        day_int = int(day)
        
        if not (2020 <= year_int <= 2030):
            return False
        if not (1 <= month_int <= 12):
            return False
        if not (1 <= day_int <= 31):
            return False
        
        return True
    except (ValueError, AttributeError):
        return False


async def scroll_element_into_view(page, element, description: str = "element"):
    """
    Scroll element into view with error handling.
    
    Args:
        page: Playwright page object
        element: Element to scroll into view
        description: Description for logging
    """
    try:
        await element.scroll_into_view_if_needed()
        print(f"✅ Scrolled {description} into view")
    except Exception as e:
        print(f"⚠️ Could not scroll {description} into view: {e}")


async def debug_element_info(element, description: str = "element"):
    """
    Print debug information about an element.
    
    Args:
        element: Element to debug
        description: Description for logging
    """
    try:
        tag_name = await element.evaluate('el => el.tagName')
        classes = await element.get_attribute('class') or 'none'
        id_attr = await element.get_attribute('id') or 'none'
        text_content = (await element.inner_text())[:50] if await element.inner_text() else 'none'
        
        print(f"🔍 Debug {description}:")
        print(f"   Tag: {tag_name}")
        print(f"   Classes: {classes}")
        print(f"   ID: {id_attr}")
        print(f"   Text: {text_content}...")
        
    except Exception as e:
        print(f"❌ Error debugging {description}: {e}")


def print_banner(text: str, char: str = "="):
    """
    Print a banner with text for better console output formatting.
    
    Args:
        text: Text to display
        char: Character to use for border
    """
    width = max(50, len(text) + 4)
    border = char * width
    padding = (width - len(text) - 2) // 2
    padded_text = f"{char}{' ' * padding}{text}{' ' * padding}{char}"
    
    print(f"\n{border}")
    print(padded_text)
    print(f"{border}\n")


async def handle_potential_modal(page, modal_selector: str, button_selector: str, description: str):
    """
    Handle potential modal dialogs that might appear.
    
    Args:
        page: Playwright page object
        modal_selector: Selector for modal container
        button_selector: Selector for button to click
        description: Description for logging
        
    Returns:
        bool: True if modal was handled, False if no modal found
    """
    try:
        modal = await page.query_selector(modal_selector)
        if modal and await modal.is_visible():
            button = await page.query_selector(button_selector)
            if button:
                await button.click()
                print(f"✅ Handled {description} modal")
                return True
        return False
    except Exception as e:
        print(f"❌ Error handling {description} modal: {e}")
        return False
