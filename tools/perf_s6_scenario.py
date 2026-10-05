"""KPI Visualizer scenario: play the verified demo while its veil ramps run."""

import time

from appium import webdriver
from appium.options.common import AppiumOptions


class TestRunner:
    def __init__(self, device_serial_number: str, port: int):
        self.driver = webdriver.Remote(
            f"http://127.0.0.1:{port}",
            options=AppiumOptions().load_capabilities(
                {
                    "platformName": "Kepler",
                    "appium:automationName": "automation-toolkit/JSON-RPC",
                    "kepler:device": f"vda://{device_serial_number}",
                    "kepler:jsonRPCPort": 8383,
                    "appium:deviceName": device_serial_number,
                    "appium:newCommandTimeout": 500,
                }
            ),
        )

    def prep(self) -> None:
        time.sleep(2)

    def run(self) -> None:
        self.driver.execute_script(
            "jsonrpc: injectInputKeyEvent",
            [{"inputKeyEvent": "96", "holdDuration": 80}],
        )
        time.sleep(9)
