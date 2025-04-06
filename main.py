from os import write
from typing import Any, Optional
import discord
from discord.ext import tasks, commands
import json
import asyncio
from datetime import date

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from profanity_check import predict, predict_prob
from better_profanity import profanity

import subprocess

# subprocess.run(["ls", "-l"]) 



config_file = open("./config.json", "r").read()
config = json.loads(config_file)

token = config["token"]
print(token)

intents = discord.Intents.all()
intents.message_content = True

bot = commands.Bot(intents=intents, command_prefix="!")

# global online = False


async def log(message):
    channel = bot.get_channel(int(config["log_id"]))

    if type(channel) != discord.channel.TextChannel:
        print("wrong channel or channel not found")
        print(type(channel))
        return 

    await channel.send(message)

@tasks.loop(hours=24) 
async def QOTD_task():
    await QOTD_post()

async def QOTD_post():
    print(f"QOTD channel id: {config["QOTD_id"]}")

    channel = bot.get_channel(int(config["QOTD_id"]))

    if type(channel) != discord.channel.ForumChannel:
        print("wrong channel or channel not found")
        print(type(channel))
        return 
    try:
        data = json.loads(open("./QOTD.json", "r").read())
        
        if len(data["questions"]) is 0:
            print("out of questions")
            return

        question = data["questions"].pop(0)
        if question == None:
            return
       
        print(data)
        open("./QOTD.json", 'w+').write(json.dumps(data))
        
        
        #ignore this error, there is no situation which it is triggered during runtime.
        await channel.create_thread(name=f"QOTD: {date.today()}", content=str(question)) 
        

    except Exception as e:
        print(e)

#
# @bot.command()
# @commands.has_role("QOTD")
# async def QOTD_start(ctx):
#     # if online == True:
#     #     return
#     await QOTD_task.start()
#     await ctx.send("QOTD system started. Do not run this command again")
#     online = True

@bot.command()
async def QOTD(ctx):
    await QOTD_post()

@bot.command()
@commands.has_role("QOTD")
async def QOTD_add(ctx, question: str):
    ctx.author

    try:
        expression = json.loads(open("./QOTD.json", "r+").read())
    except FileNotFoundError:
        open("./QOTD.json", "x")
        expression = {"questions": [""]}

            

    #cheesing the interpruter a bit here. dont change    
    if "questions" not in expression.keys() or type(expression["questions"]) != list:
        expression["questions"] = []

    expression["questions"].append(question)
    print(f"expression: {expression}")

    j = json.dumps(expression)
    print(j)
    
    await ctx.send(f"Added question: {question} to the queue")

    open("./QOTD.json", "w").write(j)

@bot.command()
@commands.has_role("QOTD")
async def QOTD_list(ctx):
    questions = json.loads(open("./QOTD.json", "r+").read())["questions"]

    final = f"There are {len(questions)} questions in queue. \n\n"
    num = 0

    for i in questions:
        final += f"{num}: {i}\n"
        num += 1
        
    await ctx.send(final)


@bot.command()
@commands.has_role("Commander")
async def blacklist(ctx, blacklisted_word):
    print("blacklisted")

    #lowercase appears to be needed
    blacklisted_word = blacklisted_word.lower()
    profanity.add_censor_words([blacklisted_word])
    config["blacklisted_words"].append(blacklisted_word)
    

    config_file_w = open("./config.json", "w")
    config_file_w.write(json.dumps(config))
    config_file_w.close()

    await ctx.send("blacklisted")

@bot.command()
@commands.has_role("Commander")
async def whitelist(ctx, whitelisted_word):
    print("whitelisted")

    #lowercase appears to be needed
    whitelisted_word = whitelisted_word.lower() 
    config["whitelisted_words"].append(whitelisted_word)
    profanity.load_censor_words(whitelist_words=config["whitelisted_words"])
    
    config_file_w = open("./config.json", "w")
    config_file_w.write(json.dumps(config))
    config_file_w.close()

    await ctx.send("whitelisted")

@bot.command()
@commands.has_role("Commander")
async def filter(ctx):
    filter = not filter
    await ctx.send(f"filter status: {filter}")

@bot.command()
@commands.has_role("Bot Lord")
async def update(ctx):
    await ctx.send("starting update")
    subprocess.run(["git", "pull"])
    await ctx.send("update complete, restarting")
    subprocess.run(["systemctl", "restart", "--user", "SCP.service"])

@bot.command()
async def lol(ctx):
    await ctx.send("lol")

@bot.command()
async def roll(ctx):
    import random
    await ctx.send("rolling d20")
    await ctx.send(random.randint(1,20))


@bot.event 
async def on_message(message):
    await bot.process_commands(message)

    # if (filter == False):
    #     return
    #
    # if message.author.id == 864917095077511178:
    #     return
    #
    # deleted = False
    #
    # async def censor():
    #     if deleted:
    #         return
    #
    #     await message.delete()
    #     await message.channel.send(f"{message.author.mention}")
    #     await message.channel.send("https://tenor.com/view/captain-america-marvel-avengers-gif-14328153")
    #
    # if profanity.contains_profanity(message.content):
    #     await censor()
    #     deleted = True
    #     await log(f"message: ||{message.content}|| \n Deleted by word filter \n deleted: {deleted}")
    #     print(f"message: {message.content} \n Deleted by word filter \n deleted: {deleted}")
    #     return
    #
    # prob = predict_prob([message.content]).max()
    #
    # # if prob > config["automod_limit"]:
    # #     await censor()
    # #     deleted = True
    # #     await log(f"message: ||{message.content}|| \n prob_of_insult: {prob} \n deleted: {deleted}")
    #
    # print(f"message: {message.content} \n prob_of_insult: {prob} \n deleted: {deleted}")
    #


async def main():
    scheduler = AsyncIOScheduler()
    #utc
    scheduler.add_job(QOTD_post, 'cron', hour=14, minute=0)
    scheduler.start()

    profanity.load_censor_words(config["blacklisted_words"], whitelist_words=config["whitelisted_words"])
    await bot.start(token)

asyncio.run(main())

