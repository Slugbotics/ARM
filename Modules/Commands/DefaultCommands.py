def register_default_commands(commands_instance):
    def help_command(_):
        print("Available commands:")
        for cmd_name, cmd_info in commands_instance.commands.items():
            print(f"{cmd_name}: {cmd_info['help']}")

    def run_file_command(args):
        try:
            with open(args.strip(), 'r') as file:
                for line in file:
                    commands_instance.run_command(line.strip())
        except FileNotFoundError:
            print(f"File not found: {args}")
        except Exception as e:
            print(f"Error running file commands: {e}")

    # Register default commands
    commands_instance.add_command("help", help_command, "Displays this help text", aliases=["?"])
    commands_instance.add_command("run", run_file_command, "Runs commands from a file")
