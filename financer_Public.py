from discord.ext import commands, tasks
import discord
import os
from datetime import date
from datetime import datetime
import sqlite3
import calendar


# Connect Database

con = sqlite3.connect("finance.db")
cur = con.cursor()

# Validate Bot and Connect Channel

BOT_TOKEN = "Token Here"
# Channel ID here
CHANNEL_ID = 0000

# Main user for personal adjustments
ADMIN_KEY = 00000

# Enable Bot Messaging

intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix="$", intents=intents)

@tasks.loop(hours=24)
async def daily_check():
    channel = bot.get_channel(CHANNEL_ID)
    now = datetime.now()
    
    # Get current month and year
    current_month = date.today().month
    current_year = date.today().year

    # Find last day of the month
    month = calendar.monthrange(current_year, current_month)

    if now.day == month[1]:
        if channel:
            total = get_month_total()
            await channel.send(f"This months total spending is {total}!!")
        else:
            print("error")

@bot.event
async def on_ready():
    print("Hello!")
    channel = bot.get_channel(CHANNEL_ID)
    await channel.send(":3")
    daily_check.start()


# Contains Adding purchase to database, Returning the new total and transaction ID, Changing the channel topic, Checking a 1k milestone

@bot.command()
async def add(ctx, amount: str = None):
    amount = amount
    if ctx.channel.id == CHANNEL_ID:


        if amount is None:
            await ctx.send("Please provide a number")
            return
        
        try:
            amount = int(amount)
            if amount <= 0:
                await ctx.send("The amount must be a positive number")
                return
            
            if amount > 100000:
                await ctx.send("No")
                return
            
        except ValueError:
            await ctx.send("Your format should be $add NUMBER HERE then text here if you want")
            return

        user_id = ctx.author.id
        current_date = date.today()

        try:
            # Add to DB
            cur.execute("INSERT INTO finance (DiscordId, Date, Amount) VALUES (?, ?, ?)", (user_id, current_date, amount))
            con.commit()
            # Get Data to spit out
            month = get_month_total()
            grand = get_grand_total()
            milestone = check_milestone()
            transaction_id = new_id()
            # Change Channel topic
            channel = bot.get_channel(CHANNEL_ID)
            if channel:
                try:
                    await channel.edit(topic=(month))
                except Exception as e:
                    print("error {e}")
            else:
                print("no channel found")
            # Milestone Update
            if int(grand / 1000) > int(milestone):
                update_milestone(int(grand / 1000))
                await ctx.send(f"WE BROKE {int(grand / 1000)}k!!!")

            await ctx.send(f"PM Total this month: {month}\nGrand Total: {grand}\nTransaction ID: {transaction_id}")
        except Exception as e:
            print(f"An error occurred: {e}")

# Allows refunding of transactions

@bot.command()
async def refund(ctx, transaction: str = None):
    if ctx.channel.id == CHANNEL_ID:
        transaction = transaction
        if transaction is None:
            await ctx.send("Please provide an ID, it will be a number")
            return
        
        try:
            transaction = int(transaction)
            if transaction <= 0:
                await ctx.send("The amount must be a positive number. DON'T TEST ME ILL SNAP ILL DO IT ILL SNAP.")
                return
        except ValueError:
            await ctx.send("Your format should be something like $refund TRANSACTION ID HERE THIS IS WHY I GIVE YOU AN ID ITS FOR THIS then text after if you want idc")
            return
        user_id = ctx.author.id
        try:
            cur.execute("SELECT DiscordID FROM finance WHERE transactionID = (?)", (transaction,))
            result = cur.fetchone()
            if result is None:
                await ctx.send("Transaction ID is not found ;-;")
                return
            if user_id == result or user_id == ADMIN_KEY:
                cur.execute("DELETE FROM finance WHERE transactionID = (?)", (transaction,))
                con.commit()
                await ctx.send("You have been refunded!")
                    # Change Channel topic
                channel = bot.get_channel(CHANNEL_ID)
                if channel:
                    month = get_month_total()
                    try:
                        await channel.edit(topic=(month))
                    except Exception as e:
                        print("error {e}")
                else:
                    print("no channel found")
                    return
            else:
                await ctx.send("You are simply a bystander in this transaction you cannot taint it")
                return
        except Exception as e:
            print(f"An error occured: {e}")
            

# Checks inputed users totals

@bot.command()
async def check(ctx, member: discord.Member = None):

    if ctx.channel.id == CHANNEL_ID:

        if member is None:
            month = get_month_total()
            grand = get_grand_total()
            await ctx.send(f"PM Total this month: {month}\nGrand Total: {grand}")
            

        else:
            if isinstance(member, discord.Member):
                try:
                    user_id = member.id
                    username = member.name
                    month = get_user_month(user_id)
                    grand = get_user_total(user_id)
                    await ctx.send(f"{username} Spendage this month: {month}\nGrand Total: {grand}")
                except Exception as e:
                    print(f"Error: {e}")
            else:
                print("Invalid User")

## At the end of the month give total

def get_first_day():

    # Get current month and year
    current_month = date.today().month
    current_year = date.today().year

    # Format Date
    x = str(current_year) + '-' + str(current_month) + '-01'
    z = datetime.strptime(x, '%Y-%m-%d').date()

    return(z)

def get_last_day():
     # Get current month and year
    current_month = date.today().month
    current_year = date.today().year

    # Find last day of the month
    month = calendar.monthrange(current_year, current_month)

    # Format date
    x = str(current_year) + '-' + str(current_month) + '-' + str(month[1])
    z = datetime.strptime(x, '%Y-%m-%d').date()

    return(z)

def get_month_total():

    # Grab variables
    start = get_first_day()
    end = get_last_day()

    # Find total
    try:
        cur.execute("SELECT SUM(AMOUNT) FROM FINANCE WHERE DATE BETWEEN ? AND ?", (start, end))
        result = cur.fetchone()
    except Exception as e:
        print(f"An error occurred: {e}")
    
    return(result[0])

def get_grand_total():

    try:
        cur.execute("SELECT SUM(AMOUNT) FROM FINANCE")
        result = cur.fetchone()
    except Exception as e:
        print(f"An error occurred: {e}")

    return(result[0])

def get_user_month(user_id):

     # Grab variables
    user_id = user_id   
    start = get_first_day()
    end = get_last_day()
    try:
        cur.execute("SELECT SUM(AMOUNT) FROM FINANCE WHERE DiscordId = ? AND DATE BETWEEN ? AND ?", (user_id, start, end))
        result = cur.fetchone()
    except Exception as e:
        print(f"An error occurred: {e}")

    return(result[0])

def get_user_total(user_id):

    # Grab Id
    x = user_id
    try:
        cur.execute("SELECT SUM(AMOUNT) FROM FINANCE WHERE DiscordId = " + str(x))
        result = cur.fetchone()
        total = result[0] if result[0] is not None else 0
    except Exception as e:
        print(f"An error occurred: {e}")
        total = 0

    return total

def check_milestone():
    try:
        cur.execute("SELECT MAX(number) FROM MILESTONE")
        result = cur.fetchone()
    except Exception as e:
        print(f"An error occurred: {e}")
    
    return(result[0])

def update_milestone(milestone):
    x = milestone
    print(f"x = {x}")
    try:
        cur.execute("INSERT INTO MILESTONE (number) VALUES (?)", (x,))
        con.commit()
    except Exception as e:
        print(f"An error occurred: {e}")

# Returns highest transaction ID
def new_id():
    try:
        cur.execute("SELECT MAX(transactionID) FROM finance")
        result = cur.fetchone()
    except Exception as e:
        print(f"An error occurred: {e}")
        result = 0
    
    return(result[0])


bot.run(BOT_TOKEN)
con.close()


