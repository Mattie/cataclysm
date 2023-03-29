from cataclysm import doom
import PIL

def main():
    """ App gets the img file from the command line and saves it as a new file at half size"""
    success = doom.resize_app()

if __name__ == '__main__':
    main()