"""
PowerPlay Lead Claimer - Main Entry Point
Automatically claims new leads on the Generac PowerPlay portal
"""
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

from bot import PowerPlayBot
from config import Config


def setup_logging() -> None:
    """Configure logging for the application"""
    # Create formatters
    console_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Setup console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, Config.LOG_LEVEL))
    console_handler.setFormatter(console_formatter)

    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)

    # Setup file handler if enabled
    if Config.LOG_TO_FILE:
        log_file = Config.LOGS_DIR / f"bot_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Reduce noise from playwright
    logging.getLogger("playwright").setLevel(logging.WARNING)


def print_banner() -> None:
    """Print application banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║           PowerPlay Lead Claimer Bot v1.0                    ║
║           Automated Lead Claiming System                     ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)
    print(f"Headless Mode: {Config.HEADLESS}")
    print(f"Polling Interval: {Config.POLLING_INTERVAL_MS}ms")
    print(f"Sound Notifications: {Config.ENABLE_SOUND_NOTIFICATION}")
    print(f"Screenshots: {Config.ENABLE_SCREENSHOTS}")
    print(f"Auto Restart: {Config.ENABLE_AUTO_RESTART}")
    print("═" * 62)
    print()


async def main() -> None:
    """Main application entry point"""
    try:
        # Ensure required directories exist
        Config.ensure_directories()

        # Setup logging
        setup_logging()

        # Print banner
        print_banner()

        # Validate configuration
        Config.validate()

        # Create and run bot
        logger = logging.getLogger(__name__)
        logger.info("Starting PowerPlay Lead Claimer Bot...")

        bot = PowerPlayBot()
        await bot.run()

    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\nPlease check your .env file and ensure all required variables are set.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Bot stopped by user (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    # Run the async main function
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n🛑 Bot stopped by user (Ctrl+C)")
        sys.exit(0)
