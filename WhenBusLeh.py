import os
from datetime import datetime
import pytz
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

load_dotenv()

LTA_API_KEY = os.getenv('LTA_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

tz = pytz.timezone('Asia/Singapore')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Welcome! Use /help for a guide on how to use the commands.')

async def busstop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) == 0:
          await update.message.reply_text('Please provide a bus stop ID.')
          return
     
    bus_stop_id = context.args[0]
    timings = get_bus_timing(bus_stop_id)

    if timings:
        await update.effective_chat.send_message(f"Here are the arrival timing of buses for bus stop {bus_stop_id}:")
        for timing in timings:
            arr_time = timing['arrival_time']
            if arr_time == 0:
                response_message = (f"Bus {timing['bus_number']} is arriving now!")
            elif arr_time == 1:
                response_message = (f"Bus {timing['bus_number']} is arriving in {arr_time} minute.")
            else:
                response_message = (f"Bus {timing['bus_number']} arriving in {arr_time} minutes.")
            await update.effective_chat.send_message(response_message)
    else:
        response_message = 'Could not retrieve bus timings. Please try again later.'
        await update.effective_chat.send_message(response_message)

    # Incoming message is from CallbackHandler, NOT MessageHandler
    # Cannot use "update.message.reply_text" as it works only first-time command calls

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('''
The following commands are available:

/help - Brings out this help menu.

/run - Automatically locates the nearest bus stop to you and outputs the bus arrival timings.

/busstop <stop_id> - Outputs the bus arrival timings of a specific bus stop. The bus stop ID is a 5 digit number. It can be found on the top right corner of directory boards or above the names of the bus station in bus stop signs. 
'''
)



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

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Sorry, I do not recognize that command. Check if the command has been mispelt!")

def main() -> None:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Command handler for /start command
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("busstop", busstop))
    application.add_handler(CommandHandler("help", help_command))

    # MessageHandler for unrecognized commands
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    # Start bot
    application.run_polling()


if __name__ == '__main__':
    main()


## TypeError: Can't subtract offset-naive and offset-aware datetimes (line 61)
## Occurs when the offset-aware datetime object has information about the time zone, while offset-naive datetime object does not.