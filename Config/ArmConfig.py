import argparse
import json
from typing import Dict
from typing import Any

class ArmConfig:
    
    # Configuration
    # these are the default values, they are saved in a file called config.json that is ignored by git.
    # if you add or rename parameters, please increment config_version for everything to work properly. 
    CONFIG_DEFAULT_DICT = {
        "use_simulator" : True,
        "use_physical" : False,        
        "use_app" : False,
        "use_server" : True,
        "use_twitch" : False,
        "use_stt" : True,
        "stt_push_to_talk" : False,
        "stt_model_large" : False,
        "open_startup_page" : False,
        "write_logs" : True,
        "use_tts" : True,
        "use_language_model": True,
        "language_model_file" : "Arm.Modelfile",
        "twitch_id": "NONE",
        "twitch_secret" : "NONE",
        "twitch_channel_name" : "ucscarm",   
        "sim_host": "localhost",
        "server_host_port": "8000",
    }
    
    def load_config(self, config_file_path: str = 'config.json') -> Dict[str, Any]:
        config = dict(self.CONFIG_DEFAULT_DICT)  # Create a copy of the default config
        json_object = {}
        config_updated = False
        try:
            with open(config_file_path, 'r') as openfile:
                json_object = json.load(openfile)
        except:
            config_updated = True

        for key in config.keys():
            if key not in json_object:
                json_object[key] = config[key]
                config_updated = True
        config = json_object

        if config_updated:
            print("Config updated. Saving config file with new properties...")
            json_str = json.dumps(config, indent=4)
            with open("config.json", "w") as outfile:
                outfile.write(json_str)
        return config
    
    def parse_args(self, config: Dict[str, Any]) -> None:
        # ARG parsing
        parser = argparse.ArgumentParser()

        # Function to handle the custom logic for --mode
        def twitch_channel_name_type(value):
            if value is None:
                return "ucscarm"
            try:
                return str(value)
            except ValueError:
                raise argparse.ArgumentTypeError(f"Invalid twitch channel value: {value}")

        # Adding optional argument
        parser.add_argument("-s", "--simulator", help = "Use the Coppeliasim hardware interface.")
        parser.add_argument("-p", "--physical", help = "Use the Physical hardware interface.")
        parser.add_argument("--use_app", help = "Use the app as the controler.")
        parser.add_argument("--disable_server", action='store_true', help = "Disable the locally hosted server.")
        parser.add_argument('--twitch_chat', nargs='?', const="ucscarm", type=twitch_channel_name_type, help='If passed in, will connect to provided twitch channel (default is ucscarm).')
        parser.add_argument("--write_logs", help = "Will write console messages to a file.")
        parser.add_argument("--use_speech_to_text", help = "Enable the speech to text system.")
        
        # Read arguments from command line
        args = parser.parse_args()
        if args.simulator:
            config["use_simulator"] = True
        if args.physical:
            config["use_simulator"] = True
        if args.disable_server:
            config["use_server"] = False
        if args.twitch_chat is not None:
            config["use_twitch"] = True
            config["twitch_channel_name"] = args.twitch_chat
        if args.use_app:
            config["use_app"] = True
        if args.write_logs:
            config["write_logs"] = True
        if args.use_speech_to_text:
            config["use_stt"] = True
            