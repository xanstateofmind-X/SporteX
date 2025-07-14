"""
Booking flow module for Playo booking automation.
Handles date selection, time selection, court booking, and checkout process.
"""

import asyncio
import re
from typing import List, Optional, Dict
from config import SELECTORS, DEFAULT_TIMEOUT, LONG_TIMEOUT, DEFAULT_DURATION_HOURS, DURATION_INCREMENT


class BookingFlow:
    """Handles the complete booking flow from venue selection to checkout."""
    
    def __init__(self, page, context):
        self.page = page
        self.context = context
    
    async def complete_booking(self, sport_name: str) -> bool:
        """
        Complete the entire booking flow.
        
        Args:
            sport_name: Name of the selected sport
            
        Returns:
            bool: True if booking completed successfully
        """
        try:
            # Wait for new tab and switch to it
            new_page = await self._wait_for_new_tab()
            if new_page:
                self.page = new_page
                await self.page.bring_to_front()
                await asyncio.sleep(2)
            
            # Click Book Now
            if not await self._click_book_now():
                return False
            
            # Ensure correct sport is selected
            await self._ensure_correct_sport(sport_name)
            
            # Get booking details from user
            date = input("What date do you want to book the turf for? (YYYY-MM-DD): ").strip()
            await self._select_date(date)
            
            # Handle time selection
            available_times = await self._scrape_time_slots()
            if available_times:
                await self._select_time_slot(available_times)
            
            # Handle duration
            await self._set_duration()
            
            # Handle court selection
            await self._select_court()
            
            # Complete checkout
            await self._complete_checkout()
            
            print("🎉 Booking flow completed!")
            return True
            
        except Exception as e:
            print(f"❌ Error in booking flow: {e}")
            return False
    
    async def _wait_for_new_tab(self) -> Optional[object]:
        """Wait for a new tab to open and return the new page."""
        print("⏳ Waiting for new tab to open...")
        old_pages = self.context.pages.copy()
        
        for _ in range(20):  # Wait up to 10 seconds
            await asyncio.sleep(0.5)
            pages = self.context.pages
            if len(pages) > len(old_pages):
                new_page = [p for p in pages if p not in old_pages][0]
                print(f"✅ Switched to new tab: {new_page.url}")
                return new_page
        
        print("⚠️ No new tab detected. Staying on current page.")
        return None
    
    async def _click_book_now(self) -> bool:
        """Click the Book Now button."""
        print("🎯 Looking for 'Book Now' button...")
        try:
            await self.page.wait_for_selector(SELECTORS["book_now_button"], timeout=DEFAULT_TIMEOUT)
            await self.page.click(SELECTORS["book_now_button"])
            print("✅ Clicked 'Book Now' button!")
            return True
        except Exception as e:
            print(f"❌ Could not click 'Book Now' button: {e}")
            print("The script will pause for 10 seconds for manual intervention...")
            await asyncio.sleep(10)
            return False
    
    async def _ensure_correct_sport(self, sport_name: str):
        """Ensure the correct sport is selected."""
        print(f"🏃 Ensuring correct sport is selected: {sport_name}")
        try:
            selected_sport_btn = await self.page.query_selector(SELECTORS["sport_selector_button"])
            if not selected_sport_btn:
                print("❌ Could not find sport selection button")
                return
            
            selected_sport_text = (await selected_sport_btn.inner_text()).strip().lower()
            
            if sport_name.lower() not in selected_sport_text:
                print(f"Current sport is not '{sport_name}'. Selecting correct sport...")
                await selected_sport_btn.click()
                await asyncio.sleep(1)
                
                await self.page.wait_for_selector(SELECTORS["sport_dropdown"], timeout=5000)
                sport_options = await self.page.query_selector_all(SELECTORS["sport_options"])
                
                for option in sport_options:
                    text = (await option.inner_text()).strip().lower()
                    if sport_name.lower() in text:
                        await option.click()
                        print(f"✅ Selected sport: {text}")
                        return
                
                print(f"❌ Could not find sport option matching '{sport_name}'")
            else:
                print(f"✅ Correct sport '{sport_name}' is already selected")
                
        except Exception as e:
            print(f"❌ Error ensuring correct sport: {e}")
    
    async def _select_date(self, date: str):
        """Select the booking date."""
        day = str(int(date.split('-')[-1]))  # Extract day
        
        print(f"📅 Selecting date: {date} (day {day})")
        
        try:
            # Click date picker
            await self.page.wait_for_selector(SELECTORS["date_picker_button"], timeout=DEFAULT_TIMEOUT)
            await self.page.click(SELECTORS["date_picker_button"])
            print("✅ Clicked date picker button")
            await asyncio.sleep(1)
            
            # Wait for calendar and select day
            await self.page.wait_for_selector(SELECTORS["calendar_popover"], timeout=DEFAULT_TIMEOUT)
            day_divs = await self.page.query_selector_all(SELECTORS["calendar_days"])
            
            for div in day_divs:
                text = (await div.inner_text()).strip()
                if text == day or text.lstrip('0') == day:
                    await div.click()
                    print(f"✅ Selected day {day}")
                    return
            
            print(f"❌ Could not find day {day} in calendar")
            
        except Exception as e:
            print(f"❌ Error selecting date: {e}")
    
    async def _scrape_time_slots(self) -> List[str]:
        """Scrape available time slots."""
        print("🕐 Scraping available time slots...")
        try:
            # Try to open time picker dropdown
            await self._open_time_picker()
            
            # Try new structure first
            time_options = await self.page.query_selector_all(SELECTORS["time_slots_new"])
            if time_options:
                print(f"Found {len(time_options)} time slots (new structure)")
                available_times = []
                for option in time_options:
                    text = (await option.inner_text()).strip()
                    if text:
                        available_times.append(text)
            else:
                # Fallback to old structure
                time_options = await self.page.query_selector_all(SELECTORS["time_slots_old"])
                print(f"Found {len(time_options)} time slots (old structure)")
                available_times = []
                for option in time_options:
                    text = (await option.inner_text()).strip()
                    if text:
                        available_times.append(text)
            
            if available_times:
                print("Available time slots:")
                for idx, time in enumerate(available_times, 1):
                    print(f"{idx}. {time}")
            
            return available_times
            
        except Exception as e:
            print(f"❌ Error scraping time slots: {e}")
            return []
    
    async def _open_time_picker(self):
        """Aggressively try to open the time picker dropdown."""
        print("🎯 Opening time picker dropdown...")
        
        # Try multiple selectors for the time picker button
        time_picker_btn = None
        for selector in SELECTORS["time_picker_buttons"]:
            try:
                time_picker_btn = await self.page.query_selector(selector)
                if time_picker_btn:
                    print(f"✅ Found time picker button with selector: {selector}")
                    break
            except Exception:
                continue
        
        if not time_picker_btn:
            print("❌ Could not find time picker button")
            return
        
        # Aggressively click the button
        box = await time_picker_btn.bounding_box()
        if box:
            await self.page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
            await asyncio.sleep(1)
            
            try:
                await time_picker_btn.click(force=True, timeout=5000)
                print("✅ Opened time picker with element click")
            except Exception as e:
                print(f"Element click failed: {e}, trying mouse click")
                try:
                    await self.page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                    print("✅ Opened time picker with mouse click")
                except Exception as e2:
                    print(f"❌ Both click methods failed: {e2}")
            
            await asyncio.sleep(2)
    
    async def _select_time_slot(self, available_times: List[str]):
        """Select a time slot from available options."""
        start_time_input = input("Enter the number or time string of your desired slot: ").strip()
        
        # Try number selection
        try:
            num_choice = int(start_time_input) - 1
            if 0 <= num_choice < len(available_times):
                start_time = available_times[num_choice]
            else:
                print(f"Invalid number. Using first available: {available_times[0]}")
                start_time = available_times[0]
        except ValueError:
            # Try string matching
            matches = [t for t in available_times if start_time_input.lower().replace(' ', '') in t.lower().replace(' ', '')]
            if matches:
                start_time = matches[0]
            else:
                print(f"No match found. Using first available: {available_times[0]}")
                start_time = available_times[0]
        
        print(f"🎯 Selecting time slot: {start_time}")
        await self._click_time_slot(start_time)
    
    async def _click_time_slot(self, start_time: str):
        """Aggressively click the selected time slot."""
        try:
            # Try new structure first
            time_slot_divs = await self.page.query_selector_all(SELECTORS["time_slots_new"])
            if not time_slot_divs:
                # Fallback to old structure
                time_slot_divs = await self.page.query_selector_all(SELECTORS["time_slots_old"])
            
            for slot_div in time_slot_divs:
                text = (await slot_div.inner_text()).strip()
                if start_time.lower().replace(' ', '') == text.lower().replace(' ', ''):
                    box = await slot_div.bounding_box()
                    if box:
                        await self.page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
                        await asyncio.sleep(0.5)
                        
                        try:
                            await slot_div.click(force=True, timeout=5000)
                            print(f"✅ Selected time slot: {text}")
                            return
                        except Exception:
                            await self.page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                            print(f"✅ Selected time slot with mouse: {text}")
                            return
            
            print(f"❌ Could not find time slot: {start_time}")
            
        except Exception as e:
            print(f"❌ Error clicking time slot: {e}")
    
    async def _set_duration(self):
        """Set the booking duration."""
        duration_input = input(
            "How many hours do you want to book? "
            "(e.g., 1.5, 2 hrs, 1 hr 30 min, 90 min): "
        ).strip()
        
        duration_hours = self._parse_duration(duration_input)
        if duration_hours is None or duration_hours <= 0:
            print("Invalid duration. Defaulting to 1 hour.")
            duration_hours = DEFAULT_DURATION_HOURS
        
        # Calculate clicks needed
        clicks_needed = int(round((duration_hours - DEFAULT_DURATION_HOURS) / DURATION_INCREMENT))
        
        if clicks_needed > 0:
            print(f"⏱️ Setting duration to {duration_hours} hours ({clicks_needed} clicks)...")
            await self._click_duration_plus(clicks_needed)
        else:
            print(f"✅ Duration already set to {duration_hours} hours")
    
    def _parse_duration(self, duration_input: str) -> Optional[float]:
        """Parse duration input into hours."""
        duration_input = duration_input.lower().strip()
        
        # Various duration patterns
        patterns = [
            (r"(\d+(?:\.\d+)?)\s*min", lambda m: float(m.group(1)) / 60),
            (r"(\d+(?:\.\d+)?)\s*hr[s]?\s*(\d+)?\s*min?", lambda m: float(m.group(1)) + (float(m.group(2)) if m.group(2) else 0) / 60),
            (r"(\d+(?:\.\d+)?)\s*(hr[s]?|hour[s]?)", lambda m: float(m.group(1))),
            (r"(\d+)\s*hr[s]?\s*(\d+)\s*min", lambda m: float(m.group(1)) + float(m.group(2)) / 60),
        ]
        
        for pattern, converter in patterns:
            match = re.match(pattern, duration_input)
            if match:
                return converter(match)
        
        # Try parsing as plain number
        try:
            return float(duration_input)
        except ValueError:
            return None
    
    async def _click_duration_plus(self, clicks_needed: int):
        """Click the plus button to increase duration."""
        for i in range(clicks_needed):
            try:
                svg = await self.page.query_selector(SELECTORS["plus_button_svg"])
                if svg:
                    box = await svg.bounding_box()
                    if box:
                        await self.page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
                        await asyncio.sleep(0.5)
                        await self.page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                        print(f"✅ Duration click {i+1}/{clicks_needed}")
                    else:
                        print(f"❌ Could not get bounding box for plus button (click {i+1})")
                else:
                    print(f"❌ Could not find plus button (click {i+1})")
            except Exception as e:
                print(f"❌ Error on duration click {i+1}: {e}")
    
    async def _select_court(self):
        """Select a court from available options."""
        print("🏟️ Selecting court...")
        try:
            # Click court selection dropdown
            court_span = await self.page.query_selector(SELECTORS["court_selector_span"])
            if court_span:
                text = (await court_span.inner_text()).strip()
                if text == '--Select Court--':
                    await self._click_court_dropdown(court_span)
                    
                    # Scrape and select court
                    courts = await self._scrape_courts()
                    if courts:
                        await self._prompt_and_select_court(courts)
                else:
                    print(f"❌ Court selector text was '{text}', not '--Select Court--'")
            else:
                print("❌ Could not find court selection element")
                
        except Exception as e:
            print(f"❌ Error selecting court: {e}")
    
    async def _click_court_dropdown(self, court_span):
        """Click the court selection dropdown."""
        # Walk up DOM to find clickable parent
        clickable = court_span
        parent = court_span
        
        for _ in range(5):
            parent = await parent.query_selector('xpath=..')
            if not parent:
                break
            
            tag_handle = await parent.get_property('tagName')
            tag = (await tag_handle.json_value()).lower() if tag_handle else ''
            classes = await parent.get_attribute('class') or ''
            
            if tag == 'button' or 'cursor-pointer' in classes:
                clickable = parent
                break
        
        box = await clickable.bounding_box()
        if box:
            await self.page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
            await asyncio.sleep(0.5)
            await clickable.click(force=True, timeout=5000)
            print("✅ Clicked court selection dropdown")
    
    async def _scrape_courts(self) -> List[Dict]:
        """Scrape available court options."""
        await self.page.wait_for_selector('ul[role="listbox"]', timeout=5000)
        court_options = await self.page.query_selector_all(SELECTORS["court_options"])
        
        courts = []
        for option in court_options:
            spans = await option.query_selector_all('span')
            name = (await spans[0].inner_text()).strip() if len(spans) > 0 else ''
            price = (await spans[1].inner_text()).strip() if len(spans) > 1 else ''
            courts.append({'name': name, 'price': price, 'el': option})
        
        return courts
    
    async def _prompt_and_select_court(self, courts: List[Dict]):
        """Prompt user to select a court."""
        print("Available courts:")
        for i, court in enumerate(courts, 1):
            print(f"{i}. {court['name']} ({court['price']})")
        
        user_input = input("Which court do you want? Enter the number or name: ").strip()
        
        # Try number selection
        try:
            num_choice = int(user_input) - 1
            if 0 <= num_choice < len(courts):
                choice = num_choice
            else:
                print(f"Invalid number. Using first court: {courts[0]['name']}")
                choice = 0
        except ValueError:
            # Try name matching
            matches = [i for i, c in enumerate(courts) if user_input.lower() in c['name'].lower()]
            if matches:
                choice = matches[0]
            else:
                print(f"No match found. Using first court: {courts[0]['name']}")
                choice = 0
        
        await self._click_court_option(courts[choice])
    
    async def _click_court_option(self, court: Dict):
        """Aggressively click the selected court option."""
        selected = court['el']
        box = await selected.bounding_box()
        
        if box:
            await self.page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
            await asyncio.sleep(0.5)
            
            try:
                await selected.click(force=True, timeout=5000)
                print(f"✅ Selected court: {court['name']} ({court['price']})")
            except Exception as e:
                print(f"Element click failed: {e}, trying mouse click")
                try:
                    await self.page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                    print(f"✅ Selected court with mouse: {court['name']}")
                except Exception as e2:
                    print(f"❌ Both click methods failed: {e2}")
    
    async def _complete_checkout(self):
        """Complete the checkout process."""
        print("🛒 Completing checkout process...")
        
        # Add to cart
        await self._click_add_to_cart()
        await asyncio.sleep(2)
        
        # Proceed to checkout
        await self._click_proceed_to_checkout()
    
    async def _click_add_to_cart(self):
        """Click the Add to Cart button."""
        print("🛒 Clicking Add to Cart...")
        
        for selector in SELECTORS["add_to_cart_buttons"]:
            try:
                button = await self.page.query_selector(selector)
                if button:
                    await self._aggressive_click(button, "Add to Cart")
                    return
            except Exception:
                continue
        
        print("❌ Could not find Add to Cart button")
    
    async def _click_proceed_to_checkout(self):
        """Click the Proceed to Checkout button."""
        print("💳 Clicking Proceed to Checkout...")
        
        for selector in SELECTORS["checkout_buttons"]:
            try:
                button = await self.page.query_selector(selector)
                if button:
                    await self._aggressive_click(button, "Proceed to Checkout")
                    return
            except Exception:
                continue
        
        print("❌ Could not find Proceed to Checkout button")
    
    async def _aggressive_click(self, element, description: str):
        """Perform aggressive clicking on an element."""
        box = await element.bounding_box()
        if box:
            await self.page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
            await asyncio.sleep(1)
            
            try:
                await element.click(force=True, timeout=10000)
                print(f"✅ Clicked {description} successfully")
            except Exception as e:
                print(f"Element click failed: {e}, trying mouse click")
                try:
                    await self.page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                    print(f"✅ Clicked {description} with mouse")
                except Exception as e2:
                    print(f"❌ All click methods failed for {description}: {e2}")
        else:
            print(f"❌ Could not get bounding box for {description}")
