from loguru import logger
import os

from . import initialize_datafiles

# if there's no "CATACLYSM_BASE_DIR" env variable, set it to './datafiles/cataclysm'
# this is the default directory for all cataclysm datafiles
if os.getenv("CATACLYSM_BASE_DIR") is None:
    CATACLYSM_BASE_DIR = "./datafiles/cataclysm"
else:
    CATACLYSM_BASE_DIR = os.getenv("CATACLYSM_BASE_DIR")
    CATACLYSM_BASE_DIR = CATACLYSM_BASE_DIR.rstrip("/")


# Configure logging
logs_dir = os.environ.get('CATACLYSM_LOGS_DIR', './logs/')

# Create a file sink that writes log messages to cataclysm.log in the logs directory
file_sink = {
    "sink": os.path.join(logs_dir, "cataclysm.log"),
    "format": "{time} - {message}",
}

# Add the file sink to Loguru's sinks
logger.add(**file_sink)

# disable debug logging for the chatsnack module
logger.disable("chatsnack")


from .doomed import doom
from .total import consume

def main():
    # logging config should exclude warnings
    config = {
        "handlers": [
            {"sink": os.path.join(logs_dir, "cataclysm.log"), "format": "{time} - {message}"},
        ],
        "extra": {"user": "someone"},
    }
    logger.configure(**config)

    # if they passed in the "init" argument, initialize the datafiles
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        initialize_datafiles()
        return
    
    # for now tell them we only have one command-line parameter (init) and what it does
    print("\ncataclysm: Embracing the End of Software Development\n")
    print("    DISCLAIMER: cataclysm generates AI-designed code and executes it.")
    print("                This is dangerous-- use at your own peril! 😱\n")
    print("\nUsage: cataclysm <command>\n")
    print("Commands:")
    print("\tinit:\tinitialize the datafiles in the current directory\n")
    # print the location to the base github repo
    print("For more information or to report issues, visit https://github.com/Mattie/cataclysm\n")


if __name__ == "__main__":
    main()
