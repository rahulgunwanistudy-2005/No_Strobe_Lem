"""KPI Visualizer scenario: play the verified demo while its veil ramps run."""

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
        # KPI Visualizer can reuse an existing singleton process between iterations.
        vda = shutil.which("vda")
        if not vda:
            raise RuntimeError("Put the SDK vda executable on PATH")
        for command in (
            ["vlcm", "terminate-app", "--pkg-id", "com.nostrobe.tv"],
            ["vlcm", "launch-app", "pkg://com.nostrobe.tv.main"],
        ):
            subprocess.run([vda, "-s", self.device, "shell", *command], check=True)
        time.sleep(3)

    def run(self) -> None:
        self.driver.execute_script(
            "jsonrpc: injectInputKeyEvent",
            [{"inputKeyEvent": "96", "holdDuration": 80}],
        )
        time.sleep(9)
