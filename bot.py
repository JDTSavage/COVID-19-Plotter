# Author: Joseph Savage
# Date: July 29, 2020
# COVID-19 is going strong and I am bored, why not do some plotting?
# Data plotted from JHU GitHub repository:
# COVID-19 Data Repository by the Center for Systems Science and Engineering (CSSE) at Johns Hopkins University
# https://github.com/CSSEGISandData/COVID-19


from urllib.error import HTTPError
import discord
import os
import gc
from dotenv import load_dotenv
import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
import manipulation_plotting as mp


# Run the bot
def main():
    # Token is loaded in from .env file, keeps token out of shell history. See README
    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')  # Loads in the bot's token.
    global SENT  # Determine if request was successful

    delta = 1
    date = dt.date.today() - dt.timedelta(days=delta)  # Get yesterday's date for data access
    date = date.strftime('%m-%d-%Y')  # Get date as a string

    # To ensure that a valid link is obtained (in the case that data was updated behind schedule) try/except for
    # valid date
    try:
        url_us_reports = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data" \
                         "/csse_covid_19_daily_reports_us/" + date + ".csv "
        data = pd.read_csv(url_us_reports, error_bad_lines=False)
    except HTTPError:
        delta += 1
        date = dt.datetime.strptime(date, '%m-%d-%Y') - dt.timedelta(days=delta)  # Get yesterday's date for data access
        date = date.strftime('%m-%d-%Y')
        url_us_reports = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data" \
                         "/csse_covid_19_daily_reports_us/" + date + ".csv "
    # US cases link
    url_us_cases_ts = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data" \
                      "/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv "

    client = discord.Client()  # Begin the bot client

    @client.event
    async def on_ready():
        print(f'{client.user} has connected to Discord')

    @client.event
    async def on_message(message):
        # message contains discord message information
        if message.content.startswith("~covid"):  # Check for command message
            print("COVID PLOTTING REQUEST")
            SENT = False
            query_str = message.content.lower()  # Get message in string

            # Parse request and plot
            if "report" in query_str:
                data = pd.read_csv(url_us_reports, error_bad_lines=False)  # Read in most recent daily report
                top_confirmed = data.nlargest(5, "Confirmed")
                top_deaths = data.nlargest(5, "Deaths")
                await mp.report(message=message, top_confirmed=top_confirmed, top_deaths=top_deaths)
                SENT = True

            elif "total" in query_str or "daily" in query_str:
                if "us" in query_str or "united states" in query_str:

                    # Read in data
                    data = pd.read_csv(url_us_cases_ts, error_bad_lines=False)
                    start_date, last_date = mp.get_start_end_dates(
                        data=data)  # First and last date containing case data

                    state_names = list(data["Province_State"])
                    states = []
                    for i in range(0, len(state_names)):
                        # Check for any matching state names from the message string
                        if (state_names[i] in query_str.title()) and (state_names[i] not in states):
                            states.append(state_names[i])

                    fig, ax = plt.subplots()  # Set up plot
                    states_summed = []  # Store summed states if multiple states are requested
                    for i in range(0, len(states)):
                        # Sum sub-region level data for the state
                        state_sum = mp.get_loc_data(name=states[i], start_date=start_date,
                                                    last_date=last_date, data=data)
                        states_summed.append(state_sum)

                        if "total" in query_str and len(states) == 1:
                            # Only one state plot requested, plot and send message.
                            mp.plot_total(data=data, location=state_sum, state=states[i],
                                          start_date=start_date, last_date=last_date, ax=ax)
                            mp.customize_plot(data=data, last_date=last_date,
                                              start_date=start_date, ax=ax)
                            await mp.send_total(data=data, location=state_sum, state=states[i],
                                                start_date=start_date, message=message)
                            SENT = True

                        elif "daily" in query_str:
                            # New plot for each region's daily results.
                            fig, ax = plt.subplots()
                            cases_ytdy, avg_ytdy, max_cases, max_ind = mp.plot_daily(data=data, location=state_sum,
                                                                                     state=states[i],
                                                                                     start_date=start_date,
                                                                                     last_date=last_date,
                                                                                     ax=ax)
                            mp.customize_plot(data=data, last_date=last_date,
                                              start_date=start_date, ax=ax)
                            await mp.send_daily(data=data, state=states[i], cases=cases_ytdy,
                                                avg=avg_ytdy, max_cases=max_cases, ind=max_ind,
                                                message=message)
                            SENT = True

                    if "total" in query_str and len(states) > 1:
                        # Different method call since multiple regions will be plotted on same plot
                        mp.plot_totals(data=data, locations=states_summed, states=states,
                                       start_date=start_date, last_date=last_date, ax=ax)
                        mp.customize_plot(data=data, last_date=last_date,
                                          start_date=start_date, ax=ax)
                        await mp.send_totals(locations=states_summed, states=states,
                                             message=message)
                        SENT = True

                    # Remove data from memory
                    del data
                    del states_summed
                    gc.collect()

            elif "help" in query_str:
                # Send help message
                await mp.send_help(message)
                SENT = True

            if not SENT:
                # Detect improper request formats and direct user to help
                print("IMPROPER REQUEST")
                async with message.channel.typing():
                    await message.channel.send(
                        "You have entered a request with an improper format. Type '~covid help' for "
                        "useage info.")

    client.run(TOKEN)  # Bot token is entered here


if __name__ == '__main__':
    main()
