from loguru import logger
import logging
import os

CHATSNACK_BASE_DIR = os.getenv("CHATSNACK_BASE_DIR", "./datafiles/chatsnack").rstrip("/\\")

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
# disable warning logging for the datafiles module
logger.disable("datafiles")

logging.getLogger("datafiles").setLevel(logging.ERROR)


def initialize_datafiles(base_dir = "."):
    chatsnack_base_dir = os.getenv("CHATSNACK_BASE_DIR", "./datafiles/chatsnack").rstrip("/\\")

    # Replace this with the name of your package
    def get_top_level_package_name():
        return __name__.split('.')[0]

    package_name = get_top_level_package_name()
    print("package_name: " + package_name)

    minimum_file_suffixes = [
        f"datafiles/chatsnack/CataclysmQuery.yml",
        f"env.template.cataclysm"
    ]

    from pkg_resources import resource_filename
    import shutil
    def copy_files_to_destination(package_name, file_suffixes, destination):
        for file_suffix in file_suffixes:
            dest_file_suffix = file_suffix.replace("datafiles/chatsnack", chatsnack_base_dir)
            dest_filename = os.path.join(destination, dest_file_suffix)
            if not os.path.exists(dest_filename):
                print("Copying default datafiles to " + dest_filename)
                # Get the path to the file within the package
                source_file = resource_filename(package_name, "default_files/" + file_suffix)
                print("source_file: " + source_file)

                # Construct the destination file path
                destination_file = dest_filename
                print("destination_file: " + destination_file)

                # Create any necessary directories in the destination path
                destination_dir = os.path.dirname(destination_file)
                if destination_dir:
                    os.makedirs(destination_dir, exist_ok=True)

                # Copy the file
                shutil.copy2(source_file, destination_file)

    copy_files_to_destination(package_name, minimum_file_suffixes, base_dir)

from .yamlformat import *
from .doomed import doom
from .total import consume
