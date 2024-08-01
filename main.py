import os
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.filters import Text
from aiogram.utils import executor
from playwright.async_api import async_playwright
from keep_alive import keep_alive
import logging

keep_alive()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get environment variables for bot and webhook
API_TOKEN = os.environ.get('bot')  # Telegram bot token
WEBHOOK_HOST = os.environ.get('host')  # Webhook host URL
WEBHOOK_PATH = f'/webhook/{API_TOKEN}'  # Webhook path
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"  # Full webhook URL

# List of email credentials (should be handled securely)
EMAILS = [
    {'email': os.environ.get('e1'), 'password': os.environ.get('p1')},
    {'email': os.environ.get('e2'), 'password': os.environ.get('p2')},
    {'email': os.environ.get('e3'), 'password': os.environ.get('p3')},
    {'email': os.environ.get('e4'), 'password': os.environ.get('p4')},
    {'email': os.environ.get('e5'), 'password': os.environ.get('p5')},
]

# Initialize the bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Webhook setup function
async def on_startup(dispatcher):
    await bot.set_webhook(WEBHOOK_URL)

# Webhook cleanup function
async def on_shutdown(dispatcher):
    logging.warning('Shutting down..')
    await bot.delete_webhook()
    logging.warning('Bye!')

# Handler for the /start command
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer(
        'I am The Render billing dashboard screenshot bot\n\n'
        '/screenshot1 - fgbot1\n'
        '/screenshot2 - loader1\n'
        '/screenshot3 - ssbot\n'
        '/screenshot4 - fgbot2\n'
        '/screenshot5 - loader2\n'
    )

# Handler for screenshot commands (/screenshot1, /screenshot2, ...)
@dp.message_handler(Text(startswith='/screenshot'))
async def screenshot(message: types.Message):
    command = message.text
    try:
        # Extract index number from command
        index = int(command.replace('/screenshot', ''))
    except ValueError:
        await message.answer('Invalid command. Please use /screenshot1, /screenshot2, etc.')
        return
    
    # Check if index is within the range of EMAILS
    if index < 1 or index > len(EMAILS):
        await message.answer(f'Invalid screenshot number. Please use 1 to {len(EMAILS)}.')
        return
    
    # Get the email and password for the specified index
    email_info = EMAILS[index - 1]
    email = email_info['email']
    password = email_info['password']
    
    screenshot_path = f'screenshot{index}.png'
    try:
        # Use Playwright to automate browser interaction
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)  # Launch browser in headless mode
            page = await browser.new_page()
            
            # Navigate to Render login page
            await page.goto("https://dashboard.render.com/")
            
            # Perform login
            await page.fill('input[name="email"]', email)
            await page.fill('input[name="password"]', password)
            await page.click('button[type="submit"]')

            # Wait for navigation to complete by checking for the dashboard URL or another element
            await page.wait_for_load_state('networkidle')

            # Check if login was successful
            if "login" in page.url:
                await message.answer(f'Login failed for email {email}. Please check the credentials.')
                await page.screenshot(path=f'failed_login_{index}.png')  # Capture screenshot if login fails
                await browser.close()
                return
            
            # Navigate to the billing page
            await page.goto("https://dashboard.render.com/billing#free-usage")
            
            # Wait for the billing page to fully load
            # await page.wait_for_load_state('networkidle')
            # Increase the timeout and wait for the billing element
            billing_selector = '#free-usage, .flex flex-col space-y-4, .type-body-03-medium.text-strong, .w-4 h-4 button-compact-text--highlight'
            await page.wait_for_selector(billing_selector, timeout=120000)  # 2 minutes timeout

            # Take screenshot
            await page.screenshot(path=screenshot_path)
            await browser.close()
        
        # Send the screenshot via Telegram
        with open(screenshot_path, 'rb') as photo:
            await bot.send_photo(chat_id=message.chat.id, photo=photo)
    except TimeoutError as e:
        logger.error(f'Timeout error while waiting for the billing element: {e}')
        await message.answer('Timeout error while waiting for the billing element. Please check the selector and page load time.')
    except Exception as e:
        logger.error(f'An unexpected error occurred: {e}')
        await message.answer(f'An unexpected error occurred: {e}')
    finally:
        # Remove screenshot file after sending
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)

# Start the bot
if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown)
