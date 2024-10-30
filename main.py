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
    # Create an instance of CFTCDataDownloader to manage zip file updates
    data_downloader = CFTCDataDownloader()
    test_file = 'test'
    data_downloader.send_email_notification(test_file)

    # Run the zip checker first to ensure files are downloaded
    data_downloader.check_and_update_zip_files()
    
    # Now import app_cftc after the zip files have been checked/updated
    from app_cftc import app

    # Start the zip checker in a separate process for continuous checking
    zip_process = multiprocessing.Process(target=check_zip_updates, args=(data_downloader,))
    zip_process.start()

    try:
        # Run the Dash app
        app.run_server(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("Keyboard interrupt received, terminating processes...")
    finally:
        zip_process.terminate()  # Ensure the subprocess is properly terminated
        zip_process.join()  # Wait for the subprocess to cleanly exit
        print("Process terminated, exiting...")