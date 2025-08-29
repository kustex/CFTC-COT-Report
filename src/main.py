import os
import logging
import multiprocessing
import time
import traceback
from zip_checker import CFTCDataDownloader

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

if __name__ == "__main__":
    CFTC = CFTCDataDownloader()
    CFTC.check_and_update_zip_files()

    # Start the background process for hourly zip updates
    from app_cftc import app

    zip_update_process = multiprocessing.Process(target=CFTC.check_zip_updates)
    zip_update_process.start()

    try:
        app.run(host="0.0.0.0", port=5000, debug=False)
    except KeyboardInterrupt:
        print("Keyboard interrupt received, terminating background update process...")
    finally:
        zip_update_process.terminate()
        zip_update_process.join()

    
    
    
    
    
    
    
    