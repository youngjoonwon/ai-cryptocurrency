mkdir src
cd ./src
mkdir csv
mkdir model
mkdir sim
sudo apt-get update
sudo apt-get install python2.7
sudo apt-get install python-pip python-dev build-essential
export LC_ALL=C
sudo apt-get install rake
sudo pip install --upgrade pip
sudo pip install --upgrade virtualenv
sudo pip install matplotlib
sudo pip install pandas
sudo apt-get install python-pycurl
pip install --upgrade pip
sudo -H pip install python-dateutil
sudo -H pip install requests==2.10.0
sudo -H pip install certifi
sudo -H pip install scipy
sudo -H pip install statsmodels
sudo -H pip install sh
sudo -H pip install telepot
sudo -H pip install pyOpenSSL
sudo pip install APScheduler
sudo timedatectl set-timezone Asia/Tokyo
curl -L https://bit.ly/janus-bootstrap | bash
sudo pip install websocket-client
sudo pip install PyJWT
export PYTHONWARNINGS="ignore:Unverified HTTPS request"
