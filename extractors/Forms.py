from selenium import webdriver
from selenium.webdriver.support.select import Select
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, \
    UnexpectedAlertPresentException, NoSuchFrameException, NoAlertPresentException, ElementNotVisibleException, \
    InvalidElementStateException
from urllib.parse import urlparse, urljoin
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import json
import pprint
import datetime
import tldextract
import math
import os
import traceback
import random
import re
import logging
import copy
import time

import Classes

from chaojiying import *


def parse_form(el, driver):
    form = Classes.Form()

    form.html = el.get_attribute("outerHTML")

    try:
        if el.get_attribute("action"):
            form.action = el.get_attribute("action")
            if el.get_attribute("method"):
                form.method = el.get_attribute("method")
            else:
                form.method = "get"

    except StaleElementReferenceException as e:
        logging.error("Stale pasta in from action")
        logging.error(traceback.format_exc())
    except:
        logging.error("Failed to write element")
        logging.error(traceback.format_exc())

    # <input> tags
    try:
        inputs = el.find_elements(By.TAG_NAME, "input")
    except StaleElementReferenceException as e:
        print("Stale pasta in inputs")
        logging.error("Stale pasta in inputs")
        inputs = None
    except:
        logging.error("Unknown exception in inputs")
        inputs = None

    if not inputs:
        # TODO Exapnd JavaScript for all types of elements
        inputs = []
        logging.warning("No inputs founds during parse, falling back to JavaScript")
        resps = driver.execute_script("return get_forms()")
        # print("No inputs, looking at js")
        # print("Looking for inputs to the form with action ", form.action)
        js_forms = json.loads(resps)
        # print(js_forms)
        for js_form in js_forms:
            current_form = Classes.Form()
            current_form.method = js_form['method']
            current_form.action = js_form['action']
            logging.info("Found js form: " + str(current_form))

            if (current_form.method == form.method and current_form.action == form.action):
                for js_el in js_form['elements']:
                    web_el = driver.find_element(By.XPATH, js_el['xpath'])
                    # print("Adding js form input", js_el, web_el)
                    inputs.append(web_el)
                break

    for iel in inputs:
        # accessible_name
        tmp = {'type': None, 'accessible_name': None, 'name': None, 'value': None, 'checked': None}
        try:
            if iel.get_attribute("type"):
                tmp['type'] = iel.get_attribute("type")
            if iel.accessible_name:
                tmp['accessible_name'] = iel.accessible_name
            if iel.get_attribute("name"):
                tmp['name'] = iel.get_attribute("name")
            if iel.get_attribute("value"):
                tmp['value'] = iel.get_attribute("value")
            if iel.get_attribute("checked"):
                tmp['checked'] = True
            if iel.aria_role and iel.aria_role == "combobox":
                # tmp['type'] = "combobox"
                # 等待下拉列表加载
                iel.click()
                time.sleep(1)
                driver.switch_to.active_element.send_keys(Keys.ENTER)

                text = driver.find_element(By.CLASS_NAME, "ant-select-selection-item").text
                tmp['value'] = text

        except StaleElementReferenceException as e:
            print("Stale pasta in from action")
        except:
            print("Failed to write element")
            print(traceback.format_exc())
        form.add_input(tmp['type'], tmp['accessible_name'], tmp['name'], tmp['value'], tmp['checked'])

    # <select> and <option> tags
    selects = el.find_elements(By.TAG_NAME, "select")
    for select in selects:
        tmp = {'accessible_name': None, 'name': None}
        if select.accessible_name:
            tmp['accessible_name'] = select.accessible_name
        if select.get_attribute("name"):
            tmp['name'] = select.get_attribute("name")
        form_select = form.add_select("select", tmp['accessible_name'], tmp['name'])

        selenium_select = Select(select)
        options = selenium_select.options
        for option in options:
            form_select.add_option(option.get_attribute("value"))
            # if option == selenium_select.first_selected_option:
            #    form_select.selected = option.get_attribute("value")

    # <textarea> tags
    textareas = el.find_elements(By.TAG_NAME, "textarea")
    for ta in textareas:
        tmp = {'accessible_name': None, 'name': None, 'value': None}
        try:
            if ta.accessible_name:
                tmp['accessible_name'] = ta.accessible_name
            if ta.get_attribute("name"):
                tmp['name'] = ta.get_attribute("name")
            if ta.get_attribute("value"):
                tmp['value'] = ta.get_attribute("value")

        except StaleElementReferenceException as e:
            print("Stale pasta in from action")
        except:
            print("Failed to write element")
            print(traceback.format_exc())
        form.add_textarea(tmp['accessible_name'], tmp['name'], tmp['value'])

    # <button> tags
    buttons = el.find_elements(By.TAG_NAME, "button")
    for button in buttons:
        form.add_button(button.get_attribute("type"),
                        button.accessible_name,
                        button.get_attribute("name"),
                        button.get_attribute("value")
                        )

    a_tags = el.find_elements(By.TAG_NAME, "a")
    for a_tag in a_tags:
        form.add_a_tag(a_tag.get_attribute("id"),
                       a_tag.accessible_name,
                       )

    # <iframe> with <body contenteditable>
    iframes = el.find_elements(By.TAG_NAME, "iframe")
    for iframe in iframes:
        iframe_id = iframe.get_attribute("id")
        driver.switch_to.frame(iframe)
        iframe_body = driver.find_element(By.TAG_NAME, "body")

        if (iframe_body.get_attribute("contenteditable") == "true"):
            form.add_iframe_body(iframe_id)

        driver.switch_to.default_content();

    # 识别验证码
    captcha_ele = el.find_elements(By.TAG_NAME, "img")
    if captcha_ele:
        for ele in captcha_ele:
             if "captcha" in ele.get_attribute("src") or "code" in ele.get_attribute("src"):
                img_base64 = ele.screenshot_as_base64
                import base64
                img_data = base64.b64decode(img_base64)
                form.set_capcha_captcha_img(captcha_img=img_data);
                break

    return form


# Search for <form>
def extract_forms(driver):
    elem = driver.find_elements(By.TAG_NAME, "form")

    forms = set()
    for el in elem:
        forms.add(parse_form(el, driver))
    return forms
