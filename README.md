# LaserPulse
Repository for assessing the uncertainty of laser pulseshapes

## Get your data
*Currently this only works for Linux machines. If you want to use this on a windows or mac,
you need to change the path in the DriverHandler class in scrape_metadata.py accordingly
Then add in the correct chromedriver, and you should be in business*
1. Edit user.py to contain your username and password for lle
2. run scrape_metadata.py
    - tgz files containing pulseshape information are stored in Data/tgz_files
