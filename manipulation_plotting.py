# Author: Joseph Savage
# Date: July 29, 2020
# Mini-library of functions for plotting and message sending.

import datetime as dt
from textwrap import wrap
import numpy as np
import matplotlib.pyplot as plt
import discord


def get_start_end_dates(data):
    """Finds the first and last dates of available data in mm/dd/yy format"""
    start_date = data.filter(regex='\\d+/\\d+/\\d\\d', axis="columns").columns[0]
    last_date = dt.datetime.strptime(data.columns[-1], '%m/%d/%y').strftime(
        '%m/%#d/%y').lstrip("0").replace(" 0", " ")
    return start_date, last_date


def get_loc_data(name, start_date, last_date, data):
    """Finds province/state location data and sums columns for that location,
    returning an array of length start_date:last_date"""
    loc_rows = data.index[data['Province_State'] == name].tolist()
    loc_sum = data.loc[loc_rows, start_date:last_date].sum(axis=0)
    return loc_sum


def plot_total(data, location, state, start_date, last_date, ax, stat):
    """Plots total cases for a single region"""
    ax.plot(data.columns[data.columns.get_loc(start_date):(data.columns.get_loc(last_date) + 1)],
            location,
            color="red")
    title = "Total Reported COVID-19 %s for %s \nsince the first US case" % (stat, state.title())
    ax.set(title=title.title(),
           xlabel="Date",
           ylabel="Total %s" % stat.title())


def plot_totals(data, locations, states, start_date, last_date, ax, stat):
    """Plots total cases for multiple regions"""
    evenly_spaced_interval = np.linspace(0, 1, len(states))  # For color map
    colors = [plt.cm.get_cmap("tab20")(x) for x in evenly_spaced_interval]
    for i in range(0, len(states)):
        ax.plot(data.columns[data.columns.get_loc(start_date):(data.columns.get_loc(last_date) + 1)],
                locations[i],
                color=colors[i],
                label=states[i])
    states_names = ""
    for i in range(0, len(states) - 1):
        states_names += states[i] + ", "
    states_names += "and " + states[-1]
    title = "Total Reported Covid %s for %s since the first US case" % (stat, states_names)
    ax.set(title="\n".join(wrap(title.title(), 60)),
           xlabel="Date",
           ylabel="Total %s" % stat.title())
    plt.legend()


def plot_daily(data, location, state, start_date, last_date, ax, stat):
    """Plots daily cases for a region"""
    daily = np.array(location)  # numpy.append(0, state_sum)
    daily = np.append(location[0], np.subtract(daily[1:(len(location))], daily[0:(len(location) - 1)]))
    ax.bar(data.columns[data.columns.get_loc(start_date):(data.columns.get_loc(last_date) + 1)],
           daily,
           color="lightblue",
           edgecolor="black",
           linewidth=0.5)

    # Calculate rolling average of last 7 days worth of cases.
    rolling_avg = [0] * len(daily)
    daily = np.append([0] * 6, daily)
    for i in range(0, len(rolling_avg)):
        rolling_avg[i] = np.mean(daily[i:(i + 6)])

    # Plot average data
    ax.plot(data.columns[data.columns.get_loc(start_date):(data.columns.get_loc(last_date) + 1)],
            rolling_avg,
            color="red")
    title = "Daily Reported Covid %s for %s \nsince the first US case" % (stat, state.title())
    ax.set(title=title.title(),
           xlabel="Date",
           ylabel="Number of %s" % stat)

    return daily[-1], rolling_avg[-1], np.max(daily), np.where(daily == np.max(daily))[0][0]


def customize_plot(data, last_date, start_date, ax):
    """Sets standard plot design"""
    plt.setp(ax.get_xticklabels(), rotation=45)
    start = 0
    end = data.columns.get_loc(last_date) - data.columns.get_loc(start_date)
    ax.xaxis.set_ticks(np.append(np.arange(start, end, 28), end))
    date_labels = data.filter(regex='\\d+/\\d+/\\d\\d', axis="columns").columns[
        np.append(np.arange(start, end, 28), end)]
    date_labels = [
        dt.datetime.strptime(date, '%m/%d/%y').strftime('%b %d, %y').lstrip("0").replace(" 0", " ")
        for date in date_labels]
    ax.set_xticklabels(date_labels)
    plt.xticks(fontsize=7.5)
    ax.set_ylim(ymin=0)
    ax.set_xlim(xmin=0, xmax=end + 5)
    plt.tight_layout()
    plt.savefig("covid_plot.png")
    plt.close()


async def send_total(data, location, state, start_date, message, stat):
    """Sends message with plot of total cases for a single region"""
    start_ind = data.columns.get_loc(start_date)
    first_date = str(dt.datetime.strptime(data.columns[start_ind:][np.argmax(location > 0)], '%m/%d/%y').strftime(
        '%b %d, %Y').lstrip("0").replace(" 0", " "))
    async with message.channel.typing():
        await message.channel.send("%s has reached %s %s since the first recorded %s there on %s."
                                   % (state.title(),
                                      f"{location[-1]:,d}",
                                      stat,
                                      stat[:len(stat)-1],
                                      first_date),
                                   file=discord.File("covid_plot.png"))


async def send_totals(locations, states, message, stat):
    """Sends message with plot of total cases for multiple regions"""
    response = """Since the first recorded %s in the United States: \n""" % stat[:len(stat) - 1]
    for i in range(0, len(states) - 1):
        response += "%s has reached %s %s\n" % (states[i],
                                                   f"{locations[i][-1]:,d}",
                                                stat.title())
    response += "%s has reached %s %s\n" % (states[-1],
                                               f"{locations[-1][-1]:,d}",
                                            stat.title())
    async with message.channel.typing():
        await message.channel.send(response,
                                   file=discord.File("covid_plot.png"))


async def send_daily(data, state, cases, avg, max_cases, ind, message, stat):
    """Sends message for plot of daily cases"""
    async with message.channel.typing():
        await message.channel.send(
            "%s had %s new %s yesterday. The 7-day average number of new %s is %s. \nThe max number of %s in "
            "a day was %s, on %s "
            % (state.title(),
               f"{cases:,d}",
               stat,
               stat,
               f"{avg:,.0f}",
               stat,
               f"{max_cases:,d}",
               str(dt.datetime.strptime(data.columns[ind + 11 - 6], '%m/%d/%y').strftime('%b %d, %Y').lstrip(
                   "0").replace(" 0", " "))),
            file=discord.File("covid_plot.png"))


async def report(message, top_confirmed, top_deaths):
    """Sends a report of the top worst states by cases and deaths"""
    async with message.channel.typing():
        cases_str = """The top 5 worst US states/territories by confirmed case count are:"""
        for i in range(0, 5):
            cases_str = cases_str + "\n     %s with %s confirmed cases" % (top_confirmed["Province_State"].iloc[i],
                                                                           f'{top_confirmed["Confirmed"].iloc[i]:,d}')
        deaths_str = """The top 5 worst US states/territories by death toll are:"""
        for i in range(0, 5):
            deaths_str = deaths_str + "\n     %s with %s deaths" % (top_deaths["Province_State"].iloc[i],
                                                                    f'{top_deaths["Deaths"].iloc[i]:,d}')

        await message.channel.send(cases_str)
        await message.channel.send(deaths_str)


async def send_help(message):
    """Sends help information to the user"""
    async with message.channel.typing():
        await message.channel.send("""COVID-19 Visualizer currently produces plots of daily and """
                                   "total case counts for US states and territories, as well as reporting "
                                   "which states are doing the worst. "
                                   "\n\nUSAGE:"
                                   "\nTo request information from the bot, type '~covid' at the beginning of "
                                   "your message. "
                                   "\nFor a plot of daily cases, type 'daily' after this"
                                   "\nFor US cases, type 'US' in your message."
                                   "\nFor states, type as many state names as you wish in any order and wait "
                                   "for the results to appear. "
                                   "\nExample: \n~covid total US New Hampshire Vermont"
                                   "\n\nFor a report of the top worst states by total cases and death toll, "
                                   "type '~covid report'")
