# Playo Sports Venue Booking Automation 🏆

An automated Python script using Playwright to book sports venues on [Playo.co](https://playo.co/). This script handles the complete booking flow from authentication to checkout, making it easy to secure your favorite sports venue quickly.

## ✨ Features

- **Complete Automation**: Handles login, sport selection, venue finding, and booking
- **Smart Venue Selection**: Filters out invalid venues and provides clean selection interface
- **Robust Error Handling**: Includes aggressive clicking and fallback mechanisms for reliable operation
- **Interactive User Interface**: Prompts for all necessary booking details
- **Visual Debugging**: Includes red mouse cursor for easy debugging
- **Modular Design**: Well-organized code structure for easy maintenance

## 🎯 Supported Sports & Features

- ✅ All sports available on Playo (Badminton, Tennis, Football, Cricket, etc.)
- ✅ Location-based venue search
- ✅ Date and time slot selection
- ✅ Duration customization
- ✅ Court selection
- ✅ Add to cart and checkout process

## 🚀 Quick Start

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd playo-booking-automation
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers:**
   ```bash
   playwright install chromium
   ```

### Usage

1. **Run the automation script:**
   ```bash
   python main.py
   ```

2. **Follow the interactive prompts:**
   - Enter your phone number for login
   - Enter OTP when received
   - Select your preferred sport
   - Choose location/area
   - Select venue from available options
   - Choose date (YYYY-MM-DD format)
   - Select time slot
   - Set duration (e.g., "1.5", "2 hrs", "90 min")
   - Select court
   - Complete checkout

## 📁 Project Structure

```
playo-booking-automation/
├── main.py                 # Main entry point
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore file
├── README.md             # This file
└── src/                  # Source code modules
    ├── __init__.py       # Package initialization
    ├── auth.py           # Authentication handling
    ├── venue_finder.py   # Venue search and selection
    ├── booking.py        # Booking flow management
    └── utils.py          # Utility functions
```

## ⚙️ Configuration

The script uses several configuration options in `config.py`:

### Location Settings
- **Default Location**: Bengaluru (latitude: 12.9352, longitude: 77.6762)
- You can modify `GEOLOCATION` in `config.py` for other cities

### Timing Settings
- **Default Timeout**: 10 seconds for most operations
- **OTP Wait Time**: 10 seconds before prompting for OTP
- **Hover/Click Delays**: 0.5 seconds for natural interaction

### Booking Settings
- **Default Duration**: 1 hour
- **Duration Increment**: 30 minutes per plus button click

## 🔧 Customization

### Adding New Selectors

If Playo updates their website, you may need to update selectors in `config.py`:

```python
SELECTORS = {
    "login_button": 'text=Login / Signup',
    "phone_input": 'input.rounded-l-none',
    # Add or modify selectors as needed
}
```

### Modifying Venue Filters

Update `VENUE_GARBAGE_PATTERNS` in `config.py` to filter out unwanted venue names:

```python
VENUE_GARBAGE_PATTERNS = [
    'featured', 'regular', 'playo', 'logo'
    # Add patterns to filter out
]
```

## 🛠️ Troubleshooting

### Common Issues

1. **Login Button Not Found**
   - The script might already be logged in
   - Check if you're redirected to the main page

2. **Venue Cards Not Loading**
   - Wait for the page to fully load
   - Check your internet connection
   - Verify location search results

3. **Time Slots Not Appearing**
   - The script uses aggressive clicking to open dropdowns
   - Some venues might not have available slots for selected dates

4. **Booking Flow Interruption**
   - The script keeps the browser open for manual intervention
   - You can complete any remaining steps manually

### Debug Mode

The script includes visual debugging features:
- Red mouse cursor shows automation actions
- Detailed console logging for each step
- Browser stays open for manual completion if needed

## 📝 Usage Examples

### Basic Booking Flow
```bash
python main.py
# Follow prompts:
# Phone: +91XXXXXXXXXX
# OTP: 12345
# Sport: Badminton (or select number)
# Location: HSR Layout
# Venue: Select from list
# Date: 2024-12-25
# Time: 06:00 AM (or select number)
# Duration: 1.5 hours
# Court: Court 1 (or select number)
```

### Advanced Duration Formats
The script accepts various duration formats:
- `1.5` (1.5 hours)
- `2 hrs` (2 hours)
- `90 min` (90 minutes = 1.5 hours)
- `1 hr 30 min` (1 hour 30 minutes)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test thoroughly
4. Commit your changes: `git commit -m "Add feature"`
5. Push to the branch: `git push origin feature-name`
6. Submit a pull request

## ⚠️ Important Notes

### Legal Considerations
- This script is for educational and personal use only
- Ensure you comply with Playo's Terms of Service
- Do not use for commercial purposes or abuse the platform
- Respect rate limits and don't overwhelm the server

### Reliability
- The script includes robust error handling and fallback mechanisms
- Browser automation can be affected by website changes
- Always verify booking details manually before payment

### Privacy
- Your login credentials are only used locally
- Browser data is stored in `playwright_user_data/` directory
- No personal information is transmitted to third parties

## 📄 License

This project is provided as-is for educational purposes. Please ensure you comply with all applicable terms of service and local laws when using this automation script.

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Verify your Python and Playwright installation
3. Ensure Playo website is accessible
4. Check for any website updates that might affect selectors

---

**Happy Booking! 🏸🎾⚽🏏**

*Automate your sports venue bookings and never miss your game time again!*
