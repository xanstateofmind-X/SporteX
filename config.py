"""
Configuration settings for Playo booking automation.
"""

import os

# Browser Configuration
USER_DATA_DIR = os.path.join(os.getcwd(), "playwright_user_data")
GEOLOCATION = {"latitude": 12.9352, "longitude": 77.6762}  # Bengaluru coordinates

# Timing Configuration (in milliseconds)
DEFAULT_TIMEOUT = 10000
SHORT_TIMEOUT = 5000
LONG_TIMEOUT = 15000
HOVER_DELAY = 0.5
CLICK_DELAY = 0.5
OTP_WAIT_TIME = 10  # seconds

# Booking Configuration
DEFAULT_DURATION_HOURS = 1.0
DURATION_INCREMENT = 0.5  # Each plus click adds 30 minutes

# Venue Display Configuration
VENUE_BATCH_SIZE = 3

# Selectors - organized by functionality
SELECTORS = {
    # Authentication
    "login_button": 'text=Login / Signup',
    "phone_input": 'input.rounded-l-none',
    "send_otp_button": 'button.bg-primary.new-button',
    "otp_inputs": 'input#otp-part{i}',  # {i} will be replaced with digit position
    "verify_button": 'button.bg-primary.new-button:has-text("VERIFY")',
    "error_modal_ok": 'button.bg-error.text-on_error',
    
    # Sports Selection
    "popular_sports_header": 'h3:has-text("Popular Sports")',
    "sports_container": 'div.flex.mt-6.gap-6.overflow-x-auto',
    "sport_cards": 'div.relative.cursor-pointer',
    "sport_name": 'div.absolute.text-white.font-bold',
    
    # Location/Search
    "search_input": 'input[placeholder*="Search"]',
    
    # Venue Selection
    "venue_cards": [
        'div.grid.w-full.grid-cols-1.gap-11 > div.border_radius.bg-white.card_shadow.pb-2.cursor-pointer:has(img[src*="gumlet"]):has(div[class*="truncate"])',
        'div[class*="card_shadow"][class*="cursor-pointer"]:has(img[src*="gumlet"]):has(div[class*="truncate"])'
    ],
    "venue_name_selectors": [
        '.title_large',
        '[class*="title_large"]',
        'div[class*="truncate"][class*="text-"]',
        'div[class*="font-"]:not([class*="text-xs"])'
    ],
    "venue_distance_selectors": [
        '.overflow-hidden.truncate',
        '[class*="overflow-hidden"][class*="truncate"]',
        'div:contains("km")',
        'span:contains("km")'
    ],
    
    # Booking Flow
    "book_now_button": 'button[aria-label="Book Now"]',
    "sport_selector_button": 'button[aria-haspopup="true"]',
    "sport_dropdown": 'ul[role="listbox"]',
    "sport_options": 'ul[role="listbox"] li[role="option"]',
    
    # Date Selection
    "date_picker_button": 'button#headlessui-popover-button-6',
    "calendar_popover": 'div[id^="headlessui-popover-panel-"]',
    "calendar_days": 'div[id^="headlessui-popover-panel-"] div.cursor-pointer.font-medium',
    
    # Time Selection
    "time_picker_buttons": [
        'button#headlessui-listbox-button-8',
        'button[aria-haspopup="true"][aria-expanded="false"]',
        'button.relative.flex.flex-row.items-center.w-full.h-12.px-3.bg-white.border.rounded-lg.cursor-pointer',
        'button:has(span.block.font-semibold.truncate)',
        'button[aria-haspopup="true"]'
    ],
    "time_slots_new": 'ul.grid.grid-cols-2.bg-white[role="listbox"] li[role="option"] div',
    "time_slots_old": 'ul[role="listbox"] li[role="option"]',
    
    # Duration
    "duration_text": 'div.text-sm.font-semibold.text-gray-700.capitalize',
    "plus_button_svg": 'svg:has(path[d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"])',
    
    # Court Selection
    "court_selector_span": 'span.block.px-3.font-semibold.text-base.truncate',
    "court_options": 'ul[role="listbox"] > div.cursor-pointer',
    
    # Cart and Checkout
    "add_to_cart_buttons": [
        'button[aria-label="Add to Cart"]',
        'button:has-text("Add To Cart")',
        'button.px-3.text-sm.border-2.py-3.border-primary.bg-primary.text-white.rounded-md.font-semibold.md\\:px-2.w-full',
        'button.bg-primary.text-white:has-text("Add")'
    ],
    "checkout_buttons": [
        'button[aria-label="Proceed to Checkout"]',
        'button:has-text("Proceed INR")',
        'button:has-text("Proceed to Checkout")',
        'button.px-3.text-md.border-2.py-3.bg-primary.border-primary.text-white.rounded-md.font-semibold.w-full',
        'button.bg-primary.text-white:has-text("Proceed")'
    ]
}

# Garbage filter patterns for venue names
VENUE_GARBAGE_PATTERNS = [
    'featured', 'regular', 'mixed doubles', 'doubles', 'singles',
    'badminton', 'football', 'cricket', 'swimming', 'tennis', 'table tennis',
    '3.39', '2.91', '4.2', '4.5', '4.8', '4.9', '5.0',  # Rating patterns
    'playo', 'logo', 'menu', 'search', 'filter'
]
