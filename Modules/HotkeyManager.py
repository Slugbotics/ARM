from pynput import keyboard

class HotkeyManager:
    def __init__(self):
        self.listener = None
        self.hotkeys = {}
        self.current_keys = set()
        self.key_press_callbacks = {} 
        self.key_release_callbacks = {} 

    def add_hotkey(self, keys, callback):
        """
        Add a hotkey with the specified keys and callback function.

        :param keys: A set of keys that make up the hotkey.
        :param callback: A function to call when the hotkey is triggered.
        """
        self.hotkeys[frozenset(keys)] = callback
        
    def add_key_press_callback(self, key, callback):
        """
        Add a callback function for when a specific key is pressed.

        :param key: The key to listen for.
        :param callback: A function to call when the key is pressed.
        """
        self.key_press_callbacks[key] = callback

    def add_key_release_callback(self, key, callback):
        """
        Add a callback function for when a specific key is released.

        :param key: The key to listen for.
        :param callback: A function to call when the key is released.
        """
        self.key_release_callbacks[key] = callback

    def on_press(self, key):
        try:
            self.current_keys.add(key.char)
        except AttributeError:
            self.current_keys.add(key)

        # Check hotkeys
        self.check_hotkeys()

        # Call key press callbacks if available
        if key in self.key_press_callbacks:
            self.key_press_callbacks[key]()

    def on_release(self, key):
        try:
            if key.char in self.current_keys:
                self.current_keys.remove(key.char)
        except AttributeError:
            if key in self.current_keys:
                self.current_keys.remove(key)

        # Call key release callbacks if available
        if key in self.key_release_callbacks:
            self.key_release_callbacks[key]()

    def check_hotkeys(self):
        for hotkey, callback in self.hotkeys.items():
            if hotkey <= self.current_keys:
                callback()

    def start(self):
        self.listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        )
        self.listener.start()

    def stop(self):
        if self.listener is not None:
            self.listener.stop()

if __name__ == "__main__":
    keep_running = True
    def test_hotkey():
        print("Hotkey triggered! test")
    def test_exit():
        global keep_running
        keep_running = False
    def hotkey_triggered(): 
        print("Hotkey triggered!")
        
    def key_press_triggered():
        print("Key pressed!")

    def key_release_triggered():
        print("Key released!")

    hotkey_manager = HotkeyManager()
    # Example hotkey: Ctrl+Shift+A
    hotkey_manager.add_hotkey({'a'}, test_hotkey)
    # hotkey_manager.add_hotkey({' '}, test_exit)
    # Registering hotkeys for Escape, Spacebar, Ctrl, and Shift 
    hotkey_manager.add_hotkey({keyboard.Key.esc}, hotkey_triggered) 
    hotkey_manager.add_hotkey({keyboard.Key.space}, hotkey_triggered) 
    hotkey_manager.add_hotkey({keyboard.Key.ctrl_l}, hotkey_triggered) 
    hotkey_manager.add_hotkey({keyboard.Key.ctrl_r}, hotkey_triggered) 
    hotkey_manager.add_hotkey({keyboard.Key.shift}, hotkey_triggered)
    
    # Registering key press and release callbacks
    hotkey_manager.add_key_press_callback(keyboard.Key.esc, key_press_triggered)
    hotkey_manager.add_key_release_callback(keyboard.Key.esc, key_release_triggered)
    
    hotkey_manager.start()

    print("Hotkey manager started. Press 'space' to trigger the hotkey. Press Esc to exit.")
    try:
        while keep_running:
            pass  # Keep the script running
    except KeyboardInterrupt:
        hotkey_manager.stop()
