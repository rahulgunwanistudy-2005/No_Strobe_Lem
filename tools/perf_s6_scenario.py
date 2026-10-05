"""KPI Visualizer scenario: play the verified demo while its veil ramps run."""

import os
import shutil
import subprocess
import time

from appium import webdriver
from appium.options.common import AppiumOptions


class TestRunner:
    def __init__(self, device_serial_number: str, port: int):
        self.device = device_serial_number
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
        time.sleep(1)

    def run(self) -> None:
        # The perf runner launches after prep; let the catalog become focusable.
        time.sleep(3)
        if os.environ.get("NOSTROBE_PERF_SCENE") == "focus":
            subprocess.run(
                [
                    shutil.which("vda"),
                    "-s",
                    self.device,
                    "shell",
                    "inputd-cli",
                    "button_press",
                    "KEY_MENU",
                ],
                check=True,
            )
            time.sleep(1)
            for key in (108, 105, 106, 108, 105, 106, 103, 105, 106, 103, 108, 103):
                self.driver.execute_script(
                    "jsonrpc: injectInputKeyEvent",
                    [{"inputKeyEvent": str(key), "holdDuration": 80}],
                )
                time.sleep(0.5)
            return
        self.driver.execute_script(
            "jsonrpc: injectInputKeyEvent",
            [{"inputKeyEvent": "96", "holdDuration": 80}],
        )
        time.sleep(9)
