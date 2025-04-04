from typing import Dict
from typing import Any

from HALs.HAL_base import HAL_base
from Vision.VisualObjectIdentifier import VisualObjectIdentifier
from Controllers.Controller import Controller
from Modules.server.ServerBase import ServerBase
from Modules.App.AppBase import AppBase
from Modules.speech_to_text.STTBase import STTBase
from Modules.Language.LanguageInterpreterBase import LanguageInterpreterBase

from Modules.Base.TextOut import TextOut
from Modules.Console import Console
from Modules.Commands.Commands import Commands
from Modules.HotkeyManager import HotkeyManager
from Modules.ConsoleInput import ConsoleInput

from Modules.Commands.DefaultCommands import register_default_commands, register_controler_commands
from Modules.Language.LanguageTools import register_default_tools, register_controler_tools

class ArmRuntime:
    def __init__(self):
        self.selected_HAL: HAL_base = None
        self.selected_object_identifier: VisualObjectIdentifier = None
        self.selected_controller: Controller = None
        self.selected_server: ServerBase = None  
        self.selected_app: AppBase = None      
        self.selected_stt: STTBase = None
        self.selected_tts = None
        self.selected_voice: TextOut = Console()
        self.selected_language_interpreter: LanguageInterpreterBase = None
        
        self.selected_logger = None
        self.commands: Commands = Commands()
        self.hotkey_manager: HotkeyManager = HotkeyManager()
        self.console_input: ConsoleInput = ConsoleInput()
        
    def apply_config(self, config: Dict[str, Any]) -> None:
        if config["write_logs"]:
            from Modules.Logging.PrintLogger import PrintLogger
            self.selected_logger = PrintLogger()
            self.selected_logger.start()

        if config["use_tts"]:
            from Modules.text_to_speech.TTSBase import TTSBase
            from Modules.text_to_speech.pyttsx_tts import pyttsx_tts
            self.selected_tts: TTSBase = pyttsx_tts()
            self.selected_voice = self.selected_tts
            
        # console input stuff
        
        def console_input_handeler(input_str: str) -> None:
            self.commands.user_input(input_str, Commands.Trust.TRUSTED, self.console_input)
            
        self.console_input = ConsoleInput(console_input_handeler, ">> ")
        register_default_commands(self.commands)
        register_controler_commands(self.commands, lambda: self.selected_controller)
        
        # Language stuff
        if config["use_language_model"]:
            from Modules.Language.LanguageInterpreter import LanguageInterpreter
            print("language_model_file: \"" + str(config["language_model_file"]) + "\"")
            self.selected_language_interpreter = LanguageInterpreter(config["language_model_file"])
            register_default_tools(self.selected_language_interpreter)
            register_controler_tools(self.selected_language_interpreter, lambda: self.selected_controller)
            self.commands.add_command("llm", lambda args: self.selected_voice.write_line(self.selected_language_interpreter.run(args)),
                                "Runs the provided input on the language model")
        # HAL stuff
        if config["use_simulator"]:
            from HALs.sim_HAL import sim_HAL
            self.selected_HAL = sim_HAL(config["sim_host"])
        elif config["use_physical"]:
            from HALs.physical_HAL import physical_HAL
            self.selected_HAL = physical_HAL()
            
        # vision stuff
        from Vision.ColorObjectIdentifier import ColorObjectIdentifier
        self.selected_object_identifier: VisualObjectIdentifier = ColorObjectIdentifier()
        
        # controler stuff
        from Controllers.FollowLargestObjectControler import FollowLargestObjectControler
        self.selected_controller: Controller = FollowLargestObjectControler(self.selected_HAL, self.selected_object_identifier, "none")

        # App stuff
        if config["use_app"]:
            # Kivy opens the window if this is imported, thus why it is here.
            from Modules.App.App import App
            from Controllers.FollowClaw import FollowClawController
            self.selected_object_identifier: ColorObjectIdentifier = ColorObjectIdentifier()
            self.selected_controller = FollowClawController(self.selected_HAL, self.selected_object_identifier)    
            self.selected_app = App(self.selected_controller, self.selected_HAL, self.selected_object_identifier)
            
        # Server setup
        if config["use_server"]:
            from Modules.server.http_server import HTTPServer
            self.selected_server: ServerBase = HTTPServer(self)
            
        # speech to text setup
        if config["use_stt"]:
            from Modules.speech_to_text.VoskSTT import VoskSTT
            
            def speech_input_handeler(input_str: str) -> None:
                self.commands.user_input(input_str, Commands.Trust.TRUSTED, self.selected_stt)
            
            self.selected_stt: STTBase = VoskSTT(on_sentence_heard_fnc = speech_input_handeler)
            if config["stt_model_large"]:
                self.selected_stt.set_selected_default_model(VoskSTT.DEFAULT_MODEL_LARGE)
                
            self.selected_stt.start()    
            if config["stt_push_to_talk"]:
                print("Speech Recognition is in push to talk mode - press left-shift to activate")
                def stt_activate():
                    if not self.selected_stt.is_active():                
                        self.selected_stt.activate()
                        print("Speech Recognition is now active")
                def stt_deactivate():
                    if self.selected_stt.is_active():                
                        self.selected_stt.deactivate()
                        print("Speech Recognition is now inactive")
                from pynput import keyboard
                self.hotkey_manager.add_key_press_callback(keyboard.Key.shift, stt_activate) 
                self.hotkey_manager.add_key_release_callback(keyboard.Key.shift, stt_deactivate) 
                
        # Twitch setup
        if config["use_twitch"]:
            from Modules.twitch.TwitchChat import TwitchChat
            if config["twitch_id"] == "NONE":
                print("Please set twitch_id to a valid twitch_id to use the twitch chat reader")
            elif config["twitch_secret"] == "NONE":
                print("Please set twitch_secret to a valid twitch secret to use the twitch chat reader")
            else:
                self.selected_twitch = TwitchChat(config["twitch_id"], config["twitch_secret"])

    def start(self, config: Dict[str, Any]) -> None:
        # Connect to twitch
        if config["use_twitch"]:
            def twitch_input_handeler(input_str: str) -> None:
                self.commands.user_input(input_str, Commands.Trust.SUS, self.selected_twitch)
            
            self.selected_twitch.connect_to_twitch(config["twitch_channel_name"], twitch_input_handeler)
            
        self.hotkey_manager.start()
        
    def stop(self, config: Dict[str, Any]) -> None:
        self.hotkey_manager.stop()
        if config["use_twitch"]:
            self.selected_twitch.stop_twitch_chat()
            
        self.console_input.cleanup()
    
        if self.selected_logger is not None:
            self.selected_logger.stop()

    def modules_to_string(self):
        return (
            f"RuntimeConfig(\n"
            f"  selected_HAL              : {self.selected_HAL.__class__.__name__},\n"
            f"  selected_controller       : {self.selected_controller.__class__.__name__},\n"
            f"  selected_object_identifier: {self.selected_object_identifier.__class__.__name__},\n"            
            f"  selected_server           : {self.selected_server.__class__.__name__},\n"
            f"  selected_app              : {self.selected_app.__class__.__name__},\n"
            f"  selected_stt              : {self.selected_stt.__class__.__name__},\n"
            f"  selected_tts              : {self.selected_tts.__class__.__name__},\n"
            f"  selected_voice            : {self.selected_voice.__class__.__name__},\n"
            f"  language_interpreter      : {self.selected_language_interpreter.__class__.__name__},\n"
            f"  selected_logger           : {self.selected_logger.__class__.__name__},\n"
            f")"
        )