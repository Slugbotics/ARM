from kivy.uix.tabbedpanel import TabbedPanel
from kivy.app import App
class AppBase(App):
    def start_app(self) -> bool: ...

    # return False

    def stop_app(self) -> bool: ...
    # return False