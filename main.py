import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram.dispatcher.filters import Text
from playwright.async_api import async_playwright, Error as PlaywrightError, TimeoutError
import os
from keep_alive import keep_alive
import subprocess

# Ensure Playwright dependencies are installed
#subprocess.run(["python", "install_playwright.py"], check=True)

keep_alive()

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Replace with your actual bot token
API_TOKEN = os.environ.get('bot')
WEBHOOK_HOST = os.environ.get('host')
WEBHOOK_PATH = f'/webhook/{API_TOKEN}'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# List of email credentials (you should handle these securely)
EMAILS = [
    {'email': os.environ.get('e1'), 'password': os.environ.get('p1')},
    {'email': os.environ.get('e2'), 'password': os.environ.get('p2')},
    {'email': os.environ.get('e3'), 'password': os.environ.get('p3')},
    {'email': os.environ.get('e4'), 'password': os.environ.get('p4')},
    {'email': os.environ.get('e5'), 'password': os.environ.get('p5')},
]

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

async def on_startup(dispatcher):
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(dispatcher):
    logging.warning('Shutting down..')
    await bot.delete_webhook()
    logging.warning('Bye!')

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer('Send\n/screenshot1\n/screenshot2\n/screenshot3\n/screenshot4\n/screenshot5\n to get the Render billing dashboard screenshot.')

@dp.message_handler(Text(startswith='/screenshot'))
async def screenshot(message: types.Message):
    command = message.text
    try:
        index = int(command.replace('/screenshot', ''))
    except ValueError:
        await message.answer('Invalid command. Please use /screenshot1, /screenshot2, etc.')
        return
    
    if index < 1 or index > len(EMAILS):
        await message.answer(f'Invalid screenshot number. Please use 1 to {len(EMAILS)}.')
        return
    
    email_info = EMAILS[index - 1]
    email = email_info['email']
    password = email_info['password']
    
    screenshot_path = f'screenshot{index}.png'
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Navigate to Render login page
            await page.goto("https://dashboard.render.com/")
            
            # Perform login
            await page.fill('input[name="email"]', email)
            await page.fill('input[name="password"]', password)
            
            await page.click('button[type="submit"]')
            await page.wait_for_navigation()
            
            # Check if login was successful
            if "login" in page.url:
                await message.answer(f'Login failed for email {email}. Please check the credentials.')
                await page.screenshot(path=f'failed_login_{index}.png')  # Capture screenshot if login fails
                await browser.close()
                return
            
            # Navigate to the billing page
            await page.goto("https://dashboard.render.com/billing#free-usage")
            
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
    except PlaywrightError as e:
        logger.error(f'Playwright error: {e}')
        await message.answer(f'Failed to capture screenshot: {e}')
    except Exception as e:
        logger.error(f'An unexpected error occurred: {e}')
        await message.answer(f'An unexpected error occurred: {e}')
    finally:
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)

if __name__ == '__main__':
    executor.start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host="0.0.0.0",
        port=int(os.environ.get('PORT', 8443)),
    )
