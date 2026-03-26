from typing import Callable

from textual.app import App

from .app_selector import AppSelector
from .data_visualiser import DataVisualiserApp

if __name__ == "__main__":
    apps_mapping: dict[int, Callable[[], App]] = {
        1: lambda: DataVisualiserApp(),
    }

    while True:
        app = AppSelector()
        app_selector_result: int | None = app.run()

        if app_selector_result is None or app_selector_result < 0:
            break

        sub_app_factory = apps_mapping.get(app_selector_result)
        if sub_app_factory is not None:
            sub_app_factory().run()
        # After the sub-app exits, loop back to the selector