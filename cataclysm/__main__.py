from loguru import logger
import os

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


def initialize_datafiles(base_dir = "."):
    print("cataclysm - initializing datafiles in directory: " + base_dir)
    chatsnack_base_dir = os.getenv("CHATSNACK_BASE_DIR", "./datafiles/chatsnack").rstrip("/\\")

    package_name = (__package__ or "cataclysm").split(".")[0]
    
    minimum_file_suffixes = [
        f"datafiles/chatsnack/CataclysmQuery.yml",
        f"env.template.cataclysm"
    ]

    from importlib.resources import as_file, files
    import shutil
    def copy_files_to_destination(package_name, file_suffixes, destination):
        for file_suffix in file_suffixes:
            dest_file_suffix = file_suffix.replace("datafiles/chatsnack", chatsnack_base_dir)
            dest_filename = os.path.join(destination, dest_file_suffix)
            if not os.path.exists(dest_filename):
                print("  Copying default file to " + dest_filename)
                # Get the path to the file within the package
                source_resource = files(package_name).joinpath(
                    "default_files", *file_suffix.split("/")
                )

                # Construct the destination file path
                destination_file = dest_filename
                print("  destination_file: " + destination_file)

                # Create any necessary directories in the destination path
                destination_dir = os.path.dirname(destination_file)
                if destination_dir:
                    os.makedirs(destination_dir, exist_ok=True)

                # Copy the file
                with as_file(source_resource) as source_file:
                    print("  source_file: " + str(source_file))
                    shutil.copy2(source_file, destination_file)

    copy_files_to_destination(package_name, minimum_file_suffixes, base_dir)

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
