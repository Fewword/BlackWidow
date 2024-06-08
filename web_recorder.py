import json
import os
import time

from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


class WebTester:
    def __init__(self):
        self.driver = self._setup_driver()
        self.action_data = []

    def _setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--ignore-certificate-errors")
        driver_service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=driver_service, options=chrome_options)
        return driver

    def _capture_screenshot(self, action_name):
        timestamp = int(time.time())
        screenshot_path = f"screenshots/{action_name}_{timestamp}.png"
        self.driver.save_screenshot(screenshot_path)
        return screenshot_path

    def _log_action(self, action_name, before_screenshot_path, after_screenshot_path, initial_request_count):
        time.sleep(2)  # 确保请求已经发送并记录
        requests_data = []
        new_requests = self.driver.requests[initial_request_count:]
        for request in new_requests:
            if request.response:
                request_data = {
                    "url": request.url,
                    "method": request.method,
                    "request_headers": dict(request.headers),
                    "response_status": request.response.status_code,
                    "response_headers": dict(request.response.headers),
                }

                # Add response body only for non-static files
                if not request.url.endswith((".js", ".css", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico")):
                    try:
                        request_data["response_body"] = request.response.body.decode('utf-8', errors='ignore')
                    except Exception as e:
                        request_data["response_body_error"] = str(e)
                requests_data.append(request_data)

        self.action_data.append({
            "action": action_name,
            "before_screenshot": before_screenshot_path,
            "after_screenshot": after_screenshot_path,
            "requests": requests_data
        })

    def perform_action(self, action_name, action_func):
        print("before:"+str(len(self.driver.requests)))
        self.driver.requests.clear()
        print("after clear:" +str(len(self.driver.requests)))
        initial_request_count = len(self.driver.requests)
        before_screenshot_path = self._capture_screenshot("before_"+action_name)
        action_func()
        time.sleep(1)
        after_screenshot_path = self._capture_screenshot("after_"+action_name)
        print("after action:" + str(len(self.driver.requests)))
        self._log_action(action_name, before_screenshot_path, after_screenshot_path, initial_request_count)

    def save_log(self):
        with open("action_log.json", "w", encoding="utf-8") as file:
            json.dump(self.action_data, file, ensure_ascii=False, indent=4)

    def close(self):
        self.driver.quit()


# 示例操作函数
def example_actions(tester):
    # 打开页面
    tester.driver.get("http://192.168.213.128:8888/login")

    elem = tester.driver.find_elements(By.TAG_NAME, "form")
    for el in elem:
        inputs = el.find_elements(By.TAG_NAME, "input")
        for input in inputs:
            if input.get_attribute("type") == "text":
                tester.perform_action("input email", lambda: input.send_keys("user1@test.com"))
            elif input.get_attribute("type") == "password":
                tester.perform_action("input password", lambda: input.send_keys("user1Test@"))
        buttons = el.find_elements(By.TAG_NAME, "button")
        for button in buttons:
            if button.get_attribute("type") == "submit":
                tester.perform_action("submit", lambda : button.click())
                time.sleep(2)
                break


if __name__ == "__main__":
    os.makedirs("screenshots", exist_ok=True)
    tester = WebTester()
    try:
        example_actions(tester)
    finally:
        tester.save_log()
        tester.close()
