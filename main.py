from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext
from playwright.sync_api import sync_playwright, Error as PlaywrightError, TimeoutError
#from dotenv import load_dotenv
from keep_alive import keep_alive
import os

#load_dotenv()
keep_alive()

# Replace with your actual bot token
TELEGRAM_BOT_TOKEN = os.environ.get('bot')

# List of email credentials (you should handle these securely)
EMAILS = [
    {'email': os.environ.get('e1'), 'password': os.environ.get('p1')},
    {'email': os.environ.get('e2'), 'password': os.environ.get('p2')},
    {'email': os.environ.get('e3'), 'password': os.environ.get('p3')},
    {'email': os.environ.get('e4'), 'password': os.environ.get('p4')},
    {'email': os.environ.get('e5'), 'password': os.environ.get('p5')},
]

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        'I am The Render billing screenshot bot\n\n'
        '/screenshot1 - fgbot1\n'
        '/screenshot2 - loader1\n'
        '/screenshot3 - ssbot\n'
        '/screenshot4 - fgbot2\n'
        '/screenshot5 - loader2\n'
        )

def screenshot(update: Update, context: CallbackContext, index: int) -> None:
    chat_id = update.message.chat_id
    
    if index < 1 or index > len(EMAILS):
        update.message.reply_text(f'Invalid screenshot number. Please use 1 to {len(EMAILS)}.')
        return
    
    email_info = EMAILS[index - 1]
    email = email_info['email']
    password = email_info['password']
    
    screenshot_path = f'screenshot{index}.png'
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Navigate to Render login page
            page.goto("https://dashboard.render.com/")
            
            # Perform login
            page.fill('input[name="email"]', email)
            page.fill('input[name="password"]', password)
            
            with page.expect_navigation():
                page.click('button[type="submit"]')
            
            # Check if login was successful
            if "login" in page.url:
                update.message.reply_text(f'Login failed for email {email}. Please check the credentials.')
                page.screenshot(path=f'failed_login_{index}.png')  # Capture screenshot if login fails
                browser.close()
                return
            
            # Navigate to the billing page
            page.goto("https://dashboard.render.com/billing#free-usage")
            
            # Increase the timeout and wait for the billing element
            billing_selector = '#free-usage, .type-body-03-medium.text-strong, .flex flex-col space-y-4, .w-4 h-4 button-compact-text--highlight'
            page.wait_for_selector(billing_selector, timeout=120000)
            
            # Take screenshot
            page.screenshot(path=screenshot_path)
            browser.close()
        
        # Send the screenshot via Telegram
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        bot.send_photo(chat_id=chat_id, photo=open(screenshot_path, 'rb'))
    except TimeoutError as e:
        update.message.reply_text('Timeout error while waiting for the billing element. Please check the selector and page load time.')
    except PlaywrightError as e:
        update.message.reply_text(f'Failed to capture screenshot: {e}')

def main() -> None:
    updater = Updater(TELEGRAM_BOT_TOKEN)

    updater.dispatcher.add_handler(CommandHandler("start", start))
    
    for i in range(1, 6):
        updater.dispatcher.add_handler(CommandHandler(f"screenshot{i}", lambda update, context, i=i: screenshot(update, context, i)))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    if not os.path.exists('playwright.config'):
        os.system('playwright install')

    main()
