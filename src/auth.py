"""
Authentication module for Playo booking automation.
Handles login, OTP verification, and authentication state management.
"""

import asyncio
from config import SELECTORS, DEFAULT_TIMEOUT, OTP_WAIT_TIME


class PlayoAuth:
    """Handles authentication flow for Playo website."""
    
    def __init__(self, page):
        self.page = page
    
    async def handle_login(self) -> bool:
        """
        Complete login flow including OTP verification.
        
        Returns:
            bool: True if login successful or already logged in, False otherwise
        """
        try:
            # Check if already logged in
            already_logged_in = await self._check_login_status()
            if already_logged_in:
                print("✅ Already logged in, skipping login flow")
                return True
            
            # Perform login flow
            phone_number = await self._get_phone_number()
            if not phone_number:
                return False
            
            await self._click_login_button()
            await self._fill_phone_number(phone_number)
            await self._send_otp()
            
            # Wait and get OTP
            print(f"⏳ Waiting {OTP_WAIT_TIME} seconds for OTP to arrive...")
            await asyncio.sleep(OTP_WAIT_TIME)
            
            otp = input("Please enter the 5-digit OTP you received: ").strip()
            if len(otp) != 5 or not otp.isdigit():
                print("❌ Invalid OTP format. Please restart the script.")
                return False
            
            await self._fill_otp(otp)
            await self._verify_otp()
            
            print("✅ Login flow completed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Login failed with error: {e}")
            return False
    
    async def _check_login_status(self) -> bool:
        """Check if user is already logged in."""
        try:
            await self.page.wait_for_selector(SELECTORS["login_button"], timeout=5000)
            return False  # Login button found, not logged in
        except Exception:
            return True  # Login button not found, already logged in
    
    async def _get_phone_number(self) -> str:
        """Get phone number from user input."""
        phone_number = input("Please enter your phone number to create an account: ").strip()
        if not phone_number:
            print("❌ Phone number is required")
            return ""
        return phone_number
    
    async def _click_login_button(self):
        """Click the login/signup button."""
        await self.page.wait_for_selector(SELECTORS["login_button"], timeout=DEFAULT_TIMEOUT)
        login_btn = await self.page.query_selector(SELECTORS["login_button"])
        
        if login_btn:
            box = await login_btn.bounding_box()
            if box:
                await self.page.mouse.move(
                    box['x'] + box['width']/2, 
                    box['y'] + box['height']/2
                )
                await asyncio.sleep(0.5)
                await login_btn.click()
                print("✅ Clicked Login / Signup button")
            else:
                print("❌ Could not get bounding box for Login / Signup button")
                raise Exception("Login button click failed")
        else:
            print("❌ Could not find Login / Signup button")
            raise Exception("Login button not found")
    
    async def _fill_phone_number(self, phone_number: str):
        """Fill the phone number input field."""
        await self.page.wait_for_selector(SELECTORS["phone_input"], timeout=DEFAULT_TIMEOUT)
        await self.page.fill(SELECTORS["phone_input"], phone_number)
        print(f"✅ Filled phone number field with {phone_number}")
    
    async def _send_otp(self):
        """Click the Send OTP button."""
        await self.page.wait_for_selector(SELECTORS["send_otp_button"], timeout=DEFAULT_TIMEOUT)
        await self.page.click(SELECTORS["send_otp_button"])
        print("✅ Clicked Send OTP button")
    
    async def _fill_otp(self, otp: str):
        """Fill individual OTP input fields."""
        for i, digit in enumerate(otp[:5], start=1):
            selector = SELECTORS["otp_inputs"].format(i=i)
            await self.page.wait_for_selector(selector, timeout=DEFAULT_TIMEOUT)
            await self.page.fill(selector, digit)
        print("✅ Filled OTP fields")
    
    async def _verify_otp(self):
        """Click the verify button to complete authentication."""
        await self.page.wait_for_selector(SELECTORS["verify_button"], timeout=DEFAULT_TIMEOUT)
        await self.page.click(SELECTORS["verify_button"])
        print("✅ Clicked VERIFY button")
    
    async def handle_error_modal(self) -> bool:
        """
        Handle 'Something went wrong' error modal if it appears.
        
        Returns:
            bool: True if error modal was handled, False if no error
        """
        try:
            error_ok_btn = await self.page.query_selector(SELECTORS["error_modal_ok"])
            if error_ok_btn:
                print("⚠️ 'Something went wrong!' error detected. Clicking OK...")
                await error_ok_btn.click()
                print("✅ Clicked OK on error modal")
                return True
            return False
        except Exception as e:
            print(f"❌ Error handling modal: {e}")
            return False
