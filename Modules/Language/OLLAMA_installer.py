import subprocess
import platform

def install_ollama():
    os_type = platform.system()
    
    if os_type == 'Windows':
        # Use the winget command to install Ollama on Windows
        command = "winget install Ollama.Ollama"
    elif os_type == 'Darwin':  # macOS
        # Use the brew command to install Ollama on macOS
        command = "/bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\" && brew install ollama"
    elif os_type == 'Linux':
        # Use the appropriate package manager for Linux
        distro = platform.linux_distribution()[0].lower()
        if 'ubuntu' in distro or 'debian' in distro:
            command = "sudo apt-get update && sudo apt-get install -y ollama"
        elif 'fedora' in distro or 'centos' in distro:
            command = "sudo dnf install -y ollama"
        elif 'arch' in distro:
            command = "sudo pacman -S ollama"
        else:
            raise Exception("Unsupported Linux distribution")
    else:
        raise Exception("Unsupported Operating System")
    
    try:
        subprocess.run(command, shell=True, check=True)
        print("Ollama installation successful.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install Ollama: {e}")

def prompt_user(question):
    # Define acceptable responses for yes and no
    yes_responses = {'yes', 'y', 'Y', 'accept', 'ok', 'sure', 'affirmative', 'yeah', 'yep'}
    no_responses = {'no', 'n', 'N', 'reject', 'nope', 'negative'}

    while True:
        # Prompt the user
        response = input(f"{question} (yes/no): ").strip().lower()

        # Check if the response is in the acceptable yes responses
        if response in yes_responses:
            return True
        # Check if the response is in the acceptable no responses
        elif response in no_responses:
            return False
        else:
            print("Answer not accepted. Please respond with yes or no.")

if __name__ == "__main__":
    # Example usage
    answer = prompt_user("Do you want to continue?")
    if answer:
        print("You chose to continue.")
    else:
        print("You chose not to continue.")

