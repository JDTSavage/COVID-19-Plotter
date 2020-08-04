# COVID-19 Visualizer

A discord bot that provides plots and reports of COVID-19 data.

### Dependencies:
discord.py, pandas, numpy, matplotlib

### Setup: 

Clone this repository.
After creating a bot account on the Discord developer portal, 
take the bot token and put it in *env.txt* immediately after 
"=" in the line "DISCORD_TOKEN=". Rename *env.txt* to *.env*.

Run *bot.py* to start the bot. After inviting the bot to your server, 
you can communicate with the bot as follows:

Beginning a message with *~covid* indicates that the message
contains a command for the bot.

- For help, type *help* next.
- For a *report*, type report.
- For a total plot, type *total* in the message.
- For a daily plot, type *daily*
- If you wish to see data on deaths instead of confirmed cases, type *deaths*
- Type the name of the country you wish to see results for.
- To see state level data for the United States of America, type up to 10 state names at the end of the message.

Example: ~covid total US Oregon Maine Florida

NOTE: I am lazy and have not put global data in yet, curently the only supported plots are of US states. Type ~covid total/daily US [STATE NAME(s)] 
to get plots of states. Global data coming soon (which will allow for plots of entire countries, including the US.)

Covid reports are also quite ugly currently, but this is under development.

### Data sources:

The data used to produce these plots is provided to the public by Johns Hopkins University through
the COVID-19 Data Repository by the Center for Systems Science
and Engineering (CSSE) at Johns Hopkins University
which can be acessed at:

https://github.com/CSSEGISandData/COVID-19

