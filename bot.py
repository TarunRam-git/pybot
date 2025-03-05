import discord
import os
import requests
from dotenv import load_dotenv
load_dotenv()
from discord.ext import commands
import google.generativeai as genai
import asyncio
import re
import parsedatetime
from datetime import datetime
from discord.ui import Button, View
import yt_dlp as youtube_dl

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
WEATHER_API_KEY =os.getenv("WEATHER_API_TOKEN")
genai.configure(api_key=os.getenv("GEMINI_API_TOKEN"))
model = genai.GenerativeModel("gemini-1.5-flash")  



intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
#welcome message
@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="general")  
    if channel:
        await channel.send(f"Hello {member.mention}!\n"
                           "Welcome to GDSC Recruitments 2025! \n"
                           "We are glad you made it this far! ")

#remind
reminders = {}

@bot.command()
async def remindme(ctx, *, time_input):
    cal = parsedatetime.Calendar()
    time_struct, _ = cal.parse(time_input)
    reminder_time = datetime(*time_struct[:6])
    if reminder_time < datetime.now():
        await ctx.send(" That time is in the past! Provide a future time.")
        return
    reminder_text = " ".join(time_input.split()[2:]) or "No message provided"
    user_id = ctx.author.id
    if user_id not in reminders:
        reminders[user_id] = []
    reminders[user_id].append((reminder_time, reminder_text))
    await ctx.send(f" Reminder set for **{reminder_time.strftime('%d %B %Y %I:%M %p')}**.")
    await asyncio.sleep((reminder_time - datetime.now()).total_seconds())
    await ctx.send(f" {ctx.author.mention}, reminder: **{reminder_text}**")
    reminders[user_id] = [r for r in reminders[user_id] if r[0] > datetime.now()]

@bot.command()
async def listreminders(ctx):
    user_id = ctx.author.id
    if user_id not in reminders or not reminders[user_id]:
        await ctx.send(" You have no active reminders.")
        return
    reminder_list = "\n".join([f"{i+1}. **{r[0].strftime('%d %B %Y %I:%M %p')}** - {r[1]}" for i, r in enumerate(reminders[user_id])])
    await ctx.send(f" **Your Reminders:**\n{reminder_list}")

@bot.command()
async def deletereminder(ctx, reminder_number: int):
    user_id = ctx.author.id
    if user_id not in reminders or not reminders[user_id]:
        await ctx.send(" You have no active reminders to delete.")
        return
    if 1 <= reminder_number <= len(reminders[user_id]):
        removed = reminders[user_id].pop(reminder_number - 1)
        await ctx.send(f"🗑 Reminder for **{removed[0].strftime('%d %B %Y %I:%M %p')}** deleted.")
    else:
        await ctx.send("Invalid reminder number.")

@bot.command()
async def clearreminders(ctx):
    user_id = ctx.author.id
    if user_id in reminders:
        reminders.pop(user_id, None)
        await ctx.send(" All your reminders have been cleared.")
    else:
        await ctx.send(" You have no active reminders to clear.")

#embed
@bot.command()
async def embed(ctx, *, message: str):
    match = re.search(r"title:\s*(.*?)\s*body:\s*(.*)", message, re.IGNORECASE)
    
    if not match:
        await ctx.send(" Invalid format! Use `!embed title: Your Title body: Your Body`")
        return
    
    title, body = match.groups()

    embed = discord.Embed(
        title=title.strip(),
        description=body.strip().replace("\\n", "\n"),  
        color=discord.Color.blue()
    )


    await ctx.send(embed=embed)



#ModCommands
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.kick(reason=reason)
    await ctx.send(f"{member.mention} has been kicked!")

@bot.command()
async def hello(ctx):
    await ctx.send("Hello! 👋")
    if isinstance(ctx.channel, discord.DMChannel):
        await ctx.send("You're messaging me in DMs!")

@bot.command()
async def say(ctx, *, message):
    await ctx.send(message)

@bot.command()
async def info(ctx):
    embed = discord.Embed(title="Bot Info", description="This is a multipurpose bot!", color=0x00ff00)
    embed.add_field(name="Moderation Commands", value="!kick, !ban, !mute", inline=False)
    embed.add_field(name="Music Commands", value="!join, !queue, !play, !skip, !stop, !leave", inline=False)
    embed.add_field(name="General Commands", value="!hello, !say, !info", inline=False)
    embed.add_field(name="Ticket System", value="!ticket, !closeticket", inline=False)
    embed.set_footer(text="Made by You")
    await ctx.send(embed=embed)
#ban and unban
@bot.command()
@commands.has_permissions(ban_members=True) 
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    await member.ban(reason=reason)
    await ctx.send(f"{member.mention} has been banned!")
@bot.command()
@commands.has_permissions(ban_members=True) 
async def unban(ctx, user_id: int):
    guild = ctx.guild
    try:
        user = await bot.fetch_user(user_id)  
        await guild.unban(user)
        await ctx.send(f' {user.name} has been unbanned.')
    except discord.NotFound:
        await ctx.send(" User not found in the ban list.")
    except discord.Forbidden:
        await ctx.send(" I don't have permission to unban this user.")
    except Exception as e:
        await ctx.send(f" An error occurred: {e}")

#mute unmute
@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name="Muted")
    if not role:
        role = await ctx.guild.create_role(name="Muted")
        for channel in ctx.guild.channels:
            await channel.set_permissions(role, send_messages=False)
    for channel in ctx.guild.channels:
        await channel.set_permissions(role, send_messages=False, speak=False)

    await member.add_roles(role)
    await ctx.send(f"{member.mention} has been muted!")
@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name="Muted")
    
    if role in member.roles:
        await member.remove_roles(role)
        await ctx.send(f"{member.mention} has been unmuted!")
    else:
        await ctx.send(f"{member.mention} is not muted.")

#filter
bad_words = []

@bot.command()
@commands.has_permissions(manage_messages=True)
async def filter(ctx, word: str):
    if word.lower() in bad_words:
        await ctx.send(f" `{word}` is already in the filter list.")
        return
    
    bad_words.append(word.lower())
    await ctx.send(f" `{word}` has been added to the filter list!")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def showfilter(ctx):
    if not bad_words:
        await ctx.send("🔹 No words are currently filtered.")
    else:
        await ctx.send(f" **Filtered words:** {', '.join(bad_words)}")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return  

    
    if any(word in message.content.lower() for word in bad_words):
        try:
            await message.delete()
            await message.channel.send(f"{message.author.mention}, watch your language! 🚫", delete_after=5)
        except discord.Forbidden:
            await message.channel.send(" I don't have permission to delete messages.")
        except discord.HTTPException:
            await message.channel.send(" Failed to delete the message due to an error.")

    await bot.process_commands(message) 


# Music Player
@bot.command()
async def join(ctx):
    if ctx.author.voice:
        await ctx.author.voice.channel.connect()
        await ctx.send(" Joined voice channel!")
    else:
        await ctx.send(" You must be in a voice channel!")

song_queue = []  

@bot.command()
async def queue(ctx, url):
    song_queue.append(url)
    await ctx.send(f" Added to queue: {url}")

@bot.command()
async def play(ctx, url=None):
    vc = ctx.voice_client
    if not ctx.author.voice:
        await ctx.send(" You must be in a voice channel!")
        return

    if not vc:
        vc = await ctx.author.voice.channel.connect()

    if url:
        song_queue.append(url)

    if not vc.is_playing():
        await playnext(ctx)

async def playnext(ctx):
    vc = ctx.voice_client

    if not vc:
        await ctx.send(" Bot is not in a voice channel!")
        return

    if song_queue:
        url = song_queue.pop(0)  
        ydl_opts = {'format': 'bestaudio'}
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            url2 = info['url']
            vc.play(discord.FFmpegPCMAudio(url2), after=lambda _: bot.loop.create_task(playnext(ctx)))
            await ctx.send(f" Now playing: {info['title']}")
    else:
        await ctx.send(" Queue is empty.")

@bot.command()
async def skip(ctx):
    vc = ctx.voice_client
    if vc and vc.is_playing():
        vc.stop()
        await ctx.send(" Skipping to the next song...")
        await playnext(ctx)
    else:
        await ctx.send(" No music is playing to skip!")

@bot.command()
async def stop(ctx):
    vc = ctx.voice_client
    if vc and vc.is_playing():
        vc.stop()
        await ctx.send(" Music stopped!")
    else:
        await ctx.send(" No music is currently playing.")

@bot.command()
async def leave(ctx):
    vc = ctx.voice_client
    if vc:
        await vc.disconnect()
        await ctx.send(" Left the voice channel.")

#apis

@bot.command()
async def summarize(ctx, *, text):
    
    if text is None:
        await ctx.send("Please provide a paragraph to summarize.")
        return

    await ctx.send("Summarizing...")

    try:
        response = await asyncio.to_thread(model.generate_content, f"summarize {text}" )
        summary = str(response.text.strip())

        embed = discord.Embed(title="Summary", description=summary, color=discord.Color.green())
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"Error: {str(e)}")





@bot.command()
async def joke(ctx):
    url = "https://v2.jokeapi.dev/joke/Any"
    response = requests.get(url).json()
    
    if response["type"] == "single":
        await ctx.send(response["joke"])  # Single line joke
    else:
        await ctx.send(f"{response['setup']}\n{response['delivery']}")  # Two-part joke
@bot.command()
async def weather(ctx, *, city: str):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
    response = requests.get(url).json()

    if response.get("cod") == 200:  # Ensure it's checking an integer, not a string
        city_name = response["name"]
        country = response["sys"]["country"]
        temp = response["main"]["temp"]
        weather_desc = response["weather"][0]["description"]
        humidity = response["main"]["humidity"]
        wind_speed = response["wind"]["speed"]

        weather_report = (
            f"**Weather in {city_name}, {country}:**\n"
            f" Temperature: {temp}°C\n"
            f" Condition: {weather_desc.capitalize()}\n"
            f" Humidity: {humidity}%\n"
            f" Wind Speed: {wind_speed} m/s"
        )
        await ctx.send(weather_report)
    else:
        await ctx.send(f" Error: {response.get('message', 'Invalid city name or API error.')}")


#better ticket
class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)  

    @discord.ui.button(label="Create Ticket", style=discord.ButtonStyle.green, custom_id="create_ticket")
    async def create_ticket(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name="Tickets")  
        if not category:
            category = await guild.create_category("Tickets")  
        ticket_number = sum(1 for c in category.channels if c.name.startswith("ticket-")) + 1
        ticket_name = f"ticket-{ticket_number:04d}"  

        ticket_channel = await guild.create_text_channel(ticket_name, category=category)
        await ticket_channel.set_permissions(interaction.user, read_messages=True, send_messages=True)
        
        await ticket_channel.send(f"{interaction.user.mention}, your ticket has been created!")
        await interaction.response.send_message(f" Ticket **{ticket_name}** created!", ephemeral=True)

@bot.command()
async def ticket(ctx):
    embed = discord.Embed(
        title=" Support Ticket System",
        description="Click the **Create Ticket** button below to create a support ticket.",
        color=discord.Color.blue()
    )
    view = TicketView()
    await ctx.send(embed=embed, view=view)

@bot.command()
@commands.has_permissions(manage_channels=True)
async def closeticket(ctx):
    if ctx.channel.category and ctx.channel.category.name == "Tickets": 
        
        await ctx.channel.delete()
    else:
        await ctx.send(" You can only use this command inside a **ticket channel**.")

'''# Ticket System
@bot.command()
async def ticket(ctx):
    guild = ctx.guild
    category = discord.utils.get(guild.categories, name="Tickets")
    if not category:
        category = await guild.create_category("Tickets")
    
    ticket_channel = await guild.create_text_channel(f"ticket-{ctx.author.name}", category=category)
    await ticket_channel.set_permissions(ctx.author, read_messages=True, send_messages=True)
    await ticket_channel.send(f"{ctx.author.mention}, how can we help you?")

@bot.command()
@commands.has_permissions(manage_channels=True)  
async def closeticket(ctx):
    if "ticket" in ctx.channel.name:  
        try:
            await ctx.channel.delete()
        except TimeoutError:
            await ctx.send("Channel deletion cancelled. You didn't confirm in time.")
    else:
        await ctx.send(" You can only delete **ticket channels**.")'''

bot.run(TOKEN)
