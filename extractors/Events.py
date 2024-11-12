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


def extract_data_toggle(driver):
    toggles = driver.find_elements(By.XPATH, "//button[@data-toggle]")
    dos = []
    for toggle in toggles:
        # 获取DOM上下文，包括父节点、兄弟节点
        parent = driver.execute_script("return arguments[0].parentNode;", toggle)
        siblings = driver.execute_script("""
            var siblings = [];
            var sibling = arguments[0].parentNode.firstChild;
            while (sibling) {
                if (sibling.nodeType === 1 && sibling !== arguments[0]) {
                    siblings.push(sibling);
                }
                sibling = sibling.nextSibling;
            }
            return siblings;
        """, toggle)

        xpath = driver.execute_script("return getXPath(arguments[0])", toggle)
        url = driver.current_url  # 获取操作URL

        do = {
            'function_id': '',
            'event': 'click',
            'id': toggle.get_attribute('id'),
            'tag': 'button',
            'addr': xpath,
            'class': toggle.get_attribute('class'),
            'dom_context': {
                'current_node': driver.execute_script("return arguments[0].outerHTML;", toggle),
                'parent_node': driver.execute_script("return arguments[0].outerHTML;", parent),
                'sibling_nodes': [driver.execute_script("return arguments[0].outerHTML;", s) for s in siblings],
                'page_title': driver.title
            },
            'url': url
        }
        dos.append(do)

    return dos


def extract_inputs(driver):
    inputs = driver.find_elements(By.XPATH, "//input | //textarea")
    dos = []
    for input_elem in inputs:
        input_type = input_elem.get_attribute("type")
        if (not input_type) or input_type == "text":
            # 获取表单和DOM上下文
            in_form = input_elem.find_elements(By.XPATH, ".//ancestor::form")
            if in_form:
                continue
            parent = driver.execute_script("return arguments[0].parentNode;", input_elem)
            siblings = driver.execute_script("""
                var siblings = [];
                var sibling = arguments[0].parentNode.firstChild;
                while (sibling) {
                    if (sibling.nodeType === 1 && sibling !== arguments[0]) {
                        siblings.push(sibling);
                    }
                    sibling = sibling.nextSibling;
                }
                return siblings;
            """, input_elem)

            xpath = driver.execute_script("return getXPath(arguments[0])", input_elem)
            url = driver.current_url  # 获取操作URL

            do = {
                'function_id': '',
                'event': 'input',
                'id': input_elem.get_attribute('id'),
                'tag': 'input',
                'addr': xpath,
                'class': input_elem.get_attribute('class'),
                'dom_context': {
                    'current_node': driver.execute_script("return arguments[0].outerHTML;", input_elem),
                    'parent_node': driver.execute_script("return arguments[0].outerHTML;", parent),
                    'sibling_nodes': [driver.execute_script("return arguments[0].outerHTML;", s) for s in siblings],
                    'page_title': driver.title
                },
                'url': url
            }
            dos.append(do)

    return dos


def extract_fake_buttons(driver):
    fake_buttons = driver.find_elements(By.CLASS_NAME, "btn")
    dos = []
    for button in fake_buttons:
        # 获取DOM上下文
        parent = driver.execute_script("return arguments[0].parentNode;", button)
        siblings = driver.execute_script("""
            var siblings = [];
            var sibling = arguments[0].parentNode.firstChild;
            while (sibling) {
                if (sibling.nodeType === 1 && sibling !== arguments[0]) {
                    siblings.push(sibling);
                }
                sibling = sibling.nextSibling;
            }
            return siblings;
        """, button)

        xpath = driver.execute_script("return getXPath(arguments[0])", button)
        url = driver.current_url  # 获取操作URL

        do = {
            'function_id': '',
            'event': 'click',
            'id': button.get_attribute('id'),
            'tag': 'a',
            'addr': xpath,
            'class': button.get_attribute('class'),
            'dom_context': {
                'current_node': driver.execute_script("return arguments[0].outerHTML;", button),
                'parent_node': driver.execute_script("return arguments[0].outerHTML;", parent),
                'sibling_nodes': [driver.execute_script("return arguments[0].outerHTML;", s) for s in siblings],
                'page_title': driver.title
            },
            'url': url
        }
        dos.append(do)

    return dos

def extract_events(driver):
    try:
    # Use JavaScript to find events
        resps = driver.execute_script("return catch_properties()")
        todo = json.loads(resps)
    except Exception as e:
        logging.warning("Failed to extract events: %s" % str(e))
        todo = []

    # From event listeners
    resps = driver.execute_script("return JSON.stringify(added_events)")
    todo += json.loads(resps)

    # From data-toggle
    resps = extract_data_toggle(driver)
    todo += resps


    # Only works in Chrome DevTools
    # resps = driver.execute_script("catch_event_listeners()");
    # todo += resps

    # From fake buttons class="btn"
    resps = extract_fake_buttons(driver)
    todo += resps

    resps = extract_inputs(driver)
    todo += resps

    #for do in todo:
    #    print(do)

    events = set()
    event_contexts = {}
    for do in todo:
        event = Classes.Event(do['function_id'], 
                      do['event'],
                      do['id'],
                      do['tag'],
                      do['addr'],
                      do['class'])
        events.add(event)
        event_contexts[event] = {
            'dom_context': do.get('dom_context', ''),
            'event': str(event),
            'url': do.get('url', '')
        }

    return events, event_contexts


