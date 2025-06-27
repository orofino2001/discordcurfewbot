import discord
from discord.ext import commands, tasks
import pytz
from datetime import datetime, time
import re
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize bot with intents
intents = discord.Intents.default()
intents.voice_states = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Database to store user settings (consider using a real database for production)
user_settings = {}

# -------------------- COMMANDS --------------------
@bot.command()
async def bedtimehelp(ctx):
    """Show all available commands"""
    embed = discord.Embed(
        title="🌙 Bedtime Bot Help",
        description="Get automatically kicked from voice channels at your bedtime!",
        color=0x7289da
    )
    commands = [
        ("!settimezone [zone]", "Set your timezone (e.g. !settimezone Europe/London)"),
        ("!setbedtime [HH:MM]", "Set your bedtime in 24-hour format (e.g. !setbedtime 23:30)"),
        ("!enable", "Enable bedtime reminders"),
        ("!disable", "Disable bedtime reminders"),
        ("!mybedtime", "Show your current settings"),
        ("!testkick", "Test if bot can kick you from VC"),
        ("!debug", "Show debug information")
    ]
    
    for name, value in commands:
        embed.add_field(name=name, value=value, inline=False)
    
    await ctx.send(embed=embed)

@bot.command()
async def settimezone(ctx, timezone: str):
    """Set your timezone"""
    if timezone not in pytz.all_timezones:
        common_tz = "\n".join([
            "Common timezones:",
            "- Europe/London",
            "- America/New_York",
            "- Asia/Tokyo",
            "- Australia/Sydney"
        ])
        await ctx.send(f"Invalid timezone! Please use one from the IANA timezone database.\n{common_tz}")
        return
    
    # Initialize user settings if not exists
    if ctx.author.id not in user_settings:
        user_settings[ctx.author.id] = {"enabled": True}
    
    user_settings[ctx.author.id]["timezone"] = timezone
    await ctx.send(f"⏰ Timezone successfully set to `{timezone}`")

@bot.command()
async def setbedtime(ctx, time_str: str):
    """Set your bedtime in HH:MM format"""
    if not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', time_str):
        return await ctx.send("Please use 24-hour format (e.g., `22:30` or `04:00`)")
    
    # Initialize user settings if not exists
    if ctx.author.id not in user_settings:
        user_settings[ctx.author.id] = {"enabled": True}
    
    user_settings[ctx.author.id]["bedtime"] = time_str
    await ctx.send(f"🌙 Bedtime successfully set to `{time_str}`")

@bot.command()
async def enable(ctx):
    """Enable bedtime checks"""
    if ctx.author.id not in user_settings:
        user_settings[ctx.author.id] = {}
    
    user_settings[ctx.author.id]["enabled"] = True
    await ctx.send("✅ Bedtime checks have been enabled")

@bot.command()
async def disable(ctx):
    """Disable bedtime checks"""
    if ctx.author.id not in user_settings:
        user_settings[ctx.author.id] = {}
    
    user_settings[ctx.author.id]["enabled"] = False
    await ctx.send("❌ Bedtime checks have been disabled")

@bot.command()
async def mybedtime(ctx):
    """Show your current settings"""
    settings = user_settings.get(ctx.author.id, {})
    
    embed = discord.Embed(
        title=f"{ctx.author.display_name}'s Bedtime Settings",
        color=0x00ff00
    )
    
    embed.add_field(name="Timezone", value=settings.get("timezone", "Not set"), inline=True)
    embed.add_field(name="Bedtime", value=settings.get("bedtime", "Not set"), inline=True)
    embed.add_field(
        name="Status", 
        value="✅ Enabled" if settings.get("enabled", False) else "❌ Disabled", 
        inline=True
    )
    
    if "timezone" in settings and "bedtime" in settings:
        try:
            tz = pytz.timezone(settings["timezone"])
            now = datetime.now(pytz.UTC).astimezone(tz)
            bedtime = datetime.strptime(settings["bedtime"], "%H:%M").time()
            
            if now.time() >= bedtime:
                status = "⏰ It's past your bedtime!"
            else:
                status = "🕒 You still have time before bedtime"
            
            embed.add_field(name="Current Status", value=status, inline=False)
        except Exception as e:
            print(f"Error calculating bedtime status: {e}")
    
    await ctx.send(embed=embed)

@bot.command()
async def testkick(ctx):
    """Test if bot can kick you from voice channel"""
    if not ctx.author.voice or not ctx.author.voice.channel:
        return await ctx.send("❌ You're not currently in a voice channel!")
    
    try:
        await ctx.author.move_to(None)
        await ctx.send("✅ Successfully kicked you from the voice channel!")
    except discord.Forbidden:
        error_msg = [
            "❌ Bot lacks permissions to move you!",
            "Required permissions:",
            "- Move Members",
            "- Connect",
            "- View Channel",
            "",
            "Also ensure the bot's role is above yours in server settings."
        ]
        await ctx.send("\n".join(error_msg))
    except Exception as e:
        await ctx.send(f"⚠️ An unexpected error occurred: `{type(e).__name__}`")

@bot.command()
async def debug(ctx):
    """Show debug information"""
    if not ctx.author.voice or not ctx.author.voice.channel:
        return await ctx.send("You're not in a voice channel.")
    
    vc = ctx.author.voice.channel
    perms = vc.permissions_for(ctx.guild.me)
    
    embed = discord.Embed(title="Debug Information", color=0xff9900)
    embed.add_field(name="Voice Channel", value=vc.name, inline=False)
    embed.add_field(name="Move Members Permission", value=perms.move_members, inline=True)
    embed.add_field(name="Connect Permission", value=perms.connect, inline=True)
    embed.add_field(name="View Channel Permission", value=perms.view_channel, inline=True)
    
    if ctx.guild.me.top_role.position <= ctx.author.top_role.position:
        embed.add_field(
            name="Role Hierarchy", 
            value="❌ Bot role is NOT above user", 
            inline=False
        )
    else:
        embed.add_field(
            name="Role Hierarchy", 
            value="✅ Bot role is above user", 
            inline=False
        )
    
    await ctx.send(embed=embed)

# -------------------- AUTO KICK LOGIC --------------------
@tasks.loop(minutes=1)
async def bedtime_check():
    now_utc = datetime.now(pytz.UTC)
    print(f"\n[Bedtime Check] Running at {now_utc.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    
    for guild in bot.guilds:
        print(f"\nChecking guild: {guild.name} (ID: {guild.id})")
        
        for member in guild.members:
            if member.bot:
                continue
            
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
                bedtime = time(h, m)
                
                print(f"Checking {member.display_name}: Local time {user_time.strftime('%H:%M')}, Bedtime {settings['bedtime']}")
                
                # Check if current time >= bedtime
                if user_time.time() >= bedtime:
                    print(f"Should kick {member.display_name}")
                    try:
                        await member.move_to(None)
                        await member.send(
                            f"⏰ Goodnight {member.display_name}! "
                            f"It's {user_time.strftime('%H:%M')} in your timezone, "
                            f"which is past your bedtime of {settings['bedtime']}. "
                            f"Sleep well! 😴"
                        )
                        print(f"Successfully kicked {member.display_name}")
                    except discord.Forbidden:
                        print(f"Failed to kick {member.display_name}: Missing permissions")
                    except Exception as e:
                        print(f"Error kicking {member.display_name}: {type(e).__name__}: {e}")
            except Exception as e:
                print(f"Error processing {member.display_name}: {type(e).__name__}: {e}")

# -------------------- BOT EVENTS --------------------
@bot.event
async def on_ready():
    print(f"\nBot is ready! Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"Currently in {len(bot.guilds)} guild(s):")
    for guild in bot.guilds:
        print(f"- {guild.name} (ID: {guild.id})")
    
    # Start the bedtime check loop
    try:
        bedtime_check.start()
        print("Started bedtime check task")
    except RuntimeError as e:
        print(f"Error starting bedtime check: {e}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Command not found. Use `!bedtimehelp` for available commands.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing required argument: {error.param.name}")
    else:
        print(f"Error in command {ctx.command}: {type(error).__name__}: {error}")
        await ctx.send("⚠️ An error occurred while executing that command.")

# -------------------- BOT STARTUP --------------------
if __name__ == "__main__":
    try:
        bot.run(os.getenv("DISCORD_TOKEN"))
    except discord.LoginFailure:
        print("Error: Invalid Discord token. Please check your .env file.")
    except Exception as e:
        print(f"Fatal error: {type(e).__name__}: {e}")
