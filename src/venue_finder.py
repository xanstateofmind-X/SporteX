"""
Venue finder module for Playo booking automation.
Handles sport selection, location search, and venue selection.
"""

import asyncio
from typing import Dict, List, Optional
from config import SELECTORS, DEFAULT_TIMEOUT, LONG_TIMEOUT, VENUE_BATCH_SIZE, VENUE_GARBAGE_PATTERNS


class VenueFinder:
    """Handles venue discovery and selection functionality."""
    
    def __init__(self, page):
        self.page = page
    
    async def select_sport(self) -> Optional[str]:
        """
        Select a sport from the available options.
        
        Returns:
            str: Selected sport name, or None if selection failed
        """
        try:
            await self._scroll_to_sports_section()
            sports = await self._scrape_sports()
            
            if not sports:
                print("❌ No sports found")
                return None
            
            selected_sport = await self._prompt_sport_selection(sports)
            await self._click_sport(sports[selected_sport])
            
            return sports[selected_sport]['name']
            
        except Exception as e:
            print(f"❌ Error in sport selection: {e}")
            return None
    
    async def select_venue(self) -> Optional[Dict]:
        """
        Handle location search and venue selection.
        
        Returns:
            Dict: Selected venue information, or None if selection failed
        """
        try:
            # Get location preference
            location = input(
                "Which area do you want to search for venues in? "
                "(e.g., Bellandur, HSR, Koramangala): "
            ).strip()
            
            if location:
                await self._search_location(location)
            
            # Scrape and select venue
            venues = await self._scrape_venues()
            if not venues:
                print("❌ No venues found")
                return None
            
            selected_venue_idx = await self._prompt_venue_selection(venues)
            selected_venue = venues[selected_venue_idx]
            
            await self._click_venue(selected_venue)
            
            return selected_venue
            
        except Exception as e:
            print(f"❌ Error in venue selection: {e}")
            return None
    
    async def _scroll_to_sports_section(self):
        """Scroll to the Popular Sports section."""
        print("📜 Scrolling to Popular Sports section...")
        try:
            await self.page.wait_for_selector(SELECTORS["popular_sports_header"], timeout=LONG_TIMEOUT)
            await self.page.evaluate("""
                () => {
                    const el = Array.from(document.querySelectorAll('h3'))
                        .find(e => e.textContent.trim() === 'Popular Sports');
                    if (el) el.scrollIntoView({behavior: 'smooth', block: 'center'});
                }
            """)
            print("✅ Popular Sports section is now visible")
        except Exception as e:
            print(f"⚠️ Could not scroll to Popular Sports section: {e}")
    
    async def _scrape_sports(self) -> List[Dict]:
        """Scrape available sports from the page."""
        print("🔍 Scraping available sports...")
        try:
            await self.page.wait_for_selector(SELECTORS["sports_container"], timeout=DEFAULT_TIMEOUT)
            sports_container = await self.page.query_selector(SELECTORS["sports_container"])
            
            if not sports_container:
                return []
            
            sport_cards = await sports_container.query_selector_all(SELECTORS["sport_cards"])
            sports = []
            
            for idx, card in enumerate(sport_cards):
                name_div = await card.query_selector(SELECTORS["sport_name"])
                name = (await name_div.inner_text()).strip() if name_div else f"Sport {idx+1}"
                sports.append({'name': name, 'el': card})
            
            return sports
            
        except Exception as e:
            print(f"❌ Error scraping sports: {e}")
            return []
    
    async def _prompt_sport_selection(self, sports: List[Dict]) -> int:
        """Prompt user to select a sport."""
        print("Available sports:")
        for i, sport in enumerate(sports, 1):
            print(f"{i}. {sport['name']}")
        
        user_input = input("Which sport do you want? Enter the number or name: ").strip()
        
        # Try number selection
        try:
            num_choice = int(user_input) - 1
            if 0 <= num_choice < len(sports):
                return num_choice
            else:
                print(f"Invalid number. Defaulting to first sport: {sports[0]['name']}")
                return 0
        except ValueError:
            # Try name matching
            matches = [i for i, s in enumerate(sports) if user_input.lower() in s['name'].lower()]
            if matches:
                return matches[0]
            else:
                print(f"No match found. Defaulting to first sport: {sports[0]['name']}")
                return 0
    
    async def _click_sport(self, sport: Dict):
        """Aggressively click the selected sport card."""
        selected = sport['el']
        box = await selected.bounding_box()
        
        if box:
            print(f"🎯 Clicking sport: {sport['name']}")
            await self.page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
            await asyncio.sleep(0.5)
            
            try:
                await selected.click(force=True, timeout=5000)
                print("✅ Sport clicked successfully")
            except Exception as e:
                print(f"Element click failed: {e}, trying mouse click")
                try:
                    await self.page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                    print("✅ Sport clicked with mouse")
                except Exception as e2:
                    print(f"❌ Both click methods failed: {e2}")
        else:
            print("❌ Could not get bounding box for sport card")
    
    async def _search_location(self, location: str):
        """Search for a specific location."""
        print(f"🔍 Searching for location: {location}")
        try:
            await self.page.wait_for_selector(SELECTORS["search_input"], timeout=DEFAULT_TIMEOUT)
            await self.page.fill(SELECTORS["search_input"], location)
            await self.page.press(SELECTORS["search_input"], 'Enter')
            print(f"✅ Location search triggered for {location}")
            await asyncio.sleep(2)
        except Exception as e:
            print(f"❌ Could not search location: {e}")
    
    async def _scrape_venues(self) -> List[Dict]:
        """Scrape venue information from the page."""
        print("🏢 Scraping venue information...")
        await asyncio.sleep(3)  # Wait for venues to load
        
        # Try multiple selectors for venue cards
        card_els = []
        for selector in SELECTORS["venue_cards"]:
            try:
                card_els = await self.page.query_selector_all(selector)
                if card_els:
                    print(f"✅ Found {len(card_els)} venue cards")
                    break
            except Exception as e:
                print(f"Selector failed: {e}")
                continue
        
        if not card_els:
            print("❌ No venue cards found")
            return []
        
        venues = []
        for idx, card in enumerate(card_els):
            try:
                venue_info = await self._extract_venue_info(card, idx)
                if venue_info and self._is_valid_venue(venue_info['name']):
                    venues.append(venue_info)
                    print(f"Venue {len(venues)}: {venue_info['name']} — {venue_info['distance']}")
                
            except Exception as e:
                print(f"Error processing card {idx+1}: {e}")
                continue
        
        # Remove duplicates
        return self._remove_duplicate_venues(venues)
    
    async def _extract_venue_info(self, card, idx: int) -> Optional[Dict]:
        """Extract venue information from a venue card element."""
        # Extract name
        name = ''
        for name_selector in SELECTORS["venue_name_selectors"]:
            name_el = await card.query_selector(name_selector)
            if name_el:
                name = (await name_el.inner_text()).strip()
                if name and len(name) > 3:
                    break
        
        # Extract distance
        distance = ''
        for dist_selector in SELECTORS["venue_distance_selectors"]:
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
        
        # Parse venue name and location
        if ' - ' in name:
            venue, location = name.rsplit(' - ', 1)
        else:
            venue, location = name, ''
        
        return {
            'name': name,
            'venue': venue,
            'location': location,
            'distance': distance,
            'el': card,
            'index': idx
        }
    
    def _is_valid_venue(self, name: str) -> bool:
        """Check if venue name is valid (not garbage data)."""
        if not name or len(name) <= 5:
            return False
        
        name_lower = name.lower()
        return not any(pattern in name_lower for pattern in VENUE_GARBAGE_PATTERNS)
    
    def _remove_duplicate_venues(self, venues: List[Dict]) -> List[Dict]:
        """Remove duplicate venues based on name."""
        seen = set()
        unique_venues = []
        for venue in venues:
            if venue['name'] not in seen:
                unique_venues.append(venue)
                seen.add(venue['name'])
        return unique_venues
    
    async def _prompt_venue_selection(self, venues: List[Dict]) -> int:
        """Prompt user to select a venue with pagination."""
        if len(venues) == 1:
            dist_str = f"{venues[0]['distance']} from your current location" if venues[0]['distance'] else "distance unknown"
            print(f"Only one venue found: {venues[0]['name']} — {dist_str}")
            return 0
        
        start = 0
        while True:
            print("Available venues:")
            for i in range(start, min(start + VENUE_BATCH_SIZE, len(venues))):
                venue = venues[i]
                dist_str = f"{venue['distance']} from your current location" if venue['distance'] else "distance unknown"
                print(f"{i+1}. {venue['name']} — {dist_str}")
            
            if start + VENUE_BATCH_SIZE >= len(venues):
                prompt = "Enter the number (1-N) or name of your choice: "
            else:
                prompt = "Type 'more' to see more venues, or enter the number (1-N) or name of your choice: "
            
            user_input = input(prompt).strip()
            
            if user_input.lower() == 'more' and start + VENUE_BATCH_SIZE < len(venues):
                start += VENUE_BATCH_SIZE
                continue
            
            # Try number selection
            try:
                num_choice = int(user_input) - 1
                if 0 <= num_choice < len(venues):
                    return num_choice
                else:
                    print(f"Please enter a number between 1 and {len(venues)}")
                    continue
            except ValueError:
                pass
            
            # Try name selection
            matches = [idx for idx, v in enumerate(venues) if user_input.lower() in v['name'].lower()]
            if len(matches) == 1:
                print(f"Selected venue by name: {venues[matches[0]]['name']}")
                return matches[0]
            elif len(matches) > 1:
                print("Multiple venues match that name. Please be more specific or use the number.")
            else:
                print("Venue not found. Please try again.")
    
    async def _click_venue(self, venue: Dict):
        """Click the selected venue."""
        await venue['el'].scroll_into_view_if_needed()
        await venue['el'].click()
        print(f"✅ Selected venue: {venue['name']}")
