from textual.app import App, ComposeResult
from textual.containers import VerticalGroup
from textual.widgets import Button, Footer, Header, Label, RadioButton, RadioSet, Rule


class AppSelector(App[int]):
    """
    The entry point for the campus_nav application.
    This app allows users to select whether to launch the navigation app or the data visualiser app.
    On exit, it will return an integer indicating what is the next step.
    """

    BINDINGS = [
        ("ctrl+q", "quit", "Exit"),
    ]
    CSS_PATH = "app_selector.tcss"

    def compose(self) -> ComposeResult:
        yield Header()
        yield AppSelector.AppSelectorContents(id="main_div")
        yield Footer()

    def on_mount(self) -> None:
        self.theme = "textual-dark"
        self.title = "Campus Navigator"
        self.sub_title = "Welcome"

    def action_quit(self) -> None:
        self.exit(-1)

    class AppSelectorContents(VerticalGroup):

        _exit_code: int = 0

        def compose(self) -> ComposeResult:
            yield Label("[b]Welcome to Campus Navigator![/b]\nSelect an option to continue:", id="lbl_welcome")
            yield Rule(line_style="heavy")
            with RadioSet(id="options_set"):
                yield RadioButton("Launch Navigator App", id="rtn_nav_app")
                yield RadioButton("Launch Data Visualiser App", id="rtn_data_manager_app")
                yield RadioButton("Exit", id="rtn_exit")
            yield Label("ACTION_DESC_PLACEHOLDER", id="lbl_action_desc")
            yield Rule(line_style="heavy")
            yield Button("Continue", id="btn_continue", variant="primary")

        def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
            radio_btns_mapping : dict[str, tuple[int, str]] = {
                "rtn_nav_app":          (0, "Launch the navigation app to find your way around campus!"),
                "rtn_data_manager_app": (1, "Launch the data visualiser app to explore the campus map graphically."),
                "rtn_exit":             (-1, "Exit the application."),
            }
            self._exit_code = radio_btns_mapping[event.pressed.id][0]
            self.query_one("#lbl_action_desc", Label).update(f"Description: {radio_btns_mapping[event.pressed.id][1]}")

        def on_mount(self) -> None:
            self.query_one("#rtn_nav_app", RadioButton).value = True

        def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "btn_continue":
                self.app.exit(self._exit_code)