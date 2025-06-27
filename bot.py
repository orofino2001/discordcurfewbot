import discord
from discord.ext import commands, tasks
import pytz
from datetime import datetime, time
import re

intents = discord.Intents.default()
intents.voice_states = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# User settings storage
user_settings = {}

# -------------------- COMMANDS --------------------
@bot.command()
async def bedtimehelp(ctx):
    """Show all commands"""
    embed = discord.Embed(
        title="🌙 Bedtime Bot Help",
        description="Get kicked from VC at your bedtime!",
        color=0x7289da
    )
    embed.add_field(name="!settimezone [zone]", value="e.g. `!settimezone Europe/London`", inline=False)
    embed.add_field(name="!setbedtime [HH:MM]", value="e.g. `!setbedtime 23:30`", inline=False)
    embed.add_field(name="!enable", value="Turn on bedtime checks", inline=False)
    embed.add_field(name="!disable", value="Turn off bedtime checks", inline=False)
    embed.add_field(name="!mybedtime", value="Show your settings", inline=False)
    embed.add_field(name="!testkick", value="Test if bot can kick you", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def settimezone(ctx, timezone: str):
    """Set your timezone"""
    if timezone not in pytz.all_timezones:
        await ctx.send("Invalid timezone! Try:\n`Europe/London`\n`America/New_York`\n`Asia/Tokyo`")
        return
    
    if ctx.author.id not in user_settings:
        user_settings[ctx.author.id] = {"enabled": True}
    
    user_settings[ctx.author.id]["timezone"] = timezone
    await ctx.send(f"⏰ Timezone set to `{timezone}`")

@bot.command()
async def setbedtime(ctx, time_str: str):
    """Set your bedtime (HH:MM)"""
    if not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', time_str):
        return await ctx.send("Use 24-hour format like `22:30`")
    
    if ctx.author.id not in user_settings:
        user_settings[ctx.author.id] = {"enabled": True}
    
    user_settings[ctx.author.id]["bedtime"] = time_str
    await ctx.send(f"🌙 Bedtime set to `{time_str}`")

@bot.command()
async def enable(ctx):
    """Enable bedtime checks"""
    if ctx.author.id not in user_settings:
        user_settings[ctx.author.id] = {}
    user_settings[ctx.author.id]["enabled"] = True
    await ctx.send("✅ Bedtime checks enabled")

@bot.command()
async def disable(ctx):
    """Disable bedtime checks"""
    if ctx.author.id not in user_settings:
        user_settings[ctx.author.id] = {}
    user_settings[ctx.author.id]["enabled"] = False
    await ctx.send("❌ Bedtime checks disabled")

@bot.command()
async def mybedtime(ctx):
    """Show your settings"""
    settings = user_settings.get(ctx.author.id, {})
    
    embed = discord.Embed(title="Your Settings", color=0x00ff00)
    embed.add_field(name="Timezone", value=settings.get("timezone", "Not set"))
    embed.add_field(name="Bedtime", value=settings.get("bedtime", "Not set"))
    embed.add_field(name="Status", value="✅ Enabled" if settings.get("enabled", False) else "❌ Disabled")
    await ctx.send(embed=embed)

@bot.command()
async def testkick(ctx):
    """Test if bot can kick you"""
    if not ctx.author.voice:
        return await ctx.send("❌ You're not in a voice channel!")
    
    try:
        await ctx.author.move_to(None)
        await ctx.send("✅ Successfully kicked you from VC!")
    except discord.Forbidden:
        await ctx.send("❌ Bot lacks permissions! Needs:")
        await ctx.send("1. **Move Members** permission\n2. Role higher than yours")
    except Exception as e:
        await ctx.send(f"⚠️ Error: `{type(e).__name__}`")

# -------------------- AUTO KICK LOGIC --------------------
@tasks.loop(minutes=1)
async def bedtime_check():
    now_utc = datetime.now(pytz.UTC)
    
    for guild in bot.guilds:
        for member in guild.members:
            if member.bot: continue
            
            # Skip if not in VC or no settings
            if not member.voice or not member.voice.channel or member.id not in user_settings:
                continue
            
            settings = user_settings[member.id]
            
            # Skip if disabled or missing settings
            if not settings.get("enabled", False) or "timezone" not in settings or "bedtime" not in settings:
                continue
            
            try:
                # Get user's local time
                tz = pytz.timezone(settings["timezone"])
                user_time = now_utc.astimezone(tz)
                h, m = map(int, settings["bedtime"].split(':'))
                
                # Check if current time >= bedtime
                if (user_time.hour > h) or (user_time.hour == h and user_time.minute >= m):
                    try:
                        await member.move_to(None)
                        await member.send(f"⏰ Goodnight! It's past your bedtime ({settings['bedtime']})")
                        print(f"Kicked {member} at {user_time.strftime('%H:%M')}")
                    except Exception as e:
                        print(f"Failed to kick {member}: {e}")
            except Exception as e:
                print(f"Error processing {member}: {e}")

# -------------------- BOT STARTUP --------------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    print(f"Monitoring {len(bot.guilds)} servers")
    bedtime_check.start()

bot.run("MTM4Nzk3ODQ0NDEzMzg5MjE0Nw.GPkA5y.eJh9NWROMF-Z_3iTKv45oTmSt0hyvS-0mig4Ek")  # Replace with your actual token