from selenium import webdriver
from selenium.webdriver.support.select import Select
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, UnexpectedAlertPresentException, NoSuchFrameException, NoAlertPresentException, ElementNotVisibleException, InvalidElementStateException
from urllib.parse import urlparse, urljoin
from selenium.webdriver.common.by import By
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

def extract_js_events(driver, element):
    """提取元素的JavaScript事件处理程序"""
    try:
        # 执行JavaScript代码来检查元素上的事件
        js_events = driver.execute_script("""
        var events = [];
        var elem = arguments[0];
        var eventListeners = getEventListeners(elem);
        for (var event in eventListeners) {
            events.push(event);
        }
        return events;
        """, element)
        return js_events
    except Exception as e:
        logging.warning("Failed to extract JS events: %s" % str(e))
        return []


def extract_dom_context_for_ui_form(element, driver):
    """提取UI_FORM的DOM上下文，包括节点、父节点、兄弟节点等"""
    dom_context = {
        "current_node": {
            "tag_name": element.tag_name,
            "attributes": element.get_attribute('outerHTML'),
            "text": element.text,
        },
        "parent_node": None,
        "sibling_nodes": [],
        "page_title": driver.title
    }

    # 提取父节点信息
    try:
        parent = element.find_element(By.XPATH, '..')
        dom_context["parent_node"] = {
            "tag_name": parent.tag_name,
            "attributes": parent.get_attribute('outerHTML'),
            "text": parent.text
        }
    except:
        dom_context["parent_node"] = None

    # 提取兄弟节点信息
    try:
        siblings = element.find_elements(By.XPATH, '../*')
        for sibling in siblings:
            if sibling != element:
                dom_context["sibling_nodes"].append({
                    "tag_name": sibling.tag_name,
                    "attributes": sibling.get_attribute('outerHTML'),
                    "text": sibling.text
                })
    except:
        dom_context["sibling_nodes"] = []

    return dom_context

def parse_ui_form(button, driver):
    """解析UI_FORM，提取DOM上下文和交互元素"""
    ui_form_context = extract_dom_context_for_ui_form(button, driver)  # 提取按钮的DOM上下文

    # 提取form元素及action属性
    form = button.find_elements(By.XPATH, ".//ancestor::form")
    action_url = form[0].get_attribute("action") if form else driver.current_url
    method = form[0].get_attribute("method").upper() if form else "GET"

    return {
        "action_url": action_url,
        "method": method,
        "dom_context": ui_form_context,
        "js_event": extract_js_events(driver, button)
    }

def extract_ui_forms(driver):
    sources = []
    submits =  []
    ui_forms = []

    ui_form_contexts = {}

    toggles = driver.find_elements(By.XPATH, "//input")
    for toggle in toggles:
        try:
            input_type = toggle.get_attribute("type")
            if (not input_type) or input_type == "text":
                in_form = toggle.find_elements(By.XPATH, ".//ancestor::form")
                if not in_form:
                    xpath = driver.execute_script("return getXPath(arguments[0])", toggle)
                    sources.append( {'xpath': xpath, 'value': 'FEWWORDSUI'} )
        except:
            logging.warning("UI form error")

    toggles = driver.find_elements(By.XPATH, "//textarea")
    for toggle in toggles:
        try:
            in_form = toggle.find_elements(By.XPATH, ".//ancestor::form")
            if not in_form:
                xpath = driver.execute_script("return getXPath(arguments[0])", toggle)
                sources.append( {'xpath': xpath, 'value': 'FEWWORDSUI'} )
        except:
            logging.warning("UI form error")


    if sources:
        buttons = driver.find_elements(By.XPATH, "//button")
        for button in buttons:
            try:
                in_form = button.find_elements(By.XPATH, ".//ancestor::form")
                if not in_form:
                    xpath = driver.execute_script("return getXPath(arguments[0])", button)
                    ui_form = Classes.Ui_form(sources, xpath)
                    ui_forms.append(ui_form)
                    ui_form_contexts[ui_form] = parse_ui_form(button, driver)
            except:
                logging.warning("UI form error")

    return ui_forms, ui_form_contexts


