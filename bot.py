"""
PowerPlay Lead Claimer Bot
Automatically detects and claims new leads on the Generac PowerPlay portal
"""
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
    TimeoutError as PlaywrightTimeoutError,
)

from config import Config
from email_sender import send_lead_email

logger = logging.getLogger(__name__)


class PowerPlayBot:
    """Main bot class for PowerPlay lead claiming automation"""

    def __init__(self):
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.is_logged_in: bool = False
        self.claims_count: int = 0

    async def initialize(self) -> None:
        """Initialize Playwright and browser"""
        logger.info("Initializing browser...")
        self.playwright = await async_playwright().start()

        # Launch browser with optimized settings
        self.browser = await self.playwright.chromium.launch(
            headless=Config.HEADLESS,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

        # Create browser context with realistic settings
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
        )

        # Set default timeouts
        self.context.set_default_timeout(Config.PAGE_LOAD_TIMEOUT)

        # Create new page
        self.page = await self.context.new_page()

        logger.info("Browser initialized successfully")

    async def login(self) -> bool:
        """
        Perform login to PowerPlay portal
        PowerPlay uses a two-step login process:
        1. Enter email and click Continue
        2. Enter password and submit

        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            logger.info("Navigating to login page...")
            await self.page.goto(Config.LOGIN_URL, wait_until="networkidle")
            await asyncio.sleep(1)  # Brief pause for page to settle

            logger.info("Step 1: Entering email address...")

            # Step 1: Wait for and fill email field
            email_selector = 'input[type="email"], input[name*="email"], input[id*="email"], input[autocomplete="username"]'
            try:
                await self.page.wait_for_selector(email_selector, timeout=10000, state="visible")
                await self.page.fill(email_selector, Config.USERNAME)
                logger.info("Email entered successfully")
            except PlaywrightTimeoutError:
                logger.error("Could not find email input field")
                await self._take_screenshot("email_field_not_found")
                return False

            # Click Continue button - use Enter key (most reliable)
            logger.info("Submitting email (pressing Enter)...")
            await asyncio.sleep(0.5)  # Brief pause after typing email

            # Press Enter to submit the form - this is most reliable
            await self.page.keyboard.press('Enter')
            logger.info("✓ Pressed Enter to submit email")

            # Wait for navigation to password page
            logger.info("Waiting for password page to load...")
            try:
                await self.page.wait_for_load_state("networkidle", timeout=10000)
                await asyncio.sleep(1)
            except:
                await asyncio.sleep(2)  # Fallback wait

            logger.info("Step 2: Entering password...")

            # Step 2: Wait for and fill password field
            password_selector = 'input[type="password"], input[name*="password"], input[id*="password"], input[autocomplete*="password"]'
            try:
                await self.page.wait_for_selector(password_selector, timeout=10000, state="visible")
                await self.page.fill(password_selector, Config.PASSWORD)
                logger.info("Password entered successfully")
            except PlaywrightTimeoutError:
                logger.error("Could not find password input field")
                await self._take_screenshot("password_field_not_found")
                return False

            # Click final login/submit button - try multiple approaches
            await asyncio.sleep(0.5)  # Brief pause after typing password

            login_selectors = [
                'button[type="submit"]',
                'button:has-text("Sign In")',
                'button:has-text("Login")',
                'button:has-text("Continue")',
                'button.MuiButton-root',
                'button',  # Any button
            ]

            login_clicked = False
            for selector in login_selectors:
                try:
                    button = await self.page.wait_for_selector(selector, timeout=2000, state="visible")
                    if button:
                        await button.click()
                        logger.info(f"Clicked login button using selector: {selector}")
                        login_clicked = True
                        break
                except:
                    continue

            if not login_clicked:
                logger.error("Could not find login button with any selector")
                await self._take_screenshot("login_button_not_found")
                # Try pressing Enter as fallback
                logger.info("Trying Enter key as fallback for login...")
                await self.page.keyboard.press('Enter')
                login_clicked = True

            logger.info("Credentials submitted, waiting for dashboard...")

            # Wait for navigation after login
            await self.page.wait_for_load_state("networkidle", timeout=30000)
            await asyncio.sleep(3)  # Give the dashboard time to fully load

            # Verify login success by checking URL
            current_url = self.page.url
            logger.info(f"Current URL after login: {current_url}")

            # Check if we're successfully logged in
            if "login" not in current_url.lower() and "identifier" not in current_url.lower():
                self.is_logged_in = True
                logger.info("✓ Login successful!")
                await self._take_screenshot("login_success")
                return True
            else:
                logger.error("Login failed - still on login page")
                await self._take_screenshot("login_failed")
                return False

        except PlaywrightTimeoutError as e:
            logger.error(f"Login timeout: {e}")
            await self._take_screenshot("login_timeout")
            return False
        except Exception as e:
            logger.error(f"Login error: {e}", exc_info=True)
            await self._take_screenshot("login_error")
            return False

    async def monitor_and_claim_leads(self) -> None:
        """
        Main loop: Monitor for new leads and claim them immediately
        Uses fast polling for sub-second response times
        """
        logger.info("🔍 Starting lead monitoring loop...")
        logger.info(f"Polling interval: {Config.POLLING_INTERVAL_MS}ms")

        consecutive_errors = 0
        max_consecutive_errors = 10

        while True:
            try:
                # Check if page is still valid
                if not self.page or self.page.is_closed():
                    logger.warning("Page closed, reinitializing...")
                    await self._handle_session_recovery()
                    continue

                # Look for claim buttons
                # Adjust these selectors based on actual PowerPlay HTML structure
                claim_button_selectors = [
                    'button:has-text("Claim")',
                    'button[aria-label*="Claim"]',
                    'a:has-text("Claim")',
                    '.claim-button',
                    '[data-action="claim"]',
                ]

                claim_button = None
                for selector in claim_button_selectors:
                    try:
                        claim_button = await self.page.wait_for_selector(
                            selector, timeout=Config.POLLING_INTERVAL_MS, state="visible"
                        )
                        if claim_button:
                            break
                    except PlaywrightTimeoutError:
                        continue

                if claim_button:
                    # Lead detected! Claim it immediately
                    await self._claim_lead(claim_button)
                    consecutive_errors = 0
                else:
                    # No lead found, continue monitoring
                    # Small delay to prevent excessive CPU usage
                    await asyncio.sleep(Config.POLLING_INTERVAL_MS / 1000)

                consecutive_errors = 0

            except PlaywrightTimeoutError:
                # Timeout is expected when no leads are available
                await asyncio.sleep(Config.POLLING_INTERVAL_MS / 1000)
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                await self._take_screenshot("monitoring_error")

                if consecutive_errors >= max_consecutive_errors:
                    logger.error("Too many consecutive errors, attempting recovery...")
                    await self._handle_session_recovery()
                    consecutive_errors = 0
                else:
                    await asyncio.sleep(1)

    async def _extract_lead_info(self) -> dict:
        """
        Extract lead contact details from the page after claiming.
        Tries common selectors; returns whatever fields are found.
        """
        info = {}
        field_selectors = {
            "name":  ['[data-field="name"]', '.lead-name', '.customer-name',
                      'h1.name', 'td:has-text("Name") + td'],
            "email": ['[data-field="email"]', '.lead-email', '.customer-email',
                      'a[href^="mailto:"]', 'td:has-text("Email") + td'],
            "phone": ['[data-field="phone"]', '.lead-phone', '.customer-phone',
                      'td:has-text("Phone") + td'],
        }
        for field, selectors in field_selectors.items():
            for sel in selectors:
                try:
                    el = await self.page.query_selector(sel)
                    if el:
                        text = await el.inner_text()
                        text = text.strip()
                        if text:
                            info[field] = text
                            break
                except Exception:
                    continue

        if "email" not in info:
            # Last-resort: scan all mailto links on the page
            try:
                links = await self.page.query_selector_all('a[href^="mailto:"]')
                if links:
                    href = await links[0].get_attribute("href")
                    info["email"] = href.replace("mailto:", "").strip()
            except Exception:
                pass

        logger.debug(f"Extracted lead info: {info}")
        return info

    async def _claim_lead(self, claim_button) -> None:
        """
        Click the claim button, then send a notification email to the lead.
        """
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            logger.info(f"🎯 LEAD DETECTED at {timestamp}! Claiming now...")

            await claim_button.click()
            await asyncio.sleep(1)

            success_indicators = [
                'text="Successfully claimed"',
                'text="Claim successful"',
                '.success-message',
                '[role="alert"]:has-text("success")',
            ]
            for indicator in success_indicators:
                try:
                    await self.page.wait_for_selector(indicator, timeout=2000)
                    break
                except PlaywrightTimeoutError:
                    continue

            self.claims_count += 1
            logger.info(f"✓ Lead claimed successfully! Total claims: {self.claims_count}")

            await self._take_screenshot(f"claim_success_{self.claims_count}")

            if Config.ENABLE_SOUND_NOTIFICATION:
                await self._play_notification_sound()

            # Extract lead contact info and send notification email
            lead_info = await self._extract_lead_info()
            send_lead_email(lead_info)

        except Exception as e:
            logger.error(f"Error claiming lead: {e}", exc_info=True)
            await self._take_screenshot("claim_error")

    async def _handle_session_recovery(self) -> None:
        """Handle session expiration or page errors by re-logging in"""
        logger.warning("Attempting session recovery...")

        try:
            # Close existing page if it exists
            if self.page and not self.page.is_closed():
                await self.page.close()

            # Create new page
            self.page = await self.context.new_page()

            # Attempt to login again
            self.is_logged_in = False
            login_success = await self.login()

            if not login_success:
                logger.error("Session recovery failed - login unsuccessful")
                await asyncio.sleep(Config.RETRY_DELAY_SECONDS)
            else:
                logger.info("Session recovered successfully")

        except Exception as e:
            logger.error(f"Error during session recovery: {e}", exc_info=True)
            await asyncio.sleep(Config.RETRY_DELAY_SECONDS)

    async def _take_screenshot(self, name: str) -> None:
        """
        Take a screenshot for debugging

        Args:
            name: Name prefix for the screenshot file
        """
        if not Config.ENABLE_SCREENSHOTS:
            return

        try:
            if self.page and not self.page.is_closed():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = Config.SCREENSHOTS_DIR / f"{name}_{timestamp}.png"
                await self.page.screenshot(path=str(screenshot_path), full_page=True)
                logger.debug(f"Screenshot saved: {screenshot_path}")
        except Exception as e:
            logger.warning(f"Failed to take screenshot: {e}")

    async def _play_notification_sound(self) -> None:
        """Play system beep sound notification"""
        try:
            # Use system beep on Linux
            if sys.platform == "linux":
                import subprocess

                subprocess.run(["paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"], check=False)
            # Add Windows/Mac support as needed
        except Exception as e:
            logger.debug(f"Could not play notification sound: {e}")

    async def run(self) -> None:
        """Main entry point for the bot"""
        retry_count = 0

        while True:
            try:
                # Initialize browser
                await self.initialize()

                # Login
                login_success = await self.login()

                if not login_success:
                    retry_count += 1
                    if retry_count >= Config.MAX_RETRIES:
                        logger.error("Max login retries reached. Exiting.")
                        break

                    logger.warning(f"Login failed. Retrying in {Config.RETRY_DELAY_SECONDS}s... ({retry_count}/{Config.MAX_RETRIES})")
                    await asyncio.sleep(Config.RETRY_DELAY_SECONDS)
                    await self.cleanup()
                    continue

                # Reset retry count on successful login
                retry_count = 0

                # Start monitoring for leads
                await self.monitor_and_claim_leads()

            except KeyboardInterrupt:
                logger.info("\n🛑 Bot stopped by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}", exc_info=True)

                if Config.ENABLE_AUTO_RESTART:
                    logger.info(f"Auto-restarting in {Config.RETRY_DELAY_SECONDS}s...")
                    await asyncio.sleep(Config.RETRY_DELAY_SECONDS)
                    await self.cleanup()
                else:
                    break

        await self.cleanup()

    async def cleanup(self) -> None:
        """Clean up browser resources"""
        logger.info("Cleaning up resources...")

        try:
            if self.page and not self.page.is_closed():
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")

        logger.info("Cleanup complete")
