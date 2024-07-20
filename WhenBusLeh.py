import os
from datetime import datetime
import pytz
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

load_dotenv()

LTA_API_KEY = os.getenv('LTA_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

tz = pytz.timezone('Asia/Singapore')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Welcome! Use /bus <stop_id> to check for the next bus timing.')

async def bus(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) == 0:
          await update.message.reply_text('Please provide a bus stop ID.')
          return
     
    bus_stop_id = context.args[0]
    timings = get_bus_timing(bus_stop_id)

    if timings:
        response_message = 'Next buses:\n' + '\n'.join([f"Bus {bus['bus_number']} arriving in {bus['arrival_time']} minutes" for bus in timings])
    else:
        response_message = 'Could not retrieve bus timings. Please try again later.'

    # Incoming message is from CallbackHandler, NOT MessageHandler
    # Cannot use "update.message.reply_text" as it works only first-time command calls
    await update.effective_chat.send_message(response_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('This is a help message.')



def get_bus_timing(bus_stop_id):
        # Define the API endpoint
        api_url = "http://datamall2.mytransport.sg/ltaodataservice/BusArrivalv2"
        headers = {
             'AccountKey': LTA_API_KEY,
             'accept': 'application/json'
        }
        params = {
             'BusStopCode': bus_stop_id
        }

        try:
            # Make a GET request to the API endpoint using requests.get()
            response = requests.get(api_url,headers=headers, params=params)
            # Check if request was successful (status code 200)
            if response.status_code == 200:
                data = response.json()
                services = data.get('Services', [])
                next_buses = []
                for service in services:
                    bus_number = service['ServiceNo']
                    next_bus = service['NextBus']
                    if next_bus['EstimatedArrival']: # E.g. 2017-06-05T14:46:27+08:00, ISO 8601 format
                        arrival_time = datetime.fromisoformat(next_bus['EstimatedArrival']) 
                        dt_now_timezone = datetime.now(tz=tz)
                        # Calculate the time (in minutes) to arrival by taking time of arrival - current time
                        minutes = int((arrival_time - dt_now_timezone).total_seconds() / 60)
                        next_buses.append({
                            'bus_number': bus_number,
                            'arrival_time': minutes
                            })
                return next_buses
            else:
                print('Error: ', response.status_code)
                return None
        except requests.exceptions.RequestException as e:
            # Handle any network-related errors or exceptions
            print('Error: ', e)
            return None

def main() -> None:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Command handler for /start command
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("bus", bus))
    application.add_handler(CommandHandler("help", help_command))

    # Start bot
    application.run_polling()


if __name__ == '__main__':
    main()


## TypeError: Can't subtract offset-naive and offset-aware datetimes (line 61)
## Occurs when the offset-aware datetime object has information about the time zone, while offset-naive datetime object does not.