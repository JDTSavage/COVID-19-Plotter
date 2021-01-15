# Author: Joseph Savage
# Date: July 29, 2020
# Mini-library of functions for plotting and message sending.

import datetime as dt
from textwrap import wrap
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import discord
import asyncio


def get_start_end_dates(data):
    """Finds the first and last dates of available data in mm/dd/yy format"""
    start_date = data.filter(regex='\\d+/\\d+/\\d\\d', axis="columns").columns[0]
    last_date = dt.datetime.strptime(data.columns[-1], '%m/%d/%y').strftime(
        '%m/%#d/%y').lstrip("0").replace(" 0", " ")
    start_ind = data.columns.get_loc(start_date)
    return start_date, last_date, start_ind


def get_loc_data(name, start_date, last_date, data, colname):
    """Finds province/state location data and sums columns for that location,
    returning an array of length start_date:last_date"""
    loc_rows = data.index[data[colname] == name].tolist()
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
           color="darkgreen",
           edgecolor="black",
           linewidth=0.0,
           width=0.6,
           align='center')

    # Calculate rolling average of last 7 days worth of cases.
    rolling_avg = [0] * len(daily)
    daily = np.append([0] * 6, daily)
    for i in range(0, len(rolling_avg)):
        rolling_avg[i] = np.mean(daily[i:(i + 7)])

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
    trash_idxs = data.columns.size - end - 1
    date_labels = data.filter(regex='\\d+/1/\\d\\d', axis="columns").columns

    date_labels = np.insert(date_labels, 0, start_date)
    date_labels = np.append(date_labels, last_date)

    date_idxs = np.where(np.isin(np.array(data.columns), np.array(date_labels)) == True)[0] - trash_idxs
    date_labels = [
        dt.datetime.strptime(date, '%m/%d/%y').strftime('%b %d, %y').lstrip("0").replace(" 0", " ")
        for date in date_labels]

    if date_idxs[1] < 14:
        date_labels = np.delete(date_labels, 1)
        date_idxs = np.delete(date_idxs, 1)
    if (date_idxs[-1] - date_idxs[-2] < 14):
        date_labels = np.delete(date_labels, -2)
        date_idxs = np.delete(date_idxs, -2)

    ax.xaxis.set_ticks(date_idxs) # np.append(date_idxs, end))
    ax.set_xticklabels(date_labels)
    plt.xticks(fontsize=7.5)
    ax.set_ylim(ymin=0)
    ax.set_xlim(xmin=0, xmax=end + 5)
    plt.tight_layout()
    plt.savefig("covid_plot.png")
    plt.close()


def data_clean(lst):
    """Cleans up JHU data for confusing region names
    Affected region names: US, 'Korea, South'"""
    if "Korea, South" in lst:
        index = lst.index("Korea, South")
        lst[index] = "South Korea"
    if "US" in lst:
        index = lst.index("US")
        lst[index] = "The United States"


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
                                      stat[:len(stat) - 1],
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


async def send_daily(data, state, cases, avg, max_cases, ind, message, stat, start_ind):
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
               str(dt.datetime.strptime(data.columns[ind + start_ind - 6], '%m/%d/%y').strftime('%b %d, %Y').lstrip(
                   "0").replace(" 0", " "))),
            file=discord.File("covid_plot.png"))


async def report(message, url, glob, client):
    """Sends a report of the top worst states by cases and deaths"""
    reactions = np.array(['\u0031\u20E3', '\u0032\u20E3', '\u0033\u20E3', '\u0034\u20E3', '\u0035\u20E3', '\u0036\u20E3'])
    stats_dict = {
        '\u0031\u20E3' : 'Confirmed',
        '\u0032\u20E3' : "Deaths",
        '\u0033\u20E3' : "Case/Fatality Ratio",
        '\u0034\u20E3' : "Recovered",
        '\u0035\u20E3' : "Active",
        '\u0036\u20E3' : "Total_Test_Results"
    }
    stats_formatted = {
        'Confirmed' : 'Confirmed Cases',
        "Deaths" : 'Confirmed Deaths',
        "Case/Fatality Ratio" : "Case Fatality Ratio",
        "Recovered" : "Recovered Cases",
        "Active" : "Active Cases",
        "Total_Test_Results" : "Total Tests"
    }

    try:
        if glob:
            embed = discord.Embed(
                title="Choose a statistic to report".title(),
                colour=discord.Colour.blue(),
                description="""%s **Confirmed cases**"""
                            "\n%s **Confirmed Deaths**"
                            "\n%s **Case/Fatality Ratio**"
                            "\n%s **Recovered Cases**"
                            "\n%s **Active Cases**" % (reactions[0], reactions[1], reactions[2], reactions[3],
                                                       reactions[4])
            )

            async with message.channel.typing():
                auth = message.author
                msg = await message.channel.send("**Global Statistics**", embed=embed)
                for emoji in reactions:
                    await msg.add_reaction(emoji)

            reaction, user = await client.wait_for('reaction_add', timeout=60, check=lambda r, u: u == auth and
                                                                                                  r.message.id == msg.id and r.emoji in reactions)
            stat_column = stats_dict[reaction.emoji]
            data = pd.read_csv(url, error_bad_lines=False)

            data = data.groupby('Country_Region')[['Confirmed','Deaths', 'Recovered','Active']].sum().reset_index()
            case_fatality = data["Deaths"]/data['Confirmed']
            data['Case/Fatality Ratio'] = case_fatality
            stats = data.nlargest(n=5, columns=stat_column)
            low_stats = data.nsmallest(n=5, columns=stat_column)

            async with message.channel.typing():
                str = "Ranked by %s, the 5 countries with the highest statistic for this are:" % stats_formatted[stat_column]
                for row in range(stats.shape[0]):
                    nstr = "\n%s with %s" % (np.array(stats['Country_Region'])[row], f"{np.array(stats[stat_column])[row]:,.1f}")
                    str = str + nstr
                str = str + "\n\nThe 5 countries with the lowest statistic for this are:"
                for row in range(stats.shape[0]):
                    nstr = "\n%s with %s" % (np.array(low_stats['Country_Region'])[row], f"{np.array(low_stats[stat_column])[row]:,.1f}")
                    str = str + nstr

                embed = discord.Embed(
                    title="Worst and Best Countries, by %s" % stats_formatted[stat_column],
                    colour=discord.Colour.blue(),
                    description=str
                )
                await message.channel.send(embed=embed)

        else:
            embed = discord.Embed(
                title="Choose a statistic to report".title(),
                colour=discord.Colour.blue(),
                description="""%s **Confirmed cases**"""
                            "\n%s **Confirmed Deaths**"
                            "\n%s **Case/Fatality Ratio**"
                            "\n%s **Recovered Cases**"
                            "\n%s **Active Cases**" 
                            "\n%s **Total Tests**" % (reactions[0], reactions[1], reactions[2], reactions[3],
                                                       reactions[4], reactions[5])
            )

            async with message.channel.typing():
                auth = message.author
                msg = await message.channel.send("**Global Statistics**", embed=embed)
                for emoji in reactions:
                    await msg.add_reaction(emoji)

            reaction, user = await client.wait_for('reaction_add', timeout=60, check=lambda r, u: u == auth and
                                                                                                  r.message.id == msg.id and r.emoji in reactions)
            stat_column = stats_dict[reaction.emoji]
            data = pd.read_csv(url, error_bad_lines=False)

            data = data.groupby('Province_State')[['Confirmed', 'Deaths', 'Recovered', 'Active', 'Total_Test_Results']].sum().reset_index()
            case_fatality = data["Deaths"] / data['Confirmed']
            data['Case/Fatality Ratio'] = case_fatality
            stats = data.nlargest(n=5, columns=stat_column)
            low_stats = data.nsmallest(n=5, columns=stat_column)

            async with message.channel.typing():
                str = "Ranked by %s, the 5 countries with the highest statistic for this are:" % stats_formatted[stat_column]
                for row in range(stats.shape[0]):
                    nstr = "\n%s with %s" % (np.array(stats['Province_State'])[row], f"{np.array(stats[stat_column])[row]:,.1f}")
                    str = str + nstr
                str = str + "\n\nThe 5 countries with the lowest statistic for this are:"
                for row in range(stats.shape[0]):
                    nstr = "\n%s with %s" % (np.array(low_stats['Province_State'])[row], f"{np.array(low_stats[stat_column])[row]:,.1f}")
                    str = str + nstr

                embed = discord.Embed(
                    title="Worst and Best Countries, by %s" % stats_formatted[stat_column],
                    colour=discord.Colour.blue(),
                    description=str
                )
                await message.channel.send(embed=embed)

    except asyncio.TimeoutError:
        async with message.channel.typing():
            await message.channel.send("You didn't pick an option.")

    return True

async def send_help(message):
    """Sends help information to the user"""
    msg = """COVID-19 Visualizer currently produces plots of daily and """ \
          "total case and death counts for countries and US states and territories, as well as " \
          "which US states are doing the worst. " \
          "\n\nUSAGE:" \
          "\nTo request information from the bot, type *~covid* at the beginning of " \
          "your message. " \
          "\nFor a plot of daily cases, type *daily* after this" \
          "\nType the name of the country you wish to see data for" \
          "\nFor US states, type states and as many state names as you wish" \
          "\nExample: \n*~covid total states New Hampshire Vermont*" \
          "\n*~covid daily Zimbabwe*" \
          "\n\nFor a report of the top worst states by total cases and death toll, " \
          "type *~covid report*" \
          "\nTo see supported locations, type *~covid locations* and follow the prompts in " \
          "your DMs"
    async with message.author.typing():
        embed = discord.Embed(
            title="COVID-19 Visualizer Help",
            colour=discord.Colour.blue(),
            description=msg
        )
        await message.author.send(embed=embed)


async def request_locs(message):
    locs = []
    msg = ""
    msg_cont = ""
    msg_title = ""
    if "countries" in message.content.lower():
        url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data" \
              "/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv"
        data = pd.read_csv(url, error_bad_lines=False)
        locs = np.sort(pd.unique(data["Country/Region"]))
        del data
        msg_title = "Supported Countries/Regions"
    elif "states" in message.content.lower():
        url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data" \
              "/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv"
        data = pd.read_csv(url, error_bad_lines=False)
        locs = np.sort(pd.unique(data["Province_State"]))
        del data
        msg_title = "Supported States/Territories"
    else:
        async with message.author.typing():
            await message.author.send("Invalid response. Try again.")

    i = 0
    while len(msg + locs[i + 1]) < 2000 and i < len(locs) - 2:
        msg += locs[i] + ", "
        i += 1
    if i < len(msg) - 1:
        while len(msg_cont + locs[i + 1]) < 2000 and i < len(locs) - 2:
            msg_cont += locs[i] + ", "
            i += 1
    if len(msg + locs[-1]) < 2000:
        msg += locs[-1]
        i += 1
    else:
        msg_cont += locs[-1]

    async with message.author.typing():
        embed = discord.Embed(
            title=msg_title,
            colour=discord.Colour.blue(),
            description=msg + " " + msg_cont
        )
        await message.author.send(embed=embed)

    return True
