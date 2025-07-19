import datetime
import math
from os import walk, write
from typing import Any, Optional
import discord
from discord.ext import tasks, commands
import json
import asyncio
from datetime import date
from datetime import time

import subprocess

from discord.types.channel import Channel

# subprocess.run(["ls", "-l"]) 


config_file = open("./config.json", "r").read()
config = json.loads(config_file)

format_string = "%Y-%m-%d %H:%M:%S"

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

def write_to_config():
    j = json.dumps(config)
    open("./QOTD.json", "w").write(j)

# def reload_config():
    # config = json.loads(open("./QOTD.json", "r+").read())

#<QOTD>
async def qotd_post():
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
    await qotd_post()


@bot.slash_command(descrpition="Instantanly triggers the next qotd")
@commands.has_role("QOTD")
async def qotd(ctx):
    await qotd_post()
    await ctx.respond("done")

@bot.slash_command(description="Adds a question to queue")
@commands.has_role("QOTD")
async def qotd_add(ctx, question: str):
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

    open("./QOTD.json", "w").write(j)
    
    await ctx.respond(f"Added question: '{question}' to the queue")

@bot.slash_command(description="Remove a question to queue")
@commands.has_role("QOTD")
async def qotd_remove(ctx, index: int):
    ctx.author

    try:
        expression = json.loads(open("./QOTD.json", "r+").read())
    except FileNotFoundError:
        open("./QOTD.json", "x")
        expression = {"questions": [""]}

            

    #cheesing the interpruter a bit here. dont change    
    if "questions" not in expression.keys() or type(expression["questions"]) != list:
        expression["questions"] = []

    try: 
        question = expression["questions"].pop(index)
    except IndexError as e:
        ctx.respond("index does not exist")
    print(f"expression: {expression}")

    j = json.dumps(expression)
    print(j)

    open("./QOTD.json", "w").write(j)
    
    await ctx.respond(f"Removed question: '{question}' from the queue")


@bot.slash_command(description="Moves a question to the front of the queue")
@commands.has_role("QOTD")
async def qotd_next(ctx, index: int):
    ctx.author

    try:
        expression = json.loads(open("./QOTD.json", "r+").read())
    except FileNotFoundError:
        open("./QOTD.json", "x")
        expression = {"questions": [""]}

            

    #cheesing the interpruter a bit here. dont change    
    if "questions" not in expression.keys() or type(expression["questions"]) != list:
        expression["questions"] = []

    try: 
        question = expression["questions"].pop(index)
        expression["questions"].insert(0, question)
    except IndexError as e:
        ctx.respond("index does not exist")

        
    print(f"expression: {expression}")

    j = json.dumps(expression)
    print(j)

    open("./QOTD.json", "w").write(j)
    
    await ctx.respond(f"Moved question: '{question}' to the front of the queue")


@bot.slash_command(description="Lists the questions in queue")
@commands.has_role("QOTD")
async def qotd_list(ctx):
    questions = json.loads(open("./QOTD.json", "r+").read())["questions"]

    final = f"There are {len(questions)} questions in queue. \n\n"
    num = 0

    for i in questions:
        final += f"{num}: {i}\n"
        num += 1
        
    await ctx.respond(final)
# </QOTD>


#<ocp>
def time_since_ocp():
    data = json.loads(open("./config.json", "r+").read())
    time = datetime.datetime.strptime(data["time_since_ocp"], format_string)

    return (datetime.datetime.now() - time)
    
@bot.slash_command(description="Use this command whenever ocp's are mentioned")
# @commands.has_role("QOTD")
async def ocp_mentioned(ctx):
    since = time_since_ocp()

    # await ctx.respond(f"It has been {since.days} days and {round((since.seconds / 3600) - (since.days * 24))} hours since ocps have been mentioned.")
    data = json.loads(open("./config.json", "r+").read())
    data["time_since_ocp"] = datetime.datetime.now().strftime(format_string)

    j = json.dumps(data)
    open("./config.json", "w").write(j)

    await ctx.respond("Reset the counter.")

@bot.slash_command(description="To get the time since the last time ocp's have been mentioned.")
# @commands.has_role("QOTD")
async def ocp(ctx):
    since = time_since_ocp()
    #alternitive format
    if math.floor(since.seconds / 3600) == 0:
        await ctx.respond(f"It has been {math.floor(since.seconds / 3600)} hours and {round((since.seconds / 60) - (math.floor(since.seconds / 3600) * 60))} minutes since ocps have been mentioned.")
        return
    await ctx.respond(f"It has been {since.days} days and {round((since.seconds / 3600) - (since.days * 24))} hours since ocps have been mentioned.")
#

#matnence
@bot.slash_command(description="Updates the bot")
@commands.has_role("Bot Lord")
async def update(ctx):
    await ctx.respond("starting update")
    subprocess.run(["git", "pull"])
    await ctx.send("update complete, restarting")
    subprocess.run(["systemctl", "restart", "--user", "SCP.service"])
    

@bot.slash_command(description="lol")
async def lol(ctx):
    await ctx.respond("lol")

@bot.slash_command(description="Rolls a d20")
async def roll(ctx):
    import random
    await ctx.respond("rolling d20")
    await ctx.respond(random.randint(1,20))


#<cpp enforcement>
cpp_connections = {}
record_connections = {}


async def once_done(sink: discord.sinks, channel: discord.TextChannel, *args):  # Our voice client already passes these in.


    recorded_users = [  # A list of recorded users
        f"<@{user_id}>"
        for user_id, audio in sink.audio_data.items()
    ]
    
    await sink.vc.disconnect()  # Disconnect from the voice channel.
    files = [discord.File(audio.file, f"{user_id}.{sink.encoding}") for user_id, audio in sink.audio_data.items()]  # List down the files.
  
    logchannel = bot.get_channel(int(config["log_id"]))

    await logchannel.send(f"finished recording audio for: {', '.join(recorded_users)}.", files=files)  # Send a message with the accumulated files.


    
@bot.slash_command(description="Robosmith will record until a third person joins the call.")
async def cpp(ctx):  # If you're using commands.Bot, this will also work.
    voice = ctx.author.voice

    # if not voice:
    #     await ctx.respond("You aren't in a voice channel!")
    #
    vc = await voice.channel.connect()  # Connect to the voice channel the author is in.
    cpp_connections.update({ctx.guild.id: vc})  # Updating the cache with the guild and channel.

    vc.start_recording(
        discord.sinks.MP3Sink(),  # The sink type to use.
        once_done,  # What to do once done.
        ctx.channel  # The channel to disconnect from.
    )
    await ctx.respond("enabled")

@bot.slash_command(description="Robosmith will record until a third person joins the call.")
# @commands.has_role("Staff")
async def record(ctx):  # If you're using commands.Bot, this will also work.
    voice = ctx.author.voice

    # if not voice:
    #     await ctx.respond("You aren't in a voice channel!")
    #
    vc = await voice.channel.connect()  # Connect to the voice channel the author is in.
    record_connections.update({ctx.guild.id: vc})  # Updating the cache with the guild and channel.

    vc.start_recording(
        discord.sinks.MP3Sink(),  # The sink type to use.
        once_done,  # What to do once done.
        ctx.channel  # The channel to disconnect from.
    )
    await ctx.respond("recording")

@bot.slash_command()
@commands.has_role("Staff")
async def stop_recording(ctx):
    if ctx.guild.id in record_connections:  # Check if the guild is in the cache.
        vc = record_connections[ctx.guild.id]
        vc.stop_recording()  # Stop recording, and call the callback (once_done).
        del record_connections[ctx.guild.id]  # Remove the guild from the cache.
        # await ctx.delete()  # And delete.
    else:
        await ctx.respond("I am currently not recording here.")  # Respond with this if we aren't recording.
        

#</cpp enforcement>

#<events>
@bot.event
async def on_voice_state_update(member, before, after):
    #
    # if before.channel is not None and after.channel is None:
    #     # Log the event, send a message, etc.
    #     print(f"{member.name} left the voice channel.")
    channel = after.channel
    
    if before.channel is not None and after.channel is None:
       # User has connected to a VoiceChannel
       channel = before.channel

        
    print(channel.members)
    if len(channel.members) <= 1 or len(channel.members) >= 4: 
        if channel.guild.id in cpp_connections:  # Check if the guild is in the cache.
            vc = cpp_connections[channel.guild.id]
            vc.stop_recording()  # Stop recording, and call the callback (once_done).
            del cpp_connections[channel.guild.id]  # Remove the guild from the cache.
            # await ctx.delete()  # And delete.

            
       # Code here...

log_file = open("logs.dislog", 'a')

@bot.listen()
async def on_message(message: discord.Message):
    print(message.content)

    sender = message.author

    entry = {
        "content": message.content,
        "sender_id": sender.id,
        "global_name": sender.global_name,
        "display_name": sender.display_name,
        "date": message.created_at.strftime("%Y-%m-%d %H:%M:%S")
    }

    print(entry)

    json.dump(entry, log_file)


    if "ocp" in message.content.lower():
        if not message.author.bot:
            data = json.loads(open("./config.json", "r+").read())
            data["time_since_ocp"] = datetime.datetime.now().strftime(format_string)

            j = json.dumps(data)
            open("./config.json", "w").write(j)
            await message.channel.send("OCP's mentioned, reset the counter. ._.")


#</events>

@bot.listen(once=True)
async def on_ready():
    qotd_task.start()

bot.run(token)
