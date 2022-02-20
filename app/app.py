# -*- coding: utf-8 -*-
from os import path
from loguru import logger
import helpers, helpers, json, time, os
from telebot import types, TeleBot
from telebot.custom_filters import AdvancedCustomFilter
from telebot.callback_data import CallbackData, CallbackDataFilter
from selenium.webdriver.common.by import By
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import codecs
import json

FORM_PREVIEW_PATH = './preview.png'
EDU_SITE_USER = os.getenv('EDU_SITE_USER')
EDU_SITE_PASSWORD = os.getenv('EDU_SITE_PASSWORD')
BOT_TOKEN = os.getenv('BOT_TOKEN')
ALLOWED_IDS = os.getenv('ALLOWED_IDS')

KIDS = []
bot = TeleBot(BOT_TOKEN)
browser = None
KIDS_FILE = "./kids.json"
os.environ.setdefault('PARENT_NAME', "")

# -------------- Set command list -------------------------------------
commands = [{"text": "דיווח בודד", "callback_data": "get_kids_list"},
            {"text": "דיווח עבור כל הילדים", "callback_data": "finish_all"},
            {"text": "דיווח וסיום", "callback_data": "finish"},
            {"text": "ביטול ויציאה", "callback_data": "stop"}, ]

kids_list = CallbackData('kid_id', prefix='kids')


# -------------- Building kids selection inline keyboard
def kids_keyboard():
    logger.debug("Build Kids Keyboard")
    markup = types.InlineKeyboardMarkup(row_width=1)
    result = []
    logger.debug("kids:" + str(KIDS))
    for kid in KIDS:
        logger.debug("kid:" + str(kid))
        markup.add(types.InlineKeyboardButton(
            text=kid['Name'],
            callback_data=kids_list.new(kid_id=kid["Index"])))
        result.append(kid["Sign"])
    logger.debug("result:" + str(result))
    if True in result:
        markup.add(types.InlineKeyboardButton(text="דיווח וסיום", callback_data="finish"))
    markup.add(types.InlineKeyboardButton(text="חזרה", callback_data="back"))
    return markup


# -------------- Get Parent name -------------------
def GetParentName():
    global browser
    try:
        if os.getenv("PARENT_NAME") == "":
            os.environ['PARENT_NAME'] = browser.find_element(By.CLASS_NAME, "profile-name").text
    except Exception as e:
        logger.error("oh snap something went wrong")
        logger.error(str(e))


# ------------- Build command keyboard -----------------
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


# ------------- Adding back button to the keyboard -------------
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


# ------------- Creating custom filter
class KidsCallbackFilter(AdvancedCustomFilter):
    key = 'config'

    def check(self, call: types.CallbackQuery, config: CallbackDataFilter):
        return config.check(query=call)


# -------------- Write kids array to file for better response time
def WriteKidsToFile():
    with codecs.open(
            KIDS_FILE, "w", encoding="utf-8") as outfile:
        json.dump(
            KIDS,
            outfile,
            skipkeys=False,
            ensure_ascii=False,
            indent=4,
            separators=None,
            default=None,
            sort_keys=True,
        )
    # with open(KIDS_FILE, 'w') as kidsfile:
    #     kidsfile.write(json.dumps(KIDS))


# -------------- Reading kids list from file ------------------
def ReadKidsFromFile():
    global KIDS
    logger.debug("Read Kids File")
    with open(KIDS_FILE, encoding="utf-8"
              ) as data_file:
        KIDS = json.loads(data_file.read())
    logger.debug("Kids List:" + str(KIDS))


# -------------- Login method ---------------------------------
def Login():
    global browser
    browser = helpers.GetBrowser()
    browser.get("https://parents.education.gov.il/prhnet/gov-education/corona/home-antigen-test")
    element = WebDriverWait(browser, 10).until(EC.visibility_of_element_located((By.CLASS_NAME, 'button-blue')))
    element.click()
    time.sleep(1)
    logger.info("Perform Login")
    browser.get("https://lgn.edu.gov.il/nidp/wsfed/ep?id=EduCombinedAuthUidPwd&sid=0&option=credential&sid=0")
    browser.find_element(By.ID, "HIN_USERID").send_keys(str(EDU_SITE_USER))
    browser.find_element(By.ID, "Ecom_Password").send_keys(str(EDU_SITE_PASSWORD))
    browser.find_element(By.ID, "loginButton2").click()
    logger.info("Logged in")
    return browser


# ----------------- Handle the /start command ---------------------------
@bot.message_handler(commands=['start', 'sign'])
def kids_command_handler(message: types.Message):
    # bot.send_message(message.chat.id, "אנא המתן כמה שניות עד לקבלת התפריט")
    GetKidsList()
    try:
        parent = os.getenv("PARENT_NAME")
        if parent == "":
            parent = message.from_user.first_name
    except Exception as e:
        parent = message.from_user.first_name
        logger.error(str(e))
    logger.info("Opening menu")
    welcome = "שלום *{}*.\n\n".format(parent) + "ברוך הבא לבוט דיווח בדיקות אנטיגן אל משרד החינוך\n\n" \
              + "כדי לבצע דיווח על ילד בודד או יותר לחץ על דיווח בודד\n\n" \
              + "כדי לבצע דיווח על כל הילדים לחץ על דיווח עבור כל הילדים\n\n" \
              + "במידה וכבר בחרת ילדים לדיווח לחץ על דיווח וסיום\n\n" \
              + "כדי לצאת לחץ על ביטול ויציאה\n\n"
    bot.send_message(chat_id=message.chat.id, text=welcome, reply_markup=command_keyboard(), parse_mode='Markdown')


# ---------------- Handle kid selection -------------------------
@bot.callback_query_handler(func=None, config=kids_list.filter())
def kids_callback(call: types.CallbackQuery):
    logger.info("Change Kids status")
    callback_data: dict = kids_list.parse(callback_data=call.data)
    if KIDS[int(callback_data['kid_id'])]["Sign"]:
        bot.answer_callback_query(callback_query_id=call.id,
                                  text=KIDS[int(callback_data['kid_id'])]["Name"] + " כבר נחתם/מה", show_alert=True)
    else:
        KIDS[int(callback_data['kid_id'])]["Sign"] = True
        KIDS[int(callback_data['kid_id'])]["Name"] = KIDS[int(callback_data['kid_id'])]["Name"] + " ✅ "
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id
                                      , reply_markup=kids_keyboard())


# ---------------- Handle the back button --------------------
@bot.callback_query_handler(func=lambda c: c.data == 'back')
def back_callback(call: types.CallbackQuery):
    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id
                                  , reply_markup=command_keyboard())


# --------------- Handle the List kids button --------------------------
@bot.callback_query_handler(func=lambda c: c.data == 'get_kids_list')
def display_kids(call: types.CallbackQuery):
    logger.info("Getting kids list")
    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None, )
    bot.send_message(chat_id=call.message.chat.id, text='בחר ילד/ה בכדי לדווח :',
                     reply_markup=kids_keyboard())


# -------------- Handle the finish / finish all buttons ---------------------------
@bot.callback_query_handler(func=lambda c: c.data == "finish" or c.data == "finish_all")
def finish_and_sign(call: types.CallbackQuery):
    Login()
    time.sleep(2)
    logger.info("Starting to sign")
    if call.data == "finish_all":
        mark_all_kids()
    mark_sign_kids()
    sign_and_finish()
    browser.find_element(By.CLASS_NAME, "agwrapper").screenshot(FORM_PREVIEW_PATH)
    if path.exists(FORM_PREVIEW_PATH):
        bot.send_photo(call.message.chat.id, photo=open(FORM_PREVIEW_PATH, 'rb'))
    bot.send_message(call.message.chat.id, "הדיווח הושלם בהצלחה")
    logger.info("Finish Sign and close all connection")
    browser.quit()
    KIDS.clear()


# ---------------- Handle stop button ----------------------------
@bot.callback_query_handler(func=lambda query: query.data == "stop")
@bot.message_handler(commands=['stop'])
def stop(message):
    bot.send_message(message.message.chat.id, "הפעולה הופסקה בהצלחה")
    logger.info("Stop and clear all connection")
    browser.quit()
    KIDS.clear()


# ------------------- Get kids list ------------------------------
def GetKidsList():
    try:
        if path.exists(KIDS_FILE):
            logger.debug("Reading kids from file")
            ReadKidsFromFile()
        else:
            logger.info("Getting kids from EDU Site")
            names = browser.find_elements(By.XPATH, "//span[@class='inner name']")
            ids = browser.find_elements(By.XPATH, "//span[@class='label']")
            ids = ids[1::2]
            for i in range(len(names)):
                KIDS.append({"Name": names[i].text.split(" ")[0], "Id": ids[i].text, "Index": str(i), "Sign": False})
            if len(KIDS) > 0:
                logger.info('Writing kids array to file')
                WriteKidsToFile()
    except Exception as e:
        logger.error("oh snap something went wrong")
        logger.error(str(e))


def mark_all_kids():
    for i in range(len(KIDS)):
        KIDS[i]["Sign"] = True
    logger.info("Mark all as negative for covid")


def mark_sign_kids():
    logger.info("Mark kid as negative for covid")
    for kid in KIDS:
        if kid["Sign"]:
            negative = browser.find_elements(By.CSS_SELECTOR, "[id^=lblNeg" + kid["Id"] + "]")
            for radio in negative:
                radio.click()


def sign_and_finish():
    logger.info("Submiting form")
    browser.find_element(By.XPATH, '//button[text()="שליחה"]').click()
    time.sleep(1)
    alert = Alert(browser)
    alert.accept()


def init():
    Login()
    GetParentName()
    GetKidsList()
    browser.quit()


if __name__ == '__main__':
    logger.debug("Starting")
    init()
    logger.debug("I'm running and wating for commands")
    bot.add_custom_filter(KidsCallbackFilter())
    bot.infinity_polling()
