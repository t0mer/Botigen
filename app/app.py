# -*- coding: utf-8 -*-
from os import path
import helpers, time
from loguru import logger
from telebot import types, TeleBot
from telebot.callback_data import CallbackData, CallbackDataFilter
from telebot.custom_filters import AdvancedCustomFilter
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

FORM_PREVIEW_PATH = './preview.png'
EDU_SITE_USER = os.getenv('EDU_SITE_USER')
EDU_SITE_PASSWORD = os.getenv('EDU_SITE_PASSWORD')
BOT_TOKEN = os.getenv('BOT_TOKEN')
ALLOWED_IDS = os.getenv('ALLOWED_IDS')

KIDS = []
bot = TeleBot(BOT_TOKEN)
browser = None


commands = [{"text": "דיווח בודד", "callback_data": "get_kids_list"},
            {"text": "דיווח עבור כל הילדים", "callback_data": "finish_all"},
            {"text": "דיווח וסיום", "callback_data": "finish"},
            {"text": "ביטול ויציאה", "callback_data": "stop"}, ]

kids_list = CallbackData('kid_id', prefix='kids')


def kids_keyboard():
    return types.InlineKeyboardMarkup(
        keyboard=[
            [
                types.InlineKeyboardButton(
                    text=kid['Name'],
                    callback_data=kids_list.new(kid_id=kid["Index"])
                )
            ]
            for kid in KIDS
        ], row_width=1
    )


def command_keyboard():
    return types.InlineKeyboardMarkup(
        keyboard=[
            [
                types.InlineKeyboardButton(
                    text=command['text'],
                    callback_data=command["callback_data"]
                )
            ]
            for command in commands
        ], row_width=1
    )


def back_keyboard():
    return types.InlineKeyboardMarkup(
        keyboard=[
            [
                types.InlineKeyboardButton(
                    text='⬅',
                    callback_data='back'
                )
            ]
        ]
    )


class KidsCallbackFilter(AdvancedCustomFilter):
    key = 'config'

    def check(self, call: types.CallbackQuery, config: CallbackDataFilter):
        return config.check(query=call)


@bot.message_handler(commands=['start'])
def products_command_handler(message: types.Message):
    logger.info("Start signing process")
    global browser
    browser = helpers.GetBrowser()
    browser.get("https://parents.education.gov.il/prhnet/gov-education/corona/home-antigen-test")
    helpers.log_browser(browser)
    time.sleep(2)
    element = WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, 'button-blue')))
    element.click()
    time.sleep(1)
    logger.info("Perform Login")
    browser.get("https://lgn.edu.gov.il/nidp/wsfed/ep?id=EduCombinedAuthUidPwd&sid=0&option=credential&sid=0")
    browser.find_element(By.XPATH, '//*[@id="HIN_USERID"]').send_keys(str(EDU_SITE_USER))
    browser.find_element(By.XPATH, '//*[@id="Ecom_Password"]').send_keys(str(EDU_SITE_PASSWORD))
    browser.find_element(By.XPATH, '//*[@id="loginButton2"]').click()
    logger.info("Logged in")
    time.sleep(1)
    try:
        parent = browser.find_elements(By.CLASS_NAME, "profile-name").text
    except:
        parent = message.from_user.first_name + " " +  message.from_user.last_name
    get_all_kids()
    welcome = "שלום *{}*.\n\n".format(parent) + "ברוך הבא לבוט דיווח בדיקות אנטיגן של משרד החינוך\n\n" \
              + "כדי לבצע דיווח על ילד בודד או יותר לחץ על דיווח בודד\n\n" \
              + "כדי לבצע דיווח על כל הילדים לחץ על דיווח עבור כל הילדים\n\n" \
              + "במידה וכבר בחרת ילדים לדיווח לחץ על דיווח וסיום\n\n" \
              + "כדי לצאת לחץ על ביטול ויציאה\n\n"
    bot.send_message(chat_id=message.chat.id, text=welcome, reply_markup=command_keyboard(), parse_mode='Markdown')


@bot.callback_query_handler(func=None, config=kids_list.filter())
def products_callback(call: types.CallbackQuery):
    callback_data: dict = kids_list.parse(callback_data=call.data)
    if KIDS[int(callback_data['kid_id'])]["Sign"]:
        bot.answer_callback_query(callback_query_id=call.id,
                                  text=KIDS[int(callback_data['kid_id'])]["Name"] + " כבר נחתם/מה", show_alert=True)
    else:
        KIDS[int(callback_data['kid_id'])]["Sign"] = True
        kids = KIDS[int(callback_data['kid_id'])]
        text = f"שם הילד: {kids['Name']}\n" \
               "דווח בהצלחה"
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=text, reply_markup=back_keyboard())


@bot.callback_query_handler(func=lambda c: c.data == 'back')
def back_callback(call: types.CallbackQuery):
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text='בחר פעולה :', reply_markup=command_keyboard())


@bot.callback_query_handler(func=lambda c: c.data == 'get_kids_list')
def display_kids(call: types.CallbackQuery):
    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
    bot.send_message(chat_id=call.message.chat.id, text='בחר ילד/ה בכדי לדווח :',
                     reply_markup=kids_keyboard())


@bot.callback_query_handler(func=lambda c: c.data == "finish" or c.data == "finish_all")
def finish_and_sign(call: types.CallbackQuery):
    if call.data == "finish_all":
        mark_all_kids()
    mark_sign_kids()
    status = sign_and_finish()
    browser.find_element(By.CLASS_NAME, "agwrapper").screenshot(FORM_PREVIEW_PATH)
    if path.exists(FORM_PREVIEW_PATH):
        bot.send_photo(call.message.chat.id, photo=open(FORM_PREVIEW_PATH, 'rb'))
    bot.send_message(call.message.chat.id, status)
    browser.close()
    KIDS.clear()


@bot.callback_query_handler(func=lambda query: query.data == "stop")
@bot.message_handler(commands=['stop'])
def stop(message):
    bot.send_message(message.message.chat.id, "הפעולה הופסקה בהצלחה")
    browser.close()
    KIDS.clear()


def get_all_kids():
    try:
        names = browser.find_elements(By.XPATH, "//span[@class='inner name']")
        ids = browser.find_elements(By.XPATH, "//span[@class='label']")
        ids = ids[1::2]
        for i in range(len(names)):
            KIDS.append({"Name": names[i].text.split(" ")[0], "Id": ids[i].text, "Index": str(i), "Sign": False})
    except Exception as e:
        logger.error("oh snap something went wrong")
        logger.error(str(e))


def mark_all_kids():
    for i in range(len(KIDS)):
        KIDS[i]["Sign"] = True


def mark_sign_kids():
    logger.info("Mark as negative for covid")
    for kid in KIDS:
        if kid["Sign"]:
            negative = browser.find_elements(By.CSS_SELECTOR, "[id^=lblNeg"+kid["Id"]+"]")
            for radio in negative:
                radio.click()


def sign_and_finish():
    logger.info("Submiting form")
    browser.find_element(By.XPATH, '//button[text()="שליחה"]').click()
    time.sleep(1)
    alert = Alert(browser)
    alert.accept()
    return alert.text

if __name__ == '__main__':
    logger.info("I'm listening")
    bot.add_custom_filter(KidsCallbackFilter())
    bot.infinity_polling()
