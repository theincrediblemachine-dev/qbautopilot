import os
import time
import math
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
qbHost = os.getenv('QB_HOST','')
qbUser = os.getenv('QB_USER','')
qbPass = os.getenv('QB_PASS','')
debug = int(os.getenv('DEBUG',0))
checkFrequency = int(os.getenv('CHECK_FREQUENCY',60))
maxFinishDuration = int(os.getenv('MAX_FINISH_DURATION',-1))
maxStartDuration = int(os.getenv('MAX_START_DURATION',-1))
maxStallDuration = int(os.getenv('MAX_STALL_DURATION',-1))
maxSeedRatio = int(os.getenv('MAX_SEED_RATIO',-1))
maxSeedTime = int(os.getenv('MAX_SEED_TIME',-1)) 

# Check Properties
if not qbHost or not qbUser or not qbPass:
    logging.error(f'Invalid startup properties. Please ensure the following environment variables are configure: (QB_HOST/QB_USER/QB_PASS)')
    time.sleep(5)
    exit()

# QB Client
def ConnectClient():
    qb = qbclient(qbHost)
    qb.login(qbUser,qbPass)
    logging.info(f'Logging into QBittorrent {qbHost}')
    if debug == 1:
            logging.info(f'********** DEBUG ENABLED **********')
    return(qb)

# Fetch Torrents
def PurgeTorrents():
    torrentsProcessed=0
    resultReturn={}
    qbclient = ConnectClient()
    torrents = qbclient.torrents()
    logging.info(f"Detected ({len(torrents)}) torrents ...")
    
    for t in torrents:
        #print(t)
        torrentHash = t['hash']
        torrentName = t['name']
        startTime  = t['added_on']
        finishTime = t['completion_on']
        seedingTime = t['seeding_time']
        seedRatio = t['ratio']
        currentTime = time.time()
        startDuration = ((currentTime - startTime) / 60)

        if debug == 1:
            logging.info(torrentName)
            #logging.info(finishTime)
            #logging.info(t)

        if t['amount_left'] == 0:
            finishDuration = math.trunc(((finishTime - startTime) / 60))
            removeTime =  int(datetime.timedelta(seconds=(currentTime - finishTime)).total_seconds() // 60)
            #logging.info(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(startTime)))
            #logging.info(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(finishTime)))
        else:
            finishDuration = -1

        # Remove Completed Torrents Exceeding Finish Duration
        if (t['amount_left'] == 0) and (finishDuration > maxFinishDuration):
            logging.info(f'Removing completed torrent {torrentName}. Maximum finish duration exceeded ...')
            logging.info(f'Finish Duration: {finishDuration}, Max Finish Duration: {maxFinishDuration}')
            if debug == 0:
                qbclient.delete_permanently(torrentHash)
            torrentsProcessed+=1

        # Remove Torrents Exceeding Start
        if (not maxStartDuration == -1) and (startDuration > maxStartDuration):
            logging.info(f'Removing torrent {torrentName}. Maximum start duration exceeded ...')
            logging.info(f'Finish Duration: {finishDuration}, Max Finish Duration: {maxFinishDuration}')
            if debug == 0:
                qbclient.delete_permanently(torrentHash)
            torrentsProcessed+=1

        # Remove Seeded Torrents
        if (not maxSeedTime == -1) and (seedingTime > maxSeedTime):
            logging.info(f'Removing seeded torrent {torrentName}. Maximum seed time exceeded by {maxFinishDuration}- ...')
            logging.info(f'Finish For {finishDuration}, Max Finish Duration: {maxFinishDuration}')
            if debug == 0:
                qbclient.delete_permanently(torrentHash)
            torrentsProcessed+=1

        if (not maxSeedRatio == -1) and (seedRatio > maxSeedRatio):
            logging.info(f'Removing seeded torrent {torrentName}. Maximum seed ratio ...')
            logging.info(f'Finish Duration: {finishDuration}, Max Finish Duration: {maxFinishDuration}')            
            if debug == 0:
                qbclient.delete_permanently(torrentHash)
            torrentsProcessed+=1

        # Remove Stalled Torrents Exceeding Start Duration
        if (not maxStallDuration == -1) and (t['state'] == "stalledDL"):
            logging.info(f"Stalled torrent detected: {t['name']}. Will remove in torrent in {max(0,maxStallDuration-startDuration)} minutes ...")
            logging.info(f'Finish Duration: {finishDuration}, Max Finish Duration: {maxFinishDuration}')
            if startDuration > maxStallDuration and t['state'] == "stalledDL":
                logging.info(f'Removing torrent {torrentName}. Maximum stall duration exceeded ...')
                if debug == 0:
                    qbclient.delete_permanently(torrentHash)
                torrentsProcessed+=1

    if torrentsProcessed > 0:
        logging.info(f"Purged ({torrentsProcessed}) out of ({len(torrents)}) of torrents ...")
    else:
        logging.info(f"Nothing to purge ...")
    
    return(resultReturn)

def main():
    while True:
        PurgeTorrents()
        logging.info(f"Sleeping for {checkFrequency} seconds ...")
        time.sleep(checkFrequency)

if __name__ == "__main__":
    main()