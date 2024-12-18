# whereami bot

Telegram bot for <https://alifeee.co.uk/whereami/>

Development:

Obtain a Telegram API token by messaging <https://telegram.me/BotFather>.

```bash
# install
python -m venv env
source env/bin/activate
pip install -r requirements.txt
# key
cp .env.example .env
nano .env
# run
python bot.py
# create user to run the service 
sudo adduser --system --no-create-home --group whereami_bot
sudo chown -R alifeee:whereami_bot embeds/
sudo chown -R alifeee:whereami_bot name/
sudo chown -R alifeee:whereami_bot status/
sudo chown -R alifeee:whereami_bot updates/
# enable service
cp whereami_bot.service /etc/systemd/system/whereami_bot.service
sudo systemctl enable whereami_bot.service
sudo systemctl start whereami_bot.service
sudo systemctl status whereami_bot.service
```

Send either a location to the bot with `/location 51.12512 -1.21511`, or share a location (including live location) and a file like `embeds/2987827852.html` should be created with an OpenStreetMap (OSM) HTML embed within it. Clear your location with `/location clear`.

Embed the file in a website with:

```html
<iframe borderStyle=0 src="....../embeds/2987827852.html">
```
