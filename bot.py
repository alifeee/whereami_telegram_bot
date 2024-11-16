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


OSM_LINK = "https://www.openstreetmap.org/?mlat={lat}&mlon={long}#map=14/{lat}/{long}"
# bbox like "-1.731657835%2C52.2582758528%2C-1.631657731%2C51.92878298"
OSM_EMBED = '<iframe width="425" height="350" src="https://www.openstreetmap.org/export/embed.html?bbox={bbox}&amp;layer=mapnik&amp;marker={lat}%2C{long}" style="border: 1px solid black"></iframe><br/><small><a href="https://www.openstreetmap.org/?mlat={lat}&amp;mlon={long}#map=14/{lat}/{long}">View Larger Map</a></small>'

EMBED_HTML_FILE = "embeds/{id_}.html"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """say hi!"""
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!"
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
                long=longitude,
            )
            + f", <small>last updated: {now.strftime('%Y-%m-%d %H:%M:%S')}</small>"
            "</body></html>"
        )


def clear_location(file):
    """blank the location file"""
    logging.info(
        "clearing location",
    )
    with open(file, "w", encoding="utf-8") as file:
        file.write("<html><body><small>no location at the moment</small></body></html>")


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
    write_file = EMBED_HTML_FILE.format(id_=id)
    write_location(write_file, latitude, longitude)

    await message.reply_text(
        "updated your live location:\n"
        f"latitude: {latitude}\n"
        f"longitude: {longitude}\n"
        + OSM_LINK.format(
            lat=latitude,
            long=longitude,
        )
        + f"\nto the file: {write_file}",
    )
    print(current_pos)


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
                long=longitude,
            )
            + f"\nto the file: {write_file}",
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
    location_handler = CommandHandler(
        "location",
        location,
    )

    application.add_handler(start_handler)
    application.add_handler(live_location_handler)
    application.add_handler(location_handler)

    application.run_polling()
