import time, telepot, helpers, os
from telepot.loop import MessageLoop
from loguru import logger
from os import path
from requests import get
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.alert import Alert

FORM_PREVIEW_PATH = './preview.png'
EDU_SITE_USER = os.getenv('EDU_SITE_USER')
EDU_SITE_PASSWORD = os.getenv('EDU_SITE_PASSWORD')
BOT_TOKEN = os.getenv('ALLOWED_IDS')
ALLOWED_IDS = os.getenv('ALLOWED_IDS')


def FillForm(bot, chat_id):
    try:
        logger.info("Start signing process")
        browser = helpers.GetBrowser()
        browser.get("https://parents.education.gov.il/prhnet/gov-education/corona/home-antigen-test#utm_source=sms&utm_medium=homeantigentest&utm_campaign=corona")
        helpers.log_browser(browser)
        time.sleep(2)
        element = WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, 'button-blue')))
        element.click()
        time.sleep(1)
        logger.info("Perform Login")
        browser.get("https://lgn.edu.gov.il/nidp/wsfed/ep?id=EduCombinedAuthUidPwd&sid=0&option=credential&sid=0")

        browser.find_element(By.XPATH,'//*[@id="HIN_USERID"]').send_keys(str(EDU_SITE_USER))
        browser.find_element(By.XPATH,'//*[@id="Ecom_Password"]').send_keys(str(EDU_SITE_PASSWORD))
        browser.find_element(By.XPATH,'//*[@id="loginButton2"]').click()

        logger.info("Logged in")
        time.sleep(1)
        logger.info("Mark as negative for covid")
        negative = browser.find_elements(By.CSS_SELECTOR,"[id^=lblNeg]")
        for radio in negative:
            radio.click()
        
        logger.info("Submiting form")
        browser.find_element(By.XPATH,'//button[text()="שליחה"]').click()
        time.sleep(1)
        alert = Alert(browser)
        bot.sendMessage(chat_id, alert.text)
        alert.accept()
        browser.find_element(By.CLASS_NAME,"agwrapper").screenshot(FORM_PREVIEW_PATH)
    
        if path.exists(FORM_PREVIEW_PATH):
            bot.sendPhoto(chat_id=chat_id,photo=open(FORM_PREVIEW_PATH, 'rb'))
        browser.close()    
    except Exception as e:
        bot.sendMessage(chat_id, "oh snap something went wrong")
        logger.error("oh snap something went wrong")
        logger.error(str(e))


def handle(msg):
    chat_id = msg['chat']['id']
    message_id = str(msg['message_id'])
    command = msg['text']
    if str(chat_id) not in os.getenv('ALLOWED_IDS'):
        bot.sendPhoto(
            chat_id, "https://github.com/t0mer/dockerbot/raw/master/No-Trespassing.gif")
        logger.error(f"[{message_id}] Chat id not allowed: {chat_id}")
        return
    if command == "/sign" or command=="/start":
        bot.sendMessage(chat_id, "signing process started")  
        FillForm(bot, chat_id)
        

bot = telepot.Bot(BOT_TOKEN)

if __name__ == '__main__':
    MessageLoop(bot, handle).run_as_thread()
    logger.info('I am listening...')
    while (True):
        a=1


