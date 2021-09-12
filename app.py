import os
import time
import datetime
import logging 
from dotenv import load_dotenv
from qbittorrent import Client as qbclient

#Configure Logging
logging.basicConfig()
logging.root.setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO)

# Set Variables
load_dotenv()
qbHost = os.getenv('qbHost','')
qbUser = os.getenv('qbUser','')
qbPass = os.getenv('qbPass','')
checkFrequency = int(os.getenv('checkFrequency',60))
maxFinishDuration = int(os.getenv('maxFinishDuration',480))
maxStartDuration = int(os.getenv('maxStartDuration',1440))

# Check Properties
if not qbHost or not qbUser or not qbPass:
    logging.error(f'Invalid startup properties. Please ensure the following environment variables are configure: (qbHost/qbUser/qbPass)')
    time.sleep(5)
    exit()

# QB Client
def ConnectClient():
    qb = qbclient(qbHost)
    qb.login(qbUser,qbPass)
    logging.info(f'Logging into QBittorrent {qbHost}')
    return(qb)

# Fetch Torrents
def PurgeTorrents():
    torrentsProcessed=0
    resultReturn={}
    qbclient = ConnectClient()
    torrents = qbclient.torrents()
    logging.info(f'Seeking {len(torrents)} torrents for purge candidates ...')
    
    for t in torrents:
        torrentHash = t['hash']
        torrentName = t['name']
        startTime  = t['added_on']
        finishTime = t['completion_on']
        currentTime = time.time()
        startDuration = int(datetime.timedelta(seconds=(currentTime - startTime)).total_seconds() // 60)
        if t['amount_left'] == 0:
            finishDuration = int(datetime.timedelta(seconds=(currentTime - finishTime)).total_seconds() // 60)
        else:
            finishDuration = 0

        # Remove Completed Torrents Exceeding Finish Duration
        if finishDuration > maxFinishDuration:
            logging.info(f'Removing completed torrent {torrentName}. Maximum finish duration exceeded ...')
            qbclient.delete_permanently(torrentHash)
            torrentsProcessed+=1

        # Remove Stalled Torrents Exceeding Start Duration
        if t['state'] == "stalledDL":
            logging.info(f"Stalled torrent detected: {t['name']}. Will remove in torrent in {maxStartDuration-startDuration} minutes ...")
        if startDuration > maxStartDuration and t['state'] == "stalledDL":
            logging.info(f'Removing torrent {torrentName}. Maximum start duration exceeded ...')
            qbclient.delete_permanently(torrentHash)
            torrentsProcessed+=1
    if torrentsProcessed > 0:
        logging.info(f"Successfully purged {torrentsProcessed} torrents ...")
    else:
        logging.info(f"No torrents to purge ...")
    
    return(resultReturn)

def main():
    while True:
        PurgeTorrents()
        logging.info(f"Sleeping for {checkFrequency} seconds ...")
        time.sleep(checkFrequency)

if __name__ == "__main__":
    main()