# Telegram Scraper with SQLite
Scrape Telegram Groups and Channels into SQLite database

# Usage
## initial
- create a telegram application with your tg account: https://core.telegram.org/api/obtaining_api_id
- insert your telegram api credentials into credentials.json
- optional: create an environment
- install requirements: ´pip install -r requirements.txt´
- create a CSV with Groups and Channes to scrape using [Telegram Semiautomatic Search](https://github.com/gidzel/telegram-semiautomatic-search)

## the script
`python ./scrape.py groups-and-channels.csv`
- groups-and-channels.csv is the CSV containing the groups and channels (result of Telegram Semiautomatic Search)

The script will ask for a session name and creates a directory with this name for the export.
You can extend your dump at a later time by using the same session name.
The script will request a verification code which will be sent to your Telegram client.
It will also ask you to allow an export request in your Telegram client.
It will then start looping through your groups and channels provided in the CSV file and copying group/channel information, content and group usernames into the designated database tables.
