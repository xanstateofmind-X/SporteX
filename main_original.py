import asyncio
from playwright.async_api import async_playwright
import re
import os

USER_DATA_DIR = os.path.join(os.getcwd(), "playwright_user_data")

async def main():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=False,
            geolocation={"latitude": 12.9352, "longitude": 77.6762},
            permissions=["geolocation"]
        )
        page = context.pages[0] if context.pages else await context.new_page()
        # Inject a highly visible mouse cursor for debugging (red, always on top)
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
        await page.goto("https://playo.co/")

        # Check if already logged in
        already_logged_in = False
        try:
            await page.wait_for_selector('text=Login / Signup', timeout=5000)
            print("Not logged in, proceeding with login flow.")
            # Click Login / Signup
            await page.wait_for_selector('text=Login / Signup', timeout=10000)
            login_btn = await page.query_selector('text=Login / Signup')
            if login_btn is not None:
                box = await login_btn.bounding_box()
                if box:
                    await page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
                    await asyncio.sleep(0.5)
                    await login_btn.click()
                    print("Clicked Login / Signup button.")
                else:
                    print("Could not find bounding box for Login / Signup button.")
            else:
                print("Could not find Login / Signup button.")

            # Wait for the phone number input and fill it
            await page.wait_for_selector('input.rounded-l-none', timeout=10000)
            phone_number = input("Please enter your phone number to create an account: ").strip()
            await page.fill('input.rounded-l-none', phone_number)
            print(f"Filled phone number field with {phone_number}.")

            # Wait for the Send OTP button and click it
            await page.wait_for_selector('button.bg-primary.new-button', timeout=10000)
            await page.click('button.bg-primary.new-button')
            print("Clicked Send OTP button.")

            # Wait for 10 seconds before prompting for OTP
            print("Waiting 10 seconds for OTP to arrive...")
            await asyncio.sleep(10)

            # Prompt user for OTP in the terminal
            otp = input("Please enter the 5-digit OTP you received: ").strip()

            # Fill each digit into the corresponding input field
            for i, digit in enumerate(otp[:5], start=1):
                selector = f'input#otp-part{i}'
                await page.wait_for_selector(selector, timeout=10000)
                await page.fill(selector, digit)
            print("Filled OTP fields.")

            # Wait for the VERIFY button and click it
            await page.wait_for_selector('button.bg-primary.new-button:has-text("VERIFY")', timeout=10000)
            await page.click('button.bg-primary.new-button:has-text("VERIFY")')
            print("Clicked VERIFY button.")

        except Exception:
            print("Already logged in, skipping login flow.")
            already_logged_in = True

        # Continue with the rest of the script (sport/location/venue selection)

        # Scroll to the Popular Sports section using the header text
        print("Scrolling to the Popular Sports section using the header text...")
        try:
            await page.wait_for_selector('h3:has-text("Popular Sports")', timeout=15000)
            await page.evaluate("""
                () => {
                    const el = Array.from(document.querySelectorAll('h3')).find(e => e.textContent.trim() === 'Popular Sports');
                    if (el) el.scrollIntoView({behavior: 'smooth', block: 'center'});
                }
            """)
            print("Popular Sports section is now visible.")
        except Exception as e:
            print(f"Could not scroll to the Popular Sports section: {e}")

        # After login, scroll to the sports section and select a sport
        try:
            print("Scrolling to the Popular Sports section and scraping sports...")
            await page.wait_for_selector('div.flex.mt-6.gap-6.overflow-x-auto', timeout=10000)
            sports_container = await page.query_selector('div.flex.mt-6.gap-6.overflow-x-auto')
            sport_cards = await sports_container.query_selector_all('div.relative.cursor-pointer') if sports_container else []
            sports = []
            for idx, card in enumerate(sport_cards):
                name_div = await card.query_selector('div.absolute.text-white.font-bold')
                name = (await name_div.inner_text()).strip() if name_div else f"Sport {idx+1}"
                sports.append({'name': name, 'el': card})
            if sports:
                print("Available sports:")
                for i, s in enumerate(sports, 1):
                    print(f"{i}. {s['name']}")
                user_input = input("Which sport do you want? Enter the number or name: ").strip()
                # Try number selection
                try:
                    num_choice = int(user_input) - 1
                    if 0 <= num_choice < len(sports):
                        choice = num_choice
                    else:
                        print(f"Invalid number. Defaulting to first sport: {sports[0]['name']}")
                        choice = 0
                except ValueError:
                    # Try to match by name
                    matches = [i for i, s in enumerate(sports) if user_input.lower() in s['name'].lower()]
                    if matches:
                        choice = matches[0]
                    else:
                        print(f"No match found. Defaulting to first sport: {sports[0]['name']}")
                        choice = 0
                # Aggressively click the selected sport card
                selected = sports[choice]['el']
                sport = sports[choice]['name']
                box = await selected.bounding_box()
                if box:
                    print(f"Aggressively moving mouse to sport at x={box['x']}, y={box['y']}, w={box['width']}, h={box['height']}")
                    await page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
                    await asyncio.sleep(0.5)
                    try:
                        await selected.click(force=True, timeout=5000)
                        print("Aggressive element.click on sport succeeded.")
                    except Exception as e:
                        print(f"Aggressive element.click on sport failed: {e}")
                        try:
                            await page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                            print("Aggressive mouse.click on sport succeeded.")
                        except Exception as e2:
                            print(f"Aggressive mouse.click on sport failed: {e2}")
                else:
                    print("❌ Could not get bounding box for selected sport card.")
                print(f"Clicked sport: {sports[choice]['name']}")
            else:
                print("❌ No sports found in the section.")
        except Exception as e:
            print(f"❌ Error scraping/selecting sport: {e}")

        # Prompt user for the location to book
        print("Note: The site may use your current location for initial access, but you can book in any area you prefer.")
        location = input("Which area do you want to search for venues in? (e.g., Bellandur, HSR, Koramangala): ").strip()

        # Skip location selection for now - it's causing navigation issues
        print(f"Proceeding with current location. You can manually change to {location} if needed.")
        print("The script will scrape venues from the current page.")

        # Check if we're still on the correct page before scraping venues
        current_url = page.url
        print(f"Current page URL: {current_url}")
        
        # If we've navigated away from the main page, try to go back or reload
        if "playo.co" not in current_url or "/venue" in current_url or "/sport" in current_url:
            print("Detected navigation to a different page. Attempting to return to venue listing...")
            try:
                await page.go_back()
                await asyncio.sleep(2)
            except:
                try:
                    await page.goto("https://playo.co/")
                    await asyncio.sleep(3)
                except:
                    print("Could not return to main page. Please restart the script.")
                    # The original code had browser.close() here, but browser is no longer defined.
                    # Assuming the intent was to close the context if the page navigation failed.
                    # However, the persistent context is managed by playwright, not directly by 'browser'.
                    # For now, removing the line as it's not directly applicable.
                    return
        
        # Scrape venue cards with multiple selector strategies for robustness
        print("Scraping venue names and distances...")
        await asyncio.sleep(3)  # Wait for venues to load after location change
        
        # Use ONLY the most specific selector to get exactly the venue cards
        card_els = []
        try:
            # Use the MOST restrictive selector to get ONLY real venue cards
            card_els = await page.query_selector_all('div.grid.w-full.grid-cols-1.gap-11 > div.border_radius.bg-white.card_shadow.pb-2.cursor-pointer:has(img[src*="gumlet"]):has(div[class*="truncate"])')
            if card_els:
                print(f"Found {len(card_els)} venue cards using restrictive selector")
            else:
                # Fallback to venue cards with both images and text
                card_els = await page.query_selector_all('div[class*="card_shadow"][class*="cursor-pointer"]:has(img[src*="gumlet"]):has(div[class*="truncate"])')
                print(f"Fallback found {len(card_els)} venue cards with images and text")
        except Exception as e:
            print(f"Error finding venue cards: {e}")
            card_els = []
        
        if not card_els:
            print("No venue cards found. Please check if the page loaded correctly.")
            # The original code had browser.close() here, but browser is no longer defined.
            # Assuming the intent was to close the context if no venue cards are found.
            # However, the persistent context is managed by playwright, not directly by 'browser'.
            # For now, removing the line as it's not directly applicable.
            return
        
        print(f"Total venue cards found: {len(card_els)}")
        
        # Debug: Print HTML of first few cards
        for idx, card in enumerate(card_els[:3]):
            try:
                html = await card.inner_html()
                print(f"Card {idx+1} HTML preview: {html[:200]}...")
            except Exception as e:
                print(f"Error reading card {idx+1}: {e}")
        
        venues = []
        for idx, card in enumerate(card_els):
            try:
                # Try multiple selectors for venue name
                name_selectors = [
                    '.title_large',
                    '[class*="title_large"]',
                    'div[class*="truncate"][class*="text-"]',
                    'div[class*="font-"]:not([class*="text-xs"])'
                ]
                
                name = ''
                for name_selector in name_selectors:
                    name_el = await card.query_selector(name_selector)
                    if name_el:
                        name = (await name_el.inner_text()).strip()
                        if name and len(name) > 3:  # Valid name should be longer than 3 chars
                            break
                
                # Try multiple selectors for distance
                distance = ''
                dist_selectors = [
                    '.overflow-hidden.truncate',
                    '[class*="overflow-hidden"][class*="truncate"]',
                    'div:contains("km")',
                    'span:contains("km")'
                ]
                
                for dist_selector in dist_selectors:
                    try:
                        dist_els = await card.query_selector_all(dist_selector)
                        for dist_el in dist_els:
                            dist_text = (await dist_el.inner_text()).strip()
                            if 'km' in dist_text:
                                distance = dist_text.replace('(', '').replace(')', '').strip()
                                break
                        if distance:
                            break
                    except:
                        continue
                
                # Parse venue name
                if ' - ' in name:
                    venue, loc = name.rsplit(' - ', 1)
                else:
                    venue, loc = name, ''
                
                # Filter out garbage data - only add if it looks like a real venue name
                if name and len(name) > 3:
                    # Skip common garbage patterns
                    garbage_patterns = [
                        'featured', 'regular', 'mixed doubles', 'doubles', 'singles',
                        'badminton', 'football', 'cricket', 'swimming', 'tennis', 'table tennis',
                        '3.39', '2.91', '4.2', '4.5', '4.8', '4.9', '5.0',  # Rating patterns
                        'playo', 'logo', 'menu', 'search', 'filter'
                    ]
                    
                    name_lower = name.lower()
                    is_garbage = any(pattern in name_lower for pattern in garbage_patterns)
                    
                    if not is_garbage and len(name) > 5:  # Must be longer than 5 chars and not garbage
                        venues.append({
                            'name': name, 
                            'venue': venue, 
                            'location': loc, 
                            'distance': distance, 
                            'el': card,
                            'index': idx
                        })
                        print(f"Venue {len(venues)}: {name} — {distance}")
                    else:
                        print(f"Skipped garbage venue: {name}")
                else:
                    print(f"Skipped invalid venue name: {name}")
                    
            except Exception as e:
                print(f"Error processing card {idx+1}: {e}")
                continue
        # Remove duplicates
        seen = set()
        unique_venues = []
        for v in venues:
            if v['name'] not in seen:
                unique_venues.append(v)
                seen.add(v['name'])
        venues = unique_venues
        # Set the location in the search field and trigger search, with error modal handling
        while True:
            try:
                await page.wait_for_selector('input[placeholder*="Search"]', timeout=10000)
                await page.fill('input[placeholder*="Search"]', location)
                await page.press('input[placeholder*="Search"]', 'Enter')
                print(f"Set location to {location} and triggered search.")
                await asyncio.sleep(2)  # Wait for results or error modal to load
            except Exception as e:
                print(f"❌ Could not set location: {e}")

            # Check for the error modal and click OK if present
            try:
                error_ok_btn = await page.query_selector('button.bg-error.text-on_error')
                if error_ok_btn:
                    print("⚠️  'Something went wrong!' error detected. Clicking OK...")
                    await error_ok_btn.click()
                    print("Clicked OK on error modal.")
                    location = input("Location search failed. Enter a new location to try again (or leave blank to cancel): ").strip()
                    if not location:
                        print("No location entered. Exiting location selection.")
                        return
                    continue  # Retry with new location
            except Exception as e:
                print(f"Error handling 'Something went wrong' modal: {e}")
            break  # Exit loop if no error modal

        # Venue selection: allow global number selection
        if len(venues) == 1:
            dist_str = f"{venues[0]['distance']} from your current location" if venues[0]['distance'] else "distance unknown"
            print(f"Only one venue found: {venues[0]['name']} — {dist_str}")
            choice = 0
        else:
            batch_size = 3
            start = 0
            choice = None
            while True:
                print(f"These are the available locations where you can play '{sport}':")
                for i in range(start, min(start + batch_size, len(venues))):
                    v = venues[i]
                    dist_str = f"{v['distance']} from your current location" if v['distance'] else "distance unknown"
                    print(f"{i+1}. {v['name']} — {dist_str}")
                if start + batch_size >= len(venues):
                    prompt = "Enter the number (1-N) or name of your choice: "
                else:
                    prompt = "Type 'more' to see more venues, or enter the number (1-N) or name of your choice: "
                user_input = input(prompt).strip()
                if user_input.lower() == 'more' and start + batch_size < len(venues):
                    start += batch_size
                    continue
                # Try global number selection
                try:
                    num_choice = int(user_input) - 1
                    if 0 <= num_choice < len(venues):
                        choice = num_choice
                        break
                    else:
                        print(f"Please enter a number between 1 and {len(venues)}")
                        continue
                except ValueError:
                    pass
                # Try name selection (case-insensitive, partial match allowed)
                matches = [idx for idx, v in enumerate(venues) if user_input.lower() in v['name'].lower()]
                if len(matches) == 1:
                    choice = matches[0]
                    print(f"Selected venue by name: {venues[choice]['name']}")
                    break
                elif len(matches) > 1:
                    print("Multiple venues match that name. Please be more specific or use the number.")
                else:
                    print("Venue not found. Please try again.")

        # Scroll to and click the chosen venue
        await venues[choice]['el'].scroll_into_view_if_needed()
        old_pages = context.pages.copy()
        await venues[choice]['el'].click()
        print(f"Selected venue: {venues[choice]['name']}")

        # Wait for a new page (tab) to open
        print("Waiting for new tab to open after venue click...")
        new_page = None
        for _ in range(20):  # Wait up to 10 seconds
            await asyncio.sleep(0.5)
            pages = context.pages
            if len(pages) > len(old_pages):
                new_page = [p for p in pages if p not in old_pages][0]
                break

        if new_page is None:
            print("❌ No new tab detected. Staying on current page.")
            new_page = page  # fallback to current page
        else:
            print(f"✅ Switched to new tab: {new_page.url}")
            page = new_page

        await page.bring_to_front()
        await asyncio.sleep(2)
        current_url = page.url
        page_title = await page.title()
        print(f"Current page URL: {current_url}")
        print(f"Current page title: {page_title}")

        # Wait for the Book Now button to appear
        print("Waiting for 'Book Now' button to appear...")
        try:
            await page.wait_for_selector('button[aria-label="Book Now"]', timeout=10000)
            print("'Book Now' button appeared!")
            await page.click('button[aria-label="Book Now"]')
            print("✅ Clicked 'Book Now' button!")
        except Exception as e:
            print(f"❌ Could not click 'Book Now' button: {e}")
            print("The script will pause here for 10 seconds so you can click manually...")
            await asyncio.sleep(10)
            print("Done! The script will now exit.")
            return

        # Ensure correct sport is selected AFTER clicking Book Now and page loads
        print(f"Ensuring correct sport is selected: {sport}")
        try:
            # Find the currently selected sport text
            selected_sport_btn = await page.query_selector('button[aria-haspopup="true"]')
            selected_sport_text = None
            if selected_sport_btn:
                # Try to get the text from the button (may be in a span)
                try:
                    selected_sport_text = (await selected_sport_btn.inner_text()).strip().lower()
                except Exception:
                    selected_sport_text = None
            if not selected_sport_text or sport.lower() not in selected_sport_text:
                print(f"Current sport is not '{sport}'. Selecting correct sport...")
                if selected_sport_btn:
                    await selected_sport_btn.click()
                    await asyncio.sleep(1)
                    # Wait for the dropdown list to appear
                    await page.wait_for_selector('ul[role="listbox"]', timeout=5000)
                    # Find and click the correct sport option
                    sport_options = await page.query_selector_all('ul[role="listbox"] li[role="option"]')
                    found = False
                    for option in sport_options:
                        text = (await option.inner_text()).strip().lower()
                        if sport.lower() in text:
                            await option.click()
                            print(f"✅ Selected sport: {text}")
                            found = True
                            break
                    if not found:
                        print(f"❌ Could not find sport option matching '{sport}'. Please select manually.")
                else:
                    print("❌ Could not find the sport selection button on the page.")
            else:
                print(f"Correct sport '{sport}' is already selected.")
        except Exception as e:
            print(f"❌ Error ensuring correct sport: {e}")

        # Prompt for date
        date = input("What date do you want to book the turf for? (YYYY-MM-DD): ").strip()
        day = str(int(date.split('-')[-1]))  # Extract day as string, e.g., "12"

        # 1. Click the date picker button
        try:
            await page.wait_for_selector('button#headlessui-popover-button-6', timeout=10000)
            await page.click('button#headlessui-popover-button-6')
            print("Clicked date picker button.")
            await asyncio.sleep(1)
        except Exception as e:
            print(f"❌ Could not click date picker button: {e}")

        # 2. Wait for the calendar popover and click the correct day
        try:
            await page.wait_for_selector('div[id^="headlessui-popover-panel-"]', timeout=10000)
            print("Calendar popover appeared.")
        except Exception as e:
            print(f"❌ Calendar popover did not appear: {e}")

        try:
            day_divs = await page.query_selector_all('div[id^="headlessui-popover-panel-"] div.cursor-pointer.font-medium')
            found = False
            for div in day_divs:
                text = (await div.inner_text()).strip()
                if text == day or text.lstrip('0') == day:
                    await div.click()
                    print(f"✅ Clicked on day {day}")
                    found = True
                    break
            if not found:
                print(f"❌ Could not find day {day} in the calendar. Please select manually.")
        except Exception as e:
            print(f"❌ Error clicking day {day}: {e}")

        # Scrape and show available time slots before prompting for start time
        print("Scraping available time slots...")
        try:
            # Step 1: Check if dropdown is already open or if we can find time slots directly
            dropdown_open = False
            time_slots_found = False
            
            # First, try to find time slots directly (dropdown might already be open)
            try:
                time_slots = await page.query_selector_all('ul.grid.grid-cols-2.bg-white[role="listbox"] li[role="option"] div')
                if time_slots:
                    print(f"✅ Found {len(time_slots)} time slots directly - dropdown is already open!")
                    time_slots_found = True
                    available_times = []
                    for slot in time_slots:
                        text = (await slot.inner_text()).strip()
                        if text:
                            available_times.append(text)
                    if available_times:
                        print("Available time slots:")
                        for idx, t in enumerate(available_times, 1):
                            print(f"{idx}. {t}")
                        # Skip to time selection since slots are already available
                        raise Exception("SKIP_TO_SELECTION")
            except Exception as e:
                if "SKIP_TO_SELECTION" in str(e):
                    # This is our signal to skip to selection
                    pass
                else:
                    print(f"Could not find time slots directly: {e}")
            
            # If we didn't find slots directly, try the normal dropdown approach
            if not time_slots_found:
                try:
                    dropdown = await page.query_selector('ul[role="listbox"]')
                    if dropdown:
                        visible = await dropdown.is_visible()
                        if visible:
                            dropdown_open = True
                            print("Dropdown is already open.")
                except Exception:
                    dropdown_open = False

                # Step 2: If not open, click the button - ULTRA AGGRESSIVE
                if not dropdown_open:
                    print("ULTRA AGGRESSIVE TIME PICKER BUTTON HUNTING...")
                    
                    # Try multiple selectors to find the button
                    time_picker_btn = None
                    selectors_to_try = [
                        'button#headlessui-listbox-button-8',  # EXACT ID from your HTML
                        'button[aria-haspopup="true"][aria-expanded="false"]',  # Closed dropdown button
                        'button.relative.flex.flex-row.items-center.w-full.h-12.px-3.bg-white.border.rounded-lg.cursor-pointer',  # Full class match
                        'button:has(span.block.font-semibold.truncate)',  # Button with time text
                        'button:has-text("06:00 AM")',  # Button with specific time
                        'button[aria-haspopup="true"]',  # Any dropdown button
                        'button:has-text("AM")',  # Button with AM
                        'button:has-text("PM")'  # Button with PM
                    ]
                    
                    for selector in selectors_to_try:
                        try:
                            time_picker_btn = await page.query_selector(selector)
                            if time_picker_btn:
                                print(f"✅ Found time picker button with selector: {selector}")
                                # Extra debug info for the found button
                                try:
                                    btn_text = await time_picker_btn.inner_text()
                                    btn_id = await time_picker_btn.get_attribute('id')
                                    btn_aria_expanded = await time_picker_btn.get_attribute('aria-expanded')
                                    print(f"🔥 Button details: text='{btn_text}', id='{btn_id}', aria-expanded='{btn_aria_expanded}'")
                                except Exception as debug_e:
                                    print(f"Could not get button details: {debug_e}")
                                break
                        except Exception as e:
                            print(f"Selector {selector} failed: {e}")
                            continue
                    
                    if time_picker_btn:
                        print("ULTRA AGGRESSIVE CLICKING ON TIME PICKER BUTTON...")
                        
                        # Get bounding box and click HARD
                        try:
                            box = await time_picker_btn.bounding_box()
                            if box:
                                print(f"🔥 MOVING MOUSE TO TIME PICKER at x={box['x']}, y={box['y']}, w={box['width']}, h={box['height']}")
                                
                                # Hover over the button first
                                await page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
                                await asyncio.sleep(1)  # Hover for 1 second
                                print("🔥 HOVERING OVER BUTTON...")
                                
                                # Click HARD ONCE - MAKE IT COUNT!
                                print("🔥 CLICKING HARD ONCE - MAKE IT COUNT!")
                                
                                # Try element.click first with maximum force
                                try:
                                    await time_picker_btn.click(force=True, timeout=5000)
                                    print("🔥 ELEMENT.CLICK SUCCESS - CLICKED HARD!")
                                except Exception as e:
                                    print(f"🔥 Element click failed: {e}")
                                    # Try mouse.click as backup - CLICK HARD
                                    try:
                                        await page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                                        print("🔥 MOUSE.CLICK SUCCESS - CLICKED HARD!")
                                    except Exception as e2:
                                        print(f"🔥 Mouse click failed: {e2}")
                                        # Last resort: click top-left corner
                                        try:
                                            await page.mouse.click(box['x'] + 10, box['y'] + 10)
                                            print("🔥 TOP-LEFT CLICK SUCCESS - CLICKED HARD!")
                                        except Exception as e3:
                                            print(f"🔥 All click methods failed: {e3}")
                                
                                # Wait and check if dropdown appeared
                                await asyncio.sleep(2)
                                print("🔥 Checking if dropdown appeared after aggressive clicking...")
                                
                            else:
                                print("❌ Could not get bounding box for time picker button.")
                        except Exception as e:
                            print(f"❌ Error during ULTRA AGGRESSIVE click on time picker: {e}")
                        
                        await asyncio.sleep(1)
                    else:
                        print("❌ COULD NOT FIND TIME PICKER BUTTON WITH ANY SELECTOR!")
                        print("🔥 Trying to find ANY button on the page...")
                        
                        # Last resort: find any button and click it
                        all_buttons = await page.query_selector_all('button')
                        print(f"Found {len(all_buttons)} buttons on the page")
                        
                        for idx, btn in enumerate(all_buttons[:10]):  # Try first 10 buttons
                            try:
                                btn_text = await btn.inner_text()
                                btn_id = await btn.get_attribute('id')
                                print(f"Button {idx+1}: text='{btn_text}', id='{btn_id}'")
                                
                                # If it looks like a time picker button, click it
                                if any(keyword in btn_text.lower() for keyword in ['am', 'pm', ':', '00']) or 'listbox' in (btn_id or ''):
                                    print(f"🔥 FOUND LIKELY TIME PICKER BUTTON: {btn_text}")
                                    box = await btn.bounding_box()
                                    if box:
                                        await page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
                                        await asyncio.sleep(0.5)
                                        await btn.click(force=True, timeout=3000)
                                        print(f"🔥 CLICKED LIKELY TIME PICKER: {btn_text}")
                                        break
                            except Exception as e:
                                print(f"Error checking button {idx+1}: {e}")
                        
                        available_times = []
                        raise Exception("Time picker button not found even after exhaustive search")

            # Step 3: Wait for the dropdown to appear - try multiple selectors for the new structure
            dropdown_found = False
            for attempt in range(5):  # Increased attempts
                try:
                    # Try the new structure first
                    await page.wait_for_selector('ul.grid.grid-cols-2.bg-white[role="listbox"]', timeout=2000)
                    print("Found time dropdown with new structure!")
                    dropdown_found = True
                    break
                except Exception:
                    try:
                        # Fallback to old structure
                        await page.wait_for_selector('ul[role="listbox"] li[role="option"]', timeout=2000)
                        print("Found time dropdown with old structure!")
                        dropdown_found = True
                        break
                    except Exception:
                        print(f"Dropdown not visible yet, retrying ({attempt+1}/5)...")
                        if not dropdown_open and time_picker_btn:
                            # Aggressively click again
                            try:
                                box = await time_picker_btn.bounding_box()
                                if box:
                                    await page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
                                    await asyncio.sleep(0.5)
                                    await page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                                    print("Retry: Aggressive mouse.click on time picker")
                            except Exception as e:
                                print(f"Retry click failed: {e}")
                            await asyncio.sleep(1)
            
            if not dropdown_found:
                print("❌ Dropdown did not appear after aggressive clicking. Trying to force it...")
                # Last resort: try to force the dropdown by clicking multiple times
                for force_attempt in range(3):
                    try:
                        if time_picker_btn:
                            box = await time_picker_btn.bounding_box()
                            if box:
                                await page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
                                await asyncio.sleep(0.3)
                                await page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                                await asyncio.sleep(0.3)
                                await page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                                print(f"Force attempt {force_attempt+1}: Double-clicked time picker")
                                await asyncio.sleep(1)
                                # Check if dropdown appeared
                                dropdown_check = await page.query_selector('ul.grid.grid-cols-2.bg-white[role="listbox"], ul[role="listbox"] li[role="option"]')
                                if dropdown_check:
                                    print("✅ Dropdown appeared after force click!")
                                    dropdown_found = True
                                    break
                    except Exception as e:
                        print(f"Force attempt {force_attempt+1} failed: {e}")
                
                if not dropdown_found:
                    available_times = []
                    raise Exception("Dropdown did not appear even after force clicks")

            # Step 4: Scrape the time options - handle both new and old structures
            available_times = []
            try:
                # Try new structure first
                time_options = await page.query_selector_all('ul.grid.grid-cols-2.bg-white[role="listbox"] li[role="option"] div')
                if time_options:
                    print(f"Found {len(time_options)} time slots with new structure")
                    for option in time_options:
                        text = (await option.inner_text()).strip()
                        if text:
                            available_times.append(text)
                else:
                    # Fallback to old structure
                    time_options = await page.query_selector_all('ul[role="listbox"] li[role="option"]')
                    print(f"Found {len(time_options)} time slots with old structure")
                    for option in time_options:
                        text = (await option.inner_text()).strip()
                        if text:
                            available_times.append(text)
                
                if available_times:
                    print("Available time slots:")
                    for idx, t in enumerate(available_times, 1):
                        print(f"{idx}. {t}")
                else:
                    print("No available time slots found.")
            except Exception as e:
                print(f"❌ Error scraping time options: {e}")
                available_times = []
        except Exception as e:
            print(f"❌ Could not scrape available time slots: {e}")
            available_times = []

        # Prompt for start time
        if available_times:
            start_time_input = input("Enter the number or time string of your desired slot: ").strip()
            # Try number selection
            try:
                num_choice = int(start_time_input) - 1
                if 0 <= num_choice < len(available_times):
                    start_time = available_times[num_choice]
                else:
                    print(f"Invalid number. Defaulting to first available time: {available_times[0]}")
                    start_time = available_times[0]
            except ValueError:
                # Try to match by string
                matches = [t for t in available_times if start_time_input.lower().replace(' ', '') in t.lower().replace(' ', '')]
                if matches:
                    start_time = matches[0]
                else:
                    print(f"No match found. Defaulting to first available time: {available_times[0]}")
                    start_time = available_times[0]
            
            # Now aggressively click the selected time slot
            print(f"Aggressively clicking on time slot: {start_time}")
            try:
                # Find all time slot divs
                time_slot_divs = await page.query_selector_all('ul.grid.grid-cols-2.bg-white[role="listbox"] li[role="option"] div')
                found = False
                
                for slot_div in time_slot_divs:
                    text = (await slot_div.inner_text()).strip()
                    if start_time.lower().replace(' ', '') == text.lower().replace(' ', ''):
                        # Aggressively click this time slot
                        try:
                            box = await slot_div.bounding_box()
                            if box:
                                print(f"Moving mouse to time slot at x={box['x']}, y={box['y']}, w={box['width']}, h={box['height']}")
                                await page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
                                await asyncio.sleep(0.5)
                                await slot_div.click(force=True, timeout=5000)
                                print(f"✅ Aggressively clicked time slot with element.click: {text}")
                                found = True
                                break
                            else:
                                print(f"❌ Could not get bounding box for time slot: {text}")
                        except Exception as e:
                            print(f"Element click failed for {text}: {e}")
                            if box:
                                try:
                                    await page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                                    print(f"✅ Aggressively clicked time slot with mouse.click: {text}")
                                    found = True
                                    break
                                except Exception as e2:
                                    print(f"Mouse click also failed for {text}: {e2}")
                
                if not found:
                    print(f"❌ Could not find time slot: {start_time}")
                    # Try clicking the first available slot as fallback
                    if time_slot_divs:
                        first_slot = time_slot_divs[0]
                        try:
                            box = await first_slot.bounding_box()
                            if box:
                                await page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
                                await asyncio.sleep(0.5)
                                await first_slot.click(force=True, timeout=5000)
                                print(f"✅ Clicked first available time slot: {(await first_slot.inner_text()).strip()}")
                            else:
                                await first_slot.click()
                                print(f"✅ Clicked first available time slot: {(await first_slot.inner_text()).strip()}")
                        except Exception as e:
                            print(f"❌ Error clicking first available time slot: {e}")
                
            except Exception as e:
                print(f"❌ Error during aggressive time slot selection: {e}")
            # Now, click the selected time option in the dropdown
            try:
                # Reopen the dropdown if needed
                dropdown = await page.query_selector('ul.grid.grid-cols-2.bg-white[role="listbox"], ul[role="listbox"]')
                visible = await dropdown.is_visible() if dropdown else False
                if not visible:
                    time_picker_btn = await page.query_selector('button#headlessui-listbox-button-8')
                    if time_picker_btn:
                        # Aggressively click to reopen
                        try:
                            box = await time_picker_btn.bounding_box()
                            if box:
                                await page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
                                await asyncio.sleep(0.5)
                                await page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                                print("Reopening dropdown with aggressive click")
                        except Exception as e:
                            print(f"Failed to reopen dropdown: {e}")
                        await asyncio.sleep(1)
                
                # Find and click the correct time option - try new structure first
                found = False
                time_options = await page.query_selector_all('ul.grid.grid-cols-2.bg-white[role="listbox"] li[role="option"] div')
                if time_options:
                    print(f"Found {len(time_options)} time options with new structure")
                    for option in time_options:
                        text = (await option.inner_text()).strip()
                        if start_time.lower().replace(' ', '') == text.lower().replace(' ', ''):
                            # Aggressively click the selected time
                            try:
                                box = await option.bounding_box()
                                if box:
                                    print(f"Moving mouse to time option at x={box['x']}, y={box['y']}, w={box['width']}, h={box['height']}")
                                    await page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
                                    await asyncio.sleep(0.5)
                                    await option.click(force=True, timeout=5000)
                                    print(f"✅ Selected time with element.click: {text}")
                                    found = True
                                    break
                                else:
                                    print(f"❌ Could not get bounding box for time option: {text}")
                            except Exception as e:
                                print(f"Element click failed for {text}: {e}")
                                if box:
                                    try:
                                        await page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                                        print(f"✅ Selected time with mouse.click: {text}")
                                        found = True
                                        break
                                    except Exception as e2:
                                        print(f"Mouse click also failed for {text}: {e2}")
                
                # Fallback to old structure if not found
                if not found:
                    time_options = await page.query_selector_all('ul[role="listbox"] li[role="option"]')
                    print(f"Trying old structure, found {len(time_options)} time options")
                    for option in time_options:
                        text = (await option.inner_text()).strip()
                        if start_time.lower().replace(' ', '') == text.lower().replace(' ', ''):
                            await option.click()
                            print(f"✅ Selected time with old structure: {text}")
                            found = True
                            break
                
                if not found:
                    # If not found, click the first available slot automatically
                    first_options = await page.query_selector_all('ul.grid.grid-cols-2.bg-white[role="listbox"] li[role="option"] div, ul[role="listbox"] li[role="option"]')
                    if first_options:
                        first_option = first_options[0]
                        try:
                            box = await first_option.bounding_box()
                            if box:
                                await page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
                                await asyncio.sleep(0.5)
                                await first_option.click(force=True, timeout=5000)
                                print(f"✅ Selected first available time: {(await first_option.inner_text()).strip()}")
                            else:
                                await first_option.click()
                                print(f"✅ Selected first available time: {(await first_option.inner_text()).strip()}")
                        except Exception as e:
                            print(f"❌ Error clicking first available time: {e}")
                    else:
                        print("❌ No time options available to click.")
            except Exception as e:
                print(f"❌ Error clicking selected time: {e}")
        else:
            # If no available times, fail gracefully
            print("❌ No available time slots to select.")

        # Prompt for duration
        def parse_duration(duration_input):
            import re
            duration_input = duration_input.lower().strip()
            # Match patterns like '1.5', '2', '2.0', '2 hrs', '2 hours', '1 hr 30 min', '90 min', etc.
            # 1. Check for 'min' only
            min_match = re.match(r"(\d+(?:\.\d+)?)\s*min", duration_input)
            if min_match:
                return float(min_match.group(1)) / 60
            # 2. Check for 'hr' and optional 'min'
            hr_min_match = re.match(r"(\d+(?:\.\d+)?)\s*hr[s]?\s*(\d+)?\s*min?", duration_input)
            if hr_min_match:
                hours = float(hr_min_match.group(1))
                mins = float(hr_min_match.group(2)) if hr_min_match.group(2) else 0
                return hours + mins / 60
            # 3. Check for 'hours' or 'hrs' only
            hr_match = re.match(r"(\d+(?:\.\d+)?)\s*(hr[s]?|hour[s]?)", duration_input)
            if hr_match:
                return float(hr_match.group(1))
            # 4. Check for '1 hr 30 min' (with spaces)
            hr_min_space_match = re.match(r"(\d+)\s*hr[s]?\s*(\d+)\s*min", duration_input)
            if hr_min_space_match:
                return float(hr_min_space_match.group(1)) + float(hr_min_space_match.group(2)) / 60
            # 5. Check for just a number (float or int)
            try:
                return float(duration_input)
            except ValueError:
                pass
            return None

        duration_input = input("How many hours do you want to book? (e.g., 1.5, 2 hrs, 1 hr 30 min, 90 min): ").strip()
        duration_hours = parse_duration(duration_input)
        if duration_hours is None or duration_hours <= 0:
            print("Invalid duration. Defaulting to 1 hour.")
            duration_hours = 1.0

        # Calculate clicks needed: default is 1 hour, each click adds 30 minutes
        default_duration = 1.0  # 1 hour
        clicks_needed = int(round((duration_hours - default_duration) / 0.5))

        if clicks_needed > 0:
            print(f"Clicking the plus button {clicks_needed} times to set duration to {duration_hours} hours...")
            for i in range(clicks_needed):
                try:
                    # Get current duration text before clicking
                    duration_text_el = await page.query_selector('div.text-sm.font-semibold.text-gray-700.capitalize')
                    current_duration = await duration_text_el.inner_text() if duration_text_el else "unknown"
                    print(f"Current duration before click {i+1}: {current_duration}")

                    # Find the SVG by its unique path
                    svg = await page.query_selector('svg:has(path[d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"])')
                    if svg:
                        box = await svg.bounding_box()
                        if box:
                            print(f"Moving mouse to SVG at x={box['x']}, y={box['y']}, w={box['width']}, h={box['height']}")
                            await page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
                            await asyncio.sleep(0.5)
                            await page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                            print("Clicked SVG center with mouse.")
                        else:
                            print("❌ Could not get bounding box for SVG.")
                        # Print SVG and parent outer HTML for debugging
                        svg_html = await svg.evaluate('(el) => el.outerHTML')
                        print(f"SVG outerHTML: {svg_html}")
                        parent = await svg.query_selector('xpath=..')
                        if parent:
                            parent_html = await parent.evaluate('(el) => el.outerHTML')
                            print(f"SVG parent outerHTML: {parent_html}")
                    else:
                        print("❌ Could not find the SVG plus icon by path.")
                    # Verify the duration text changed
                    new_duration_text_el = await page.query_selector('div.text-sm.font-semibold.text-gray-700.capitalize')
                    new_duration = await new_duration_text_el.inner_text() if new_duration_text_el else "unknown"
                    print(f"Duration after click {i+1}: {new_duration}")
                    if new_duration == current_duration:
                        print(f"⚠️ Duration text did not change after click {i+1}")
                    else:
                        print(f"✅ Duration text changed successfully")
                    print(f"Click {i+1}/{clicks_needed} completed")
                except Exception as e:
                    print(f"❌ Error on click {i+1}: {e}")
            print(f"✅ Set duration to {duration_hours} hours.")
        else:
            print(f"Duration is already set to {duration_hours} hours (default).")

        # Click the court selection dropdown (robust parent click)
        try:
            print("Attempting to click the court selection dropdown...")
            court_span = await page.query_selector('span.block.px-3.font-semibold.text-base.truncate')
            clickable = None
            if court_span:
                text = (await court_span.inner_text()).strip()
                if text == '--Select Court--':
                    # Walk up the DOM to find a clickable parent
                    parent = court_span
                    for _ in range(5):
                        parent = await parent.query_selector('xpath=..')
                        if not parent:
                            break
                        tag_handle = await parent.get_property('tagName')
                        tag = (await tag_handle.json_value()).lower() if tag_handle else ''
                        classes = await parent.get_attribute('class')
                        print(f"Checking parent <{tag}>.{classes}")
                        if tag == 'button' or (classes and 'cursor-pointer' in classes):
                            clickable = parent
                            print(f"Found clickable parent <{tag}>.{classes}")
                            break
                    if not clickable:
                        clickable = court_span
                        print("Falling back to clicking the span directly.")
                    box = await clickable.bounding_box()
                    if box:
                        print(f"Moving mouse to clickable at x={box['x']}, y={box['y']}, w={box['width']}, h={box['height']}")
                        await page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
                        await asyncio.sleep(0.5)
                        await clickable.click(force=True, timeout=5000)
                        print("Clicked court selection element with mouse.")
                    else:
                        print("❌ Could not get bounding box for clickable element.")
                else:
                    print(f"❌ Found span but text was '{text}' not '--Select Court--'.")
            else:
                print("❌ Could not find the court selection span.")
        except Exception as e:
            print(f"❌ Error clicking court selection dropdown: {e}")

        # Wait for the dropdown, scrape and select a court, then stop
        try:
            print("Scraping available court options...")
            await page.wait_for_selector('ul[role="listbox"]', timeout=5000)
            court_options = await page.query_selector_all('ul[role="listbox"] > div.cursor-pointer')
            courts = []
            for idx, option in enumerate(court_options):
                spans = await option.query_selector_all('span')
                name = (await spans[0].inner_text()).strip() if len(spans) > 0 else ''
                price = (await spans[1].inner_text()).strip() if len(spans) > 1 else ''
                courts.append({'name': name, 'price': price, 'el': option})
            if courts:
                print("Available courts:")
                for i, c in enumerate(courts, 1):
                    print(f"{i}. {c['name']} ({c['price']})")
                user_input = input("Which court do you want? Enter the number or name: ").strip()
                # Try number selection
                try:
                    num_choice = int(user_input) - 1
                    if 0 <= num_choice < len(courts):
                        choice = num_choice
                    else:
                        print(f"Invalid number. Defaulting to first court: {courts[0]['name']}")
                        choice = 0
                except ValueError:
                    # Try to match by name
                    matches = [i for i, c in enumerate(courts) if user_input.lower() in c['name'].lower()]
                    if matches:
                        choice = matches[0]
                    else:
                        print(f"No match found. Defaulting to first court: {courts[0]['name']}")
                        choice = 0
                # Aggressively click the selected court option (move mouse, click with force, try both element.click and mouse.click)
                selected = courts[choice]['el']
                box = await selected.bounding_box()
                if box:
                    print(f"Aggressively moving mouse to court at x={box['x']}, y={box['y']}, w={box['width']}, h={box['height']}")
                    await page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
                    await asyncio.sleep(0.5)
                    try:
                        await selected.click(force=True, timeout=5000)
                        print("Aggressive element.click succeeded.")
                    except Exception as e:
                        print(f"Aggressive element.click failed: {e}")
                        try:
                            await page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                            print("Aggressive mouse.click succeeded.")
                        except Exception as e2:
                            print(f"Aggressive mouse.click failed: {e2}")
                else:
                    print("❌ Could not get bounding box for selected court option.")
                print(f"Clicked court option: {courts[choice]['name']} ({courts[choice]['price']})")
                # Wait for the court to be visually selected
                try:
                    print("Waiting for court selection to be registered...")
                    await page.wait_for_function('''(el) => {
                        const btn = document.querySelector('button[aria-label=\"Add to Cart\"]');
                        if (!btn) return false;
                        const enabled = !btn.classList.contains('cursor-default') && !btn.classList.contains('text-gray-400');
                        return enabled;
                    }''', arg=selected, timeout=5000)
                    print("Court selection registered.")
                except Exception as e:
                    print(f"⚠️ Court selection may not be registered: {e}")
                
                # TEST CLICK: Aggressively click on the empty cart area
                print("🔥 TEST CLICK: Aggressively clicking on empty cart area...")
                try:
                    # Find the empty cart container
                    empty_cart_selectors = [
                        'div.hidden.w-full.md\\:block',
                        'div:has-text("Cart Is Empty")',
                        'div:has(img[src*="empty-cart.svg"])',
                        'div.font-semibold.texl-lg:has-text("Cart Is Empty")'
                    ]
                    
                    empty_cart_element = None
                    for selector in empty_cart_selectors:
                        try:
                            empty_cart_element = await page.query_selector(selector)
                            if empty_cart_element:
                                print(f"✅ Found empty cart area with selector: {selector}")
                                break
                        except Exception as e:
                            print(f"Selector {selector} failed: {e}")
                            continue
                    
                    if empty_cart_element:
                        # Get bounding box and click HARD
                        box = await empty_cart_element.bounding_box()
                        if box:
                            print(f"🔥 MOVING MOUSE TO EMPTY CART AREA at x={box['x']}, y={box['y']}, w={box['width']}, h={box['height']}")
                            
                            # Hover over the area first
                            await page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
                            await asyncio.sleep(1)  # Hover for 1 second
                            print("🔥 HOVERING OVER EMPTY CART AREA...")
                            
                            # Click HARD ONCE - MAKE IT COUNT!
                            print("🔥 CLICKING HARD ON EMPTY CART AREA - MAKE IT COUNT!")
                            
                            # Try element.click first with maximum force
                            try:
                                await empty_cart_element.click(force=True, timeout=5000)
                                print("🔥 ELEMENT.CLICK SUCCESS ON EMPTY CART - CLICKED HARD!")
                            except Exception as e:
                                print(f"🔥 Element click failed on empty cart: {e}")
                                # Try mouse.click as backup - CLICK HARD
                                try:
                                    await page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                                    print("🔥 MOUSE.CLICK SUCCESS ON EMPTY CART - CLICKED HARD!")
                                except Exception as e2:
                                    print(f"🔥 Mouse click failed on empty cart: {e2}")
                                    # Last resort: click different parts of the area
                                    try:
                                        await page.mouse.click(box['x'] + 10, box['y'] + 10)  # Top-left
                                        print("🔥 TOP-LEFT CLICK SUCCESS ON EMPTY CART - CLICKED HARD!")
                                    except Exception as e3:
                                        print(f"🔥 All click methods failed on empty cart: {e3}")
                        else:
                            print("❌ Could not get bounding box for empty cart area.")
                    else:
                        print("❌ Could not find empty cart area with any selector.")
                        
                except Exception as e:
                    print(f"❌ Error during test click on empty cart area: {e}")
                
                # ADD TO CART: Aggressively click on the Add to Cart button
                print("🔥 ADD TO CART: Aggressively clicking on Add to Cart button...")
                try:
                    # Find the Add to Cart button
                    add_to_cart_selectors = [
                        'button[aria-label="Add to Cart"]',
                        'button:has-text("Add To Cart")',
                        'button.px-3.text-sm.border-2.py-3.border-primary.bg-primary.text-white.rounded-md.font-semibold.md\\:px-2.w-full',
                        'button.bg-primary.text-white:has-text("Add")'
                    ]
                    
                    add_to_cart_button = None
                    for selector in add_to_cart_selectors:
                        try:
                            add_to_cart_button = await page.query_selector(selector)
                            if add_to_cart_button:
                                print(f"✅ Found Add to Cart button with selector: {selector}")
                                break
                        except Exception as e:
                            print(f"Selector {selector} failed: {e}")
                            continue
                    
                    if add_to_cart_button:
                        # Get bounding box and click HARD
                        box = await add_to_cart_button.bounding_box()
                        if box:
                            print(f"🔥 MOVING MOUSE TO ADD TO CART BUTTON at x={box['x']}, y={box['y']}, w={box['width']}, h={box['height']}")
                            
                            # Hover over the button first
                            await page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
                            await asyncio.sleep(1)  # Hover for 1 second
                            print("🔥 HOVERING OVER ADD TO CART BUTTON...")
                            
                            # Click HARD ONCE - MAKE IT COUNT!
                            print("🔥 CLICKING HARD ON ADD TO CART BUTTON - MAKE IT COUNT!")
                            
                            # Try element.click first with maximum force
                            try:
                                await add_to_cart_button.click(force=True, timeout=5000)
                                print("🔥 ELEMENT.CLICK SUCCESS ON ADD TO CART - CLICKED HARD!")
                            except Exception as e:
                                print(f"🔥 Element click failed on Add to Cart: {e}")
                                # Try mouse.click as backup - CLICK HARD
                                try:
                                    await page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                                    print("🔥 MOUSE.CLICK SUCCESS ON ADD TO CART - CLICKED HARD!")
                                except Exception as e2:
                                    print(f"🔥 Mouse click failed on Add to Cart: {e2}")
                                    # Last resort: click different parts of the button
                                    try:
                                        await page.mouse.click(box['x'] + 10, box['y'] + 10)  # Top-left
                                        print("🔥 TOP-LEFT CLICK SUCCESS ON ADD TO CART - CLICKED HARD!")
                                    except Exception as e3:
                                        print(f"🔥 All click methods failed on Add to Cart: {e3}")
                        else:
                            print("❌ Could not get bounding box for Add to Cart button.")
                    else:
                        print("❌ Could not find Add to Cart button with any selector.")
                        
                except Exception as e:
                    print(f"❌ Error during Add to Cart click: {e}")
                
                # PROCEED TO CHECKOUT: ULTRA AGGRESSIVE click on the Proceed to Checkout button
                print("🔥🔥🔥 PROCEED TO CHECKOUT: ULTRA AGGRESSIVE CLICKING ON PROCEED TO CHECKOUT BUTTON...")
                try:
                    # Find the Proceed to Checkout button
                    checkout_selectors = [
                        'button[aria-label="Proceed to Checkout"]',
                        'button:has-text("Proceed INR")',
                        'button:has-text("Proceed to Checkout")',
                        'button.px-3.text-md.border-2.py-3.bg-primary.border-primary.text-white.rounded-md.font-semibold.w-full',
                        'button.bg-primary.text-white:has-text("Proceed")'
                    ]
                    
                    checkout_button = None
                    for selector in checkout_selectors:
                        try:
                            checkout_button = await page.query_selector(selector)
                            if checkout_button:
                                print(f"✅ Found Proceed to Checkout button with selector: {selector}")
                                break
                        except Exception as e:
                            print(f"Selector {selector} failed: {e}")
                            continue
                    
                    if checkout_button:
                        # Get bounding box and click ULTRA HARD
                        box = await checkout_button.bounding_box()
                        if box:
                            print(f"🔥🔥🔥 MOVING MOUSE TO PROCEED TO CHECKOUT BUTTON at x={box['x']}, y={box['y']}, w={box['width']}, h={box['height']}")
                            
                            # Hover over the button first
                            await page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
                            await asyncio.sleep(1)  # Hover for 1 second
                            print("🔥🔥🔥 HOVERING OVER PROCEED TO CHECKOUT BUTTON...")
                            
                            # ULTRA AGGRESSIVE CLICK - MAKE IT COUNT!
                            print("🔥🔥🔥 ULTRA AGGRESSIVE CLICKING ON PROCEED TO CHECKOUT BUTTON - MAKE IT COUNT!")
                            
                            # Try element.click first with MAXIMUM force
                            try:
                                await checkout_button.click(force=True, timeout=10000)  # Longer timeout
                                print("🔥🔥🔥 ELEMENT.CLICK SUCCESS ON PROCEED TO CHECKOUT - CLICKED ULTRA HARD!")
                            except Exception as e:
                                print(f"🔥🔥🔥 Element click failed on Proceed to Checkout: {e}")
                                # Try mouse.click as backup - CLICK ULTRA HARD
                                try:
                                    await page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                                    print("🔥🔥🔥 MOUSE.CLICK SUCCESS ON PROCEED TO CHECKOUT - CLICKED ULTRA HARD!")
                                except Exception as e2:
                                    print(f"🔥🔥🔥 Mouse click failed on Proceed to Checkout: {e2}")
                                    # Last resort: click different parts of the button
                                    try:
                                        await page.mouse.click(box['x'] + 10, box['y'] + 10)  # Top-left
                                        print("🔥🔥🔥 TOP-LEFT CLICK SUCCESS ON PROCEED TO CHECKOUT - CLICKED ULTRA HARD!")
                                    except Exception as e3:
                                        print(f"🔥🔥🔥 All click methods failed on Proceed to Checkout: {e3}")
                                        # FINAL RESORT: Try clicking multiple times
                                        print("🔥🔥🔥 FINAL RESORT: Trying multiple clicks...")
                                        for final_attempt in range(3):
                                            try:
                                                await page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                                                await asyncio.sleep(0.2)
                                                print(f"🔥🔥🔥 Final attempt {final_attempt + 1} clicked!")
                                            except Exception as final_e:
                                                print(f"🔥🔥🔥 Final attempt {final_attempt + 1} failed: {final_e}")
                        else:
                            print("❌ Could not get bounding box for Proceed to Checkout button.")
                    else:
                        print("❌ Could not find Proceed to Checkout button with any selector.")
                        
                except Exception as e:
                    print(f"❌ Error during Proceed to Checkout click: {e}")
                
                print("🔥🔥🔥 BOOKING FLOW COMPLETE! 🔥🔥🔥")
                
            else:
                print("❌ No court options found.")
        except Exception as e:
            print(f"❌ Error scraping/selecting court: {e}")
        # Keep the browser open and wait for further instructions
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
