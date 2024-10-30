import os
import logging
import multiprocessing
import time
import sys
import traceback

from zip_checker import CFTCDataDownloader 

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def check_zip_updates(data_downloader, sleep_interval=60):
    while True:
        try:
            logging.info("Checking for zip file updates...")
            new_files = data_downloader.check_and_update_zip_files()
            if new_files:
                logging.info(f"New zip files downloaded: {new_files}")
                data_downloader.send_email_notification(new_files)
            time.sleep(sleep_interval)  
        except Exception as e:
            logging.error(f"Error while checking zip updates: {e}")
            logging.error(traceback.format_exc())  
            logging.warning("An error occurred. Retrying in 1 hour...")
            time.sleep(sleep_interval)  



if __name__ == "__main__":
    data_downloader = CFTCDataDownloader()
    new_files = 'Hello'
    data_downloader.send_email_notification(new_files)
