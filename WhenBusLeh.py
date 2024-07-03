import os
from datetime import datetime

import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

load_dotenv()

LTA_API_KEY = os.getenv('LTA_API_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

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

    await update.message.reply_text(response_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('This is a help message.')



def get_bus_timing(bus_stop_id):
        # Replace with actual API endpoint and API key if required
        api_url = "http://datamall2.mytransport.sg/ltaodataservice/BusArrivalv2" # May be wrong
        headers = {
             'AccountKey': LTA_API_KEY,
             'accept': 'application/json'
        }
        params = {
             'BusStopCode': bus_stop_id
        }



        response = requests.get(api_url,headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            services = data.get('Services', [])
            next_buses = []
            for service in services:
                 bus_number = service['ServiceNo']
                 next_bus = service['NextBus']
                 if next_bus['EstimatedArrival']:
                      arrival_time = datetime.fromisoformat(next_bus['EstimatedArrival'])
                      minutes = int((arrival_time - datetime.now()).total_seconds() / 60)
                      next_buses.append({
                           'bus_number': bus_number,
                           'arrival_time': minutes
                        })
            return next_buses
        else:
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