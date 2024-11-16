"""telegram bot to generate HTML files"""

import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    filters,
    ContextTypes,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
)
from typing import List

load_dotenv()
TOKEN = os.environ["TELEGRAM_API_KEY"]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

BASE_CSS='<link rel="stylesheet" href="./stylesheet.css">'

OSM_LINK = "https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=14/{lat}/{lon}"
# bbox like "-1.731657835%2C52.2582758528%2C-1.631657731%2C51.92878298"
OSM_EMBED = '<p>location: {lon}/{lat}. map may be out of date, so... <a target="_blank" href="https://www.openstreetmap.org/?mlat={lat}&amp;mlon={lon}#map=14/{lat}/{lon}">View Larger Map</a>, <small>last updated {nowtime}</small></p><iframe width="325" height="300" src="https://www.openstreetmap.org/export/embed.html?bbox={bbox}&amp;layer=mapnik&amp;marker={lat}%2C{lon}" style="border: 1px solid black"></iframe><br/>'

EMBED_HTML_FILE = "embeds/{id_}.html"
MESSAGES_HTML_FILE = "updates/{id_}.html"
STATUS_HTML_FILE = "status/{id_}.html"
NAME_FILE = "name/{id_}.txt"
BASE_URL = os.environ.get("BASE_URL", "...")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """say hi!"""
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="have a look at the commands, press some of them\nsend any message to send an update"
    )


def write_location(file, latitude, longitude):
    """write an OSM embed to embed.html"""
    # bbox
    bbox_lat_diff = 0.022525635
    bbox_lon_diff = 0.071668625
    bbox = (
        f"{longitude - bbox_lon_diff}%2C{latitude - bbox_lat_diff}"
        f"%2C{longitude + bbox_lon_diff}%2C{latitude+bbox_lat_diff}"
    )

    logging.info(
        "writing latlong to embed.html: %s, %s\nbbox: %s",
        latitude,
        longitude,
        bbox,
    )

    now = datetime.now()

    with open(file, "w", encoding="utf-8") as file:
        file.write(
            "<html><body>"
            + OSM_EMBED.format(
                bbox=bbox,
                lat=latitude,
                lon=longitude,
                nowtime=now.strftime('%Y-%m-%d %H:%M:%S')
            )
            + f"</body>{BASE_CSS}</html>"
        )


def clear_location(file):
    """blank the location file"""
    logging.info(
        "clearing location",
    )
    if os.path.exists(file):
      os.remove(file)

async def live_location(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """deal with live location updates"""
    message = None
    if update.edited_message:
        message = update.edited_message
    else:
        message = update.message
    current_pos = (message.location.latitude, message.location.longitude)
    latitude, longitude = current_pos

    id_ = update.effective_user.id
    write_file = EMBED_HTML_FILE.format(id_=id_)
    write_location(write_file, latitude, longitude)

    await message.reply_text(
        "updated your live location:\n"
        f"latitude: {latitude}\n"
        f"longitude: {longitude}\n"
        + OSM_LINK.format(
            lat=latitude,
            lon=longitude,
        )
        + f"\nto file: {BASE_URL}{write_file}",
    )


async def location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """command handler to manually change location"""
    latlong: List = context.args

    id_ = update.effective_user.id
    write_file = EMBED_HTML_FILE.format(id_=id_)

    if len(latlong) == 2:
        latitude, longitude = latlong
        latitude = float(latitude)
        longitude = float(longitude)

        write_location(write_file, latitude, longitude)

        await update.message.reply_text(
            "updated your live location:\n"
            f"latitude: {latitude}\n"
            f"longitude: {longitude}\n"
            + OSM_LINK.format(
                lat=latitude,
                lon=longitude,
            )
            + f"\nto the file: {BASE_URL}{write_file}",
        )
    elif len(latlong) == 1 and latlong[0] in ["none", "clear"]:
        clear_location(write_file)
        await update.message.reply_text(f"cleared location in {write_file}")
    else:
        await update.message.reply_text(
            '/location requires two arguments or "none", e.g., \n'
            "/location 53.377452 -1.465185\n"
            "/location none"
        )

async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
  id_ = update.effective_user.id
  write_file = MESSAGES_HTML_FILE.format(id_=id_)

  text = update.message.text
  now = datetime.now()
  html = f"<p>{text}, <small>{now.strftime('%Y-%m-%d %H:%M:%S')}</small></p>"

  try:
    with open(write_file, 'r', encoding="utf-8") as file:
      content=file.read()
  except FileNotFoundError as ex:
    content = BASE_CSS

  with open(write_file, 'w', encoding="utf-8") as file:
    file.write(html)
    file.write(content)

  await update.message.reply_text(f"updated {BASE_URL}{write_file}")

async def clear_updates(update: Update, context: ContextTypes.DEFAULT_TYPE):
  id_ = update.effective_user.id
  write_file = MESSAGES_HTML_FILE.format(id_=id_)

  if os.path.exists(write_file):
    os.remove(write_file)
    message = f"removed {write_file}"
  else:
    message = "no updates file existed. send some messages to add to one."

  await update.message.reply_text(message)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
  id_ = update.effective_user.id
  write_file = STATUS_HTML_FILE.format(id_=id_)

  if len(context.args) == 0:
    if os.path.exists(write_file):
      os.remove(write_file)
      message = f"removed status file {write_file}"
    else:
      message = "no status file to remove"
  else:
    text = " ".join(context.args)
    now = datetime.now()
    html = f"<p>{text}, <small>{now.strftime('%Y-%m-%d %H:%M:%S')}</small></p>"

    with open(write_file, 'w', encoding="utf-8") as file:
      file.write(BASE_CSS)
      file.write(html)

    message = f"updated {BASE_URL}{write_file}"

  await update.message.reply_text(message + "\nchange status with /status <status>")

async def name(update: Update, context: ContextTypes.DEFAULT_TYPE):
  id_ = update.effective_user.id
  write_file = NAME_FILE.format(id_=id_)

  name_arr = context.args
  if len(name_arr) == 0:
    if os.path.exists(write_file):
      message = "removed_name..."
      os.remove(write_file)
    else:
      message = "no name to remove..."
  else:
    name = " ".join(name_arr)
    with open(write_file, 'w', encoding="utf-8") as file:
      file.write(name)
    message = f"changed your name to {name}"

  await update.message.reply_text(message + "\nuse /name <your name> to set your name or just /name to blank")




if __name__ == "__main__":

    application = ApplicationBuilder().token(TOKEN).build()

    start_handler = CommandHandler(
        "start",
        start,
    )
    live_location_handler = MessageHandler(
        filters.LOCATION,
        live_location,
    )
    location_handler = CommandHandler("location", location)
    loc_handler = CommandHandler("loc", location)
    message_handler = MessageHandler(
      filters.ALL,
      message
    )
    status_handler = CommandHandler("status", status)
    name_handler = CommandHandler("name", name)
    clear_handler = CommandHandler("clear", clear_updates)

    application.add_handler(start_handler)
    application.add_handler(live_location_handler)
    application.add_handler(location_handler)
    application.add_handler(loc_handler)
    application.add_handler(status_handler)
    application.add_handler(name_handler)
    application.add_handler(clear_handler)
    # catch-all
    application.add_handler(message_handler)


    application.run_polling()
