from os import write
from typing import Any, Optional
import discord
from discord.ext import tasks, commands
import json
import asyncio
from datetime import date
from profanity_check import predict, predict_prob


config_file = open("./config.json", "r").read()
config = json.loads(config_file)

token = config["token"]
print(token)

intents = discord.Intents.all()
intents.message_content = True

bot = commands.Bot(intents=intents, command_prefix="!")

# global online = False

@tasks.loop(hours=24) 
# @tasks.loop(seconds=10) 
async def QOTD_task():
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


@bot.command()
@commands.has_role("QOTD")
async def QOTD_start(ctx):
    # if online == True:
    #     return
    await QOTD_task.start()
    await ctx.send("QOTD system started. Do not run this command again")
    online = True


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


@bot.event 
async def on_message(message):
    prob = predict_prob([message.content]).max()
    deleted = False

    if prob > config["automod_limit"]:
        await message.delete()
        await message.channel.send(f"{message.author.mention}")
        await message.channel.send("https://tenor.com/view/captain-america-marvel-avengers-gif-14328153")
        deleted = True

    print(f"message: {message.content} \n prob_of_insult: {prob} \n deleted: {deleted}")
        

    
@bot.event 
async def on_start():
    print("starting QOTD")
    await QOTD_task.start()

bot.run(token)

