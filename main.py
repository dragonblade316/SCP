from os import walk, write
from typing import Any, Optional
import discord
from discord.ext import tasks, commands
import json
import asyncio
from datetime import date
from datetime import time

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler

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


#<QOTD>
async def QOTD_post():
    print(f"QOTD channel id: {config["QOTD_id"]}")

    channel = bot.get_channel(int(config["QOTD_id"]))

    print(type(channel))

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

@tasks.loop(time=time(hour=12, minute=0))
async def qotd_task():
    await QOTD_post()


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
# </QOTD>


#matnence
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
    await ctx.respond("rolling d20")
    await ctx.send(random.randint(1,20))


#<cpp enforcement>
connections = {}

async def once_done(sink: discord.sinks, channel: discord.TextChannel, *args):  # Our voice client already passes these in.


    recorded_users = [  # A list of recorded users
        f"<@{user_id}>"
        for user_id, audio in sink.audio_data.items()
    ]
    
    await sink.vc.disconnect()  # Disconnect from the voice channel.
    files = [discord.File(audio.file, f"{user_id.encoding}") for user_id, audio in sink.audio_data.items()]  # List down the files.
    
    await channel.send(f"finished recording audio for: {', '.join(recorded_users)}.", files=files)  # Send a message with the accumulated files.

    await channel.send("test complete")

    
@bot.command()
async def record(ctx):  # If you're using commands.Bot, this will also work.
    voice = ctx.author.voice

    # if not voice:
    #     await ctx.respond("You aren't in a voice channel!")
    #
    vc = await voice.channel.connect()  # Connect to the voice channel the author is in.
    connections.update({ctx.guild.id: vc})  # Updating the cache with the guild and channel.

    vc.start_recording(
        discord.sinks.MP3Sink(),  # The sink type to use.
        once_done,  # What to do once done.
        ctx.channel  # The channel to disconnect from.
    )
    await ctx.send("Started recording!")

@bot.command()
async def stop_recording(ctx):
    if ctx.guild.id in connections:  # Check if the guild is in the cache.
        vc = connections[ctx.guild.id]
        vc.stop_recording()  # Stop recording, and call the callback (once_done).
        del connections[ctx.guild.id]  # Remove the guild from the cache.
        # await ctx.delete()  # And delete.
    else:
        await ctx.respond("I am currently not recording here.")  # Respond with this if we aren't recording.
        

#</cpp enforcement>

#<events>
# @bot.event
# async def on_voice_state_update(member, before, after):
#     if before.channel is None and after.channel:
#        # User has connected to a VoiceChannel
#        channel = after.channel
#        # Code here...
#
#</events>

@bot.listen(once=True)
async def on_ready():
    qotd_task.start()

# async def main():
#     scheduler = AsyncIOScheduler()
#     #
#     # #utc
#     # scheduler.add_job(QOTD_post, 'cron', hour=14, minute=0)
#     # scheduler.start()
#     await bot.start(token)
#
# asyncio.run(main())

bot.run(token)
