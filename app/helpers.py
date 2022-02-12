# -*- coding: utf-8 -*-
from loguru import logger
# from webdriver_manager.chrome import ChromeDriverManager
import time, os
from os import path
from selenium import webdriver


def GetBrowser():
    options = webdriver.ChromeOptions()
    options.add_argument("--incognito")
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument('--start-maximized')
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument('--disable-notifications')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument("--mute-audio")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option("detach", True)
    #For linux
    browser = webdriver.Chrome(executable_path='/opt/chromedriver/chromedriver', options=options)
    #For windows
    # browser = webdriver.Chrome(executable_path=ChromeDriverManager().install(), options=options)
    return browser

#### Browser state logging ####
def log_browser(browser):
    logger.debug(f"Opened page. Url: {browser.current_url}, size: {len(browser.page_source)}")
