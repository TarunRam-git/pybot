import discord
import os
from discord.ext import commands

from discord.ext import commands
from discord.ext import commands
import yt_dlp as youtube_dl

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ✅ Moderation Commands
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
    embed = discord.test(title="Bot Info", description="This is a multipurpose bot!", color=0x00ff00)
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
@commands.has_permissions(ban_members=True)  # Only users with ban permissions can use this
async def unban(ctx, user_id: int):
    guild = ctx.guild
    try:
        user = await bot.fetch_user(user_id)  
        await guild.unban(user)
        await ctx.send(f'✅ {user.name} has been unbanned.')
    except discord.NotFound:
        await ctx.send("❌ User not found in the ban list.")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to unban this user.")
    except Exception as e:
        await ctx.send(f"❌ An error occurred: {e}")


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
        await ctx.send(f"❌ `{word}` is already in the filter list.")
        return
    
    bad_words.append(word.lower())
    await ctx.send(f"✅ `{word}` has been added to the filter list!")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def showfilter(ctx):
    if not bad_words:
        await ctx.send("🔹 No words are currently filtered.")
    else:
        await ctx.send(f"🚫 **Filtered words:** {', '.join(bad_words)}")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return  # Ignore bot's own messages

    # Check if message contains any filtered words
    if any(word in message.content.lower() for word in bad_words):
        try:
            await message.delete()
            await message.channel.send(f"{message.author.mention}, watch your language! 🚫", delete_after=5)
        except discord.Forbidden:
            await message.channel.send("❌ I don't have permission to delete messages.")
        except discord.HTTPException:
            await message.channel.send("❌ Failed to delete the message due to an error.")

    await bot.process_commands(message)  # Allow bot commands to still work


# ✅ Music Player
@bot.command()
async def join(ctx):
    if ctx.author.voice:
        await ctx.author.voice.channel.connect()
        await ctx.send("🎵 Joined voice channel!")
    else:
        await ctx.send("❌ You must be in a voice channel!")

song_queue = []  # Global queue list

@bot.command()
async def queue(ctx, url):
    song_queue.append(url)
    await ctx.send(f"📌 Added to queue: {url}")

@bot.command()
async def play(ctx, url=None):
    vc = ctx.voice_client
    if not ctx.author.voice:
        await ctx.send("❌ You must be in a voice channel!")
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
        await ctx.send("❌ Bot is not in a voice channel!")
        return

    if song_queue:
        url = song_queue.pop(0)  
        ydl_opts = {'format': 'bestaudio'}
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            url2 = info['url']
            vc.play(discord.FFmpegPCMAudio(url2), after=lambda _: bot.loop.create_task(playnext(ctx)))
            await ctx.send(f"🎶 Now playing: {info['title']}")
    else:
        await ctx.send("✅ Queue is empty.")

@bot.command()
async def skip(ctx):
    vc = ctx.voice_client
    if vc and vc.is_playing():
        vc.stop()
        await ctx.send("⏭️ Skipping to the next song...")
        await playnext(ctx)
    else:
        await ctx.send("❌ No music is playing to skip!")

@bot.command()
async def stop(ctx):
    vc = ctx.voice_client
    if vc and vc.is_playing():
        vc.stop()
        await ctx.send("⏹️ Music stopped!")
    else:
        await ctx.send("❌ No music is currently playing.")

@bot.command()
async def leave(ctx):
    vc = ctx.voice_client
    if vc:
        await vc.disconnect()
        await ctx.send("👋 Left the voice channel.")

# ✅ Ticket System
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
@commands.has_permissions(manage_channels=True)  # Only mods/admins can use this
async def closeticket(ctx):
    if "ticket" in ctx.channel.name:  # Only works in ticket channels
        try:
            await ctx.channel.delete()
        except TimeoutError:
            await ctx.send("Channel deletion cancelled. You didn't confirm in time.")
    else:
        await ctx.send("❌ You can only delete **ticket channels**.")

bot.run(TOKEN)
