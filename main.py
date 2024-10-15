import os
import logging
import multiprocessing
import time
import sys
import smtplib
import ssl
import traceback

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from zip_checker import CFTCDataDownloader 

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def send_email_notification(new_files):
    # Set up the email details from environment variables
    sender_email = os.environ.get("EMAIL_USER")  # GitHub Secret
    receiver_email = os.environ.get("EMAIL_USER")  # Assuming you are sending to yourself
    password = os.environ.get("EMAIL_PASSWORD")  # GitHub Secret

    logging.info(f"Sender email: {sender_email}")
    logging.info(f"Password: {password}")  

    subject = "New Zip Files Downloaded"
    body = f"The following new zip files have been downloaded:\n\n" + "\n".join(new_files)

    # Create a multipart email message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    # Attach the email body to the message
    msg.attach(MIMEText(body, 'plain'))

    # Send the email
    context = ssl.create_default_context()
    with smtplib.SMTP("smtp.office365.com", 587) as server: 
        server.starttls(context=context)
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())

def check_zip_updates(data_downloader, sleep_interval=3600, max_retries=3):
    retries = 0

    while True:
        try:
            logging.info("Checking for zip file updates...")

            # Check and update zip files, returning any new files
            new_files = data_downloader.check_and_update_zip_files()

            if new_files:
                logging.info(f"New zip files downloaded: {new_files}")
                send_email_notification(new_files)
            
            # Reset retries if successful
            retries = 0
            time.sleep(sleep_interval)  # Sleep for the configured interval before checking again

        except Exception as e:
            logging.error(f"Error while checking zip updates: {e}")
            logging.error(traceback.format_exc())  # Log full stack trace for debugging

            # Implement retry logic with exponential backoff
            retries += 1
            if retries <= max_retries:
                backoff_time = min(sleep_interval * 2 ** retries, 7200)  # Exponential backoff, up to 2 hours
                logging.warning(f"Retrying in {backoff_time} seconds... (Attempt {retries}/{max_retries})")
                time.sleep(backoff_time)
            else:
                logging.error("Max retries exceeded. Aborting further attempts.")
                break  # Exit the loop if retries are exhausted

if __name__ == "__main__":
    # Create an instance of CFTCDataDownloader to manage zip file updates
    data_downloader = CFTCDataDownloader()
    send_email_notification('new_files')

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

