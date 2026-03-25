from typing import Callable

from textual.app import App

from .app_selector import AppSelector

if __name__ == "__main__":
    apps_mapping: dict[int, Callable[[], App]] = {

    }
    app = AppSelector()
    app_selector_result: int | None = app.run()

    print(f"App selector result: {app_selector_result}")

    sub_app = apps_mapping.get(app_selector_result)
    if sub_app is not None:
        sub_app().run()

    exit(0)