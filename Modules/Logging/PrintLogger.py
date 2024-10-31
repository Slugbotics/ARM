import os
import sys
import datetime

from Modules.Base.TextOut import TextOut
    
class PrintLogger(TextOut):
    def __init__(self, log_dir="Logs", include_datestamp=False):
        self.log_dir = log_dir
        self.include_datestamp = include_datestamp
        self.log_file = None
        self.original_stdout = sys.stdout
        self.capturing = False        

    def _generate_log_file_name(self):
        # Create a timestamped file name
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return os.path.join(self.log_dir, f"{timestamp}_log.txt")

    def _write(self, message):
        # Prepend a datestamp if needed
        if self.include_datestamp:
            message = f"{datetime.datetime.now().isoformat()} - {message}"
        
        # Write to both file and standard output
        if self.log_file:
            self.log_file.write(message)
            self.log_file.flush()
        self.original_stdout.write(message)
        self.original_stdout.flush()

    def start_capturing(self):
        if not self.capturing:
            
            # Ensure the logging directory exists
            if not os.path.exists(self.log_dir):
                os.makedirs(self.log_dir)
            
            self.capturing = True
            self.log_file = open(self._generate_log_file_name(), 'a')
            sys.stdout = self

    def stop_capturing(self):
        if self.capturing:
            sys.stdout = self.original_stdout
            if self.log_file:
                self.log_file.close()
                self.log_file = None
            self.capturing = False

    def write(self, message):
        # Redirecting print messages to the log
        self._write(message)

    def flush(self):
        # Needed to support the flush method used by some output systems
        pass
    
    def write_line(self, text: str) -> None:
        if self.capturing:
            self._write(text + "\n")
            
    def start(self):
        self.start_capturing()
        
    def stop(self):
        self.stop_capturing()