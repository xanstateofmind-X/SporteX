## 📄 main.py (UPDATED)
```python
#!/usr/bin/env python3
"""
Playo Sports Venue Booking Automation
Main entry point for the booking automation script.
"""

import asyncio
import os
from playwright.async_api import async_playwright

from src.auth import PlayoAuth
from src.venue_finder import VenueFinder
from src.booking import BookingFlow
from src.utils import setup_browser_context, add_mouse_cursor
from config import USER_DATA_DIR, GEOLOCATION


async def main():
    """Main function to run the Playo booking automation."""
    print("🏆 Starting Playo Sports Venue Booking Automation...")
    
    async with async_playwright() as p:
        # Setup browser context
        context = await setup_browser_context(p, USER_DATA_DIR, GEOLOCATION)
        page = context.pages[0] if context.pages else await context.new_page()
        
        # Add visual mouse cursor for debugging
        await add_mouse_cursor(page)
        
        try:
            # Navigate to Playo
            await page.goto("https://playo.co/")
            print("✅ Navigated to Playo.co")
            
            # Initialize components
            auth = PlayoAuth(page)
            venue_finder = VenueFinder(page)
            booking_flow = BookingFlow(page, context)
            
            # Step 1: Authentication
            print("\n🔐 Starting authentication process...")
            login_successful = await auth.handle_login()
            if not login_successful:
                print("❌ Login failed. Exiting...")
                return
            
            # Step 2: Sport Selection
            print("\n🏃 Starting sport selection...")
            selected_sport = await venue_finder.select_sport()
            if not selected_sport:
                print("❌ Sport selection failed. Exiting...")
                return
            
            # Step 3: Location and Venue Selection
            print("\n📍 Starting venue search...")
            selected_venue = await venue_finder.select_venue()
            if not selected_venue:
                print("❌ Venue selection failed. Exiting...")
                return
            
            # Step 4: Booking Flow
            print("\n📅 Starting booking process...")
            booking_successful = await booking_flow.complete_booking(selected_sport)
            
            if booking_successful:
                print("\n🎉 Booking flow completed successfully!")
                print("The script will now wait. You can manually complete any remaining steps.")
            else:
                print("\n⚠️ Booking flow completed with some issues. Please check manually.")
            
            # Keep browser open for manual intervention if needed
            print("\n⏳ Keeping browser open for manual completion...")
            await asyncio.Future()
            
        except KeyboardInterrupt:
            print("\n🛑 Script interrupted by user")
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            print("Browser will remain open for manual intervention")
            await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
