import os
import sys
from codereview.config import Config

def handle_config(args, config):
    subcommand = args.config_subcommand
    env_file = ".env"
    
    if subcommand == "init":
        if os.path.exists(env_file):
            print(f"Configuration file '{env_file}' already exists. Skipping initialization.")
            return
            
        try:
            with open(env_file, "w", encoding="utf-8") as f:
                f.write("""# Codivus Local Configuration
OPENAI_API_KEY=your_openai_api_key_here
DEFAULT_PROVIDER=openai
DEFAULT_MODEL=gpt-4o
TEMPERATURE=0.2
""")
            print(f"Initialized default template configuration in: {os.path.abspath(env_file)}")
        except Exception as e:
            print(f"Error creating configuration file: {str(e)}", file=sys.stderr)
            sys.exit(1)
            
    elif subcommand == "show":
        print("--- Active Configuration Key-Values ---")
        print(f"Loaded config file: {os.path.abspath(env_file) if os.path.exists(env_file) else 'None (using environment/defaults)'}")
        print(f"  DEFAULT_PROVIDER: {config.default_provider}")
        print(f"  DEFAULT_MODEL:    {config.default_model}")
        print(f"  TEMPERATURE:      {config.temperature}")
        
        key = config.openai_api_key
        if key:
            redacted = key[:8] + "..." + key[-4:] if len(key) > 12 else "[REDACTED]"
            print(f"  OPENAI_API_KEY:   {redacted}")
        else:
            print("  OPENAI_API_KEY:   [NOT CONFIGURED]")
            
    elif subcommand == "set":
        if not args.key or not args.value:
            print("Error: config set requires key and value. E.g. 'codivus config set default_model gpt-4o'", file=sys.stderr)
            sys.exit(1)
            
        key = args.key.upper()
        value = args.value
        
        env_lines = []
        replaced = False
        if os.path.exists(env_file):
            try:
                with open(env_file, "r", encoding="utf-8") as f:
                    env_lines = f.readlines()
            except Exception as e:
                print(f"Error reading configuration file: {str(e)}", file=sys.stderr)
                sys.exit(1)
                
        for idx, line in enumerate(env_lines):
            if line.strip().startswith(f"{key}="):
                env_lines[idx] = f"{key}={value}\n"
                replaced = True
                break
                
        if not replaced:
            env_lines.append(f"{key}={value}\n")
            
        try:
            with open(env_file, "w", encoding="utf-8") as f:
                f.writelines(env_lines)
            print(f"Successfully set {key}={value} in: {os.path.abspath(env_file)}")
        except Exception as e:
            print(f"Error writing to configuration file: {str(e)}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Error: Unknown config subcommand. Use: init, show, or set.", file=sys.stderr)
        sys.exit(1)
