import os
import logging
import multiprocessing
import time
import traceback
from zip_checker import CFTCDataDownloader

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to check for updates
# def start_zip_update_process(data_downloader, interval=60):
#     """Background process to check for zip updates every `interval` seconds."""
#     while True:
#         try:
#             logging.info("Checking for zip file updates...")
#             data_downloader.check_and_update_zip_files()
#         except Exception as e:
#             logging.error("Error during zip file update check:", exc_info=True)
#         time.sleep(interval)

if __name__ == "__main__":
    CFTC = CFTCDataDownloader()
    CFTC.check_and_update_zip_files()

    # Start the background process for hourly zip updates
    from app_cftc import app

    zip_update_process = multiprocessing.Process(target=CFTC.check_zip_updates)
    zip_update_process.start()

    try:
        app.run_server(host="0.0.0.0", port=5000, debug=False)
    except KeyboardInterrupt:
        print("Keyboard interrupt received, terminating background update process...")
    finally:
        zip_update_process.terminate()
        zip_update_process.join()

    
    
    
    
    
    
    
    