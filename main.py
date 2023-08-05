import discord
from discord.ext import commands, tasks
import datetime
import pytz
import asyncio
import random
import keep_alive
import json
import os
import requests
from PIL import Image, ImageDraw, ImageFont
import io


# 2nd and 3rd position settings for role 
# Help section image

Permanent_color = discord.Color.from_rgb(255, 119, 0)
bot = commands.Bot(command_prefix='.', intents=discord.Intents.all())
intents = discord.Intents.default()
intents.members = True
intents.typing = False
intents.presences = False
server_settings={}



def save_server_settings():
    # Save the server settings to a JSON file
    with open("server_settings.json", "w") as file:
        json.dump(server_settings, file)

def save_settings():
    with open("server_settings.json", "w") as f:
        json.dump(server_settings, f)

def load_settings():
    global server_settings

    try:
        with open("settings.json", "r") as file:
            server_settings = json.load(file)
    except FileNotFoundError:
        # If settings file doesn't exist, initialize with an empty dictionary
        server_settings = {}

def load_server_settings():
    try:
        with open("server_settings.json", "r") as file:
            # Check if the file is empty
            if os.path.getsize("server_settings.json") > 0:
                return json.load(file)
            else:
                # If the file is empty, return an empty dictionary
                return {}
    except FileNotFoundError:
        # If the file doesn't exist yet, return an empty dictionary
        return {}

async def add_new_server_settings(guild):
    # Add new server settings data when the bot joins a server
    server_settings[guild.id] = {
        "welcome_channel_id": None,
        "welcome_message": "Welcome @user to {server}, enjoy your stay and have fun ⭐",
        "message_channel_id": None
        # Add other required data for server settings here...
    }
    save_server_settings()

@bot.event
async def on_guild_join(guild):
    add_new_server_settings(guild)

def load_server_settings():
    try:
        with open("server_settings.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        # If the file doesn't exist yet, return an empty dictionary
        return {}

def save_server_settings():
    with open("server_settings.json", "w") as file:
        json.dump(server_settings, file)

def save_todo_tasks():
    # Save the todo list data to a JSON file
    with open("todo_tasks.json", "w") as file:
        json.dump(todo_tasks, file)

def load_todo_tasks():
    try:
        with open("todo_tasks.json", "r") as file:
            # Check if the file is empty
            if os.path.getsize("todo_tasks.json") > 0:
                return json.load(file)
            else:
                # If the file is empty, return an empty dictionary
                return {}
    except FileNotFoundError:
        # If the file doesn't exist yet, return an empty dictionary
        return {}
server_settings = load_server_settings()


server_settings = load_server_settings()
vc_roles = {}
user_voice_times = {}
todo_tasks = load_todo_tasks()
pomodoro_times = {}
pomodoro_settings = {}
daily_voice_times = {}
daily_leaderboard = {}
monthly_leaderboard = {}
IST = pytz.timezone('Asia/Kolkata')
HH, MM = 0, 0
upload_time = datetime.time(HH, MM)
BOT_AVATAR_URL = "https://imgur.com/a/7qtxGa1"
HELP_IMAGE_PATHS = ["assets/1.png", "assets/2.png", "assets/3.png", "assets/4.png"]


def get_user_vc_time(user_id):
    if user_id in user_voice_times:
        return user_voice_times[user_id]
    return datetime.timedelta()

async def reset_daily_voice_tracking():
    daily_voice_times.clear()

@tasks.loop(hours=24)
async def daily_leaderboard():
    # Generate and send daily leaderboard here
    await reset_daily_voice_tracking()

@daily_leaderboard.before_loop
async def before_leaderboard():
    await bot.wait_until_ready()
    tz = pytz.timezone('Your_Timezone')
    now = datetime.datetime.now(tz)
    time_to_reset = datetime.time(0, 0)
    next_reset = datetime.datetime.combine(now + datetime.timedelta(days=1), time_to_reset)
    seconds_until_reset = (next_reset - now).total_seconds()
    await asyncio.sleep(seconds_until_reset)
    # Call the reset_daily_voice_tracking function after the initial delay
    await reset_daily_voice_tracking()



def calculate_monthly_vc_time(member_id):
    total_time = 0
    for guild_id, data in user_voice_times.items():
        if member_id in data:
            total_time += data[member_id]
    return total_time


class HelpView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=None)  # Set timeout to None to keep the buttons active indefinitely
        self.ctx = ctx
        self.current_page = 0

    async def show_page(self, page_num):
        file_path = HELP_IMAGE_PATHS[page_num]
        file = discord.File(file_path)

        content = f"Page {page_num + 1}/{len(HELP_IMAGE_PATHS)}"
        message = await self.ctx.send(content=content, file=file, view=self)

        # Delete the original message if it exists
        if hasattr(self.ctx, "message"):
            try:
                await self.ctx.message.delete()
            except discord.Forbidden:
                pass

        # Update the context with the new message
        self.ctx.message = message

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.primary)
    async def prev_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.current_page -= 1
        if self.current_page < 0:
            self.current_page = len(HELP_IMAGE_PATHS) - 1

        await self.show_page(self.current_page)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.primary)
    async def next_page(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.current_page += 1
        if self.current_page >= len(HELP_IMAGE_PATHS):
            self.current_page = 0

        await self.show_page(self.current_page)

@bot.command()
async def gethelp(ctx):
    view = HelpView(ctx)
    await view.show_page(view.current_page)

# Command to set welcome message
@bot.command()
async def setwelcome(ctx, *, message):
    if ctx.guild.id not in server_settings:
        server_settings[ctx.guild.id] = {
            "welcome_status": True,
            "welcome_message": "",
            "welcome_channel_id": None
        }
    server_settings[ctx.guild.id]["welcome_message"] = message
    save_settings()
    await ctx.send(f"Welcome message set: `{message}`")

# Command to remove welcome message
@bot.command()
async def rmwelcome(ctx):
    server_settings[ctx.guild.id].pop("welcome_message", None)
    save_settings()
    await ctx.send("Welcome message removed.")

# Command to set welcome channel
@bot.command()
async def setwelcomechannel(ctx, channel: discord.TextChannel):
    server_settings[ctx.guild.id]["welcome_channel_id"] = channel.id
    save_settings()
    await ctx.send(f"Welcome channel set to: {channel.mention}")

# Command to enable/disable welcome messages
@bot.command()
async def setwelcomestatus(ctx, status: bool):
    server_settings[ctx.guild.id]["welcome_status"] = status
    save_settings()
    await ctx.send(f"Welcome messages are {'enabled' if status else 'disabled'}.")

## Readiness

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    for guild in bot.guilds:
        if guild.id not in server_settings:
            server_settings[guild.id] = {
                "vc_channels": [],
                "message_channel_id": None,
                "embed_color": discord.Color.dark_blue().value,
                "mercy_time": 5,
                "monthly_top_role": None,
                "vc_count_dict": {}
            }
            vc_roles[guild.id] = {}
    save_server_settings()
    load_settings()

#xontuinues

@bot.event
async def on_member_join(member):
    guild_id = member.guild.id
    if guild_id not in server_settings:
        server_settings[guild_id] = {
            "welcome_status": True,
            "welcome_message": "Welcome to our server!",
            "welcome_channel_id": None
        }
        save_settings()

    if server_settings[guild_id]["welcome_status"]:
        welcome_message = server_settings[guild_id]["welcome_message"].replace("{user}", member.mention).replace("{server}", member.guild.name)

        if server_settings[guild_id]["welcome_channel_id"] is not None:
            channel = member.guild.get_channel(server_settings[guild_id]["welcome_channel_id"])
            if channel:
                await channel.send(welcome_message)
        else:
            await member.send(welcome_message)


## securtiy below

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f"{member.mention} has been kicked. Reason: {reason}")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f"{member.mention} has been banned. Reason: {reason}")

@bot.command()
@commands.has_permissions(mute_members=True)
async def mute(ctx, member: discord.Member, *, reason=None):
    # Assuming you have a 'Muted' role to apply to muted users
    muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
    
    if not muted_role:
        # If 'Muted' role does not exist, create it
        muted_role = await ctx.guild.create_role(name="Muted")
        for channel in ctx.guild.channels:
            # Disable send message permissions for the 'Muted' role in all channels
            await channel.set_permissions(muted_role, send_messages=False)
    
    await member.add_roles(muted_role)
    
    # Check if a timeout was provided in the reason (in minutes) and unmute after the timeout
    timeout_minutes = None
    if reason and "min" in reason:
        timeout_index = reason.find("min")
        try:
            timeout_minutes = int(reason[:timeout_index].strip())
            reason = reason[timeout_index + 3:].strip()
        except ValueError:
            pass
    
    await ctx.send(f"{member.mention} has been muted. Reason: {reason}")
    
    if timeout_minutes:
        await asyncio.sleep(timeout_minutes * 60)
        await member.remove_roles(muted_role)
        await ctx.send(f"{member.mention} has been unmuted after the timeout.")

@bot.command()
async def unmute(ctx, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name="Muted")
    if role in member.roles:
        await member.remove_roles(role)
        await ctx.send(f"{member.mention} has been unmuted.")
    else:
        await ctx.send(f"{member.mention} is not muted.")

# Command to unban a member
@bot.command()
async def unban(ctx, member_id: int):
    banned_users = await ctx.guild.bans()
    member = discord.utils.find(lambda u: u.user.id == member_id, banned_users)

    if member:
        await ctx.guild.unban(member.user)
        await ctx.send(f"{member.user.mention} has been unbanned.")
    else:
        await ctx.send("Member not found or not banned.")

@bot.command()
async def warn(ctx, member: discord.Member, *, reason=None):
    await ctx.send(f"{member.mention} has been warned. Reason: {reason}")

@kick.error
@ban.error
@mute.error
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have the necessary permissions to execute this command.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Invalid user specified.")
    else:
        print(error)

def is_baby_account(member):
    account_age_hours = (member.created_at - discord.utils.utcnow()).total_seconds() / 3600
    return account_age_hours <= server_settings.get(member.guild.id, {}).get("baby_account_threshold", 5)

@bot.event
async def on_member_join(member):
    server_id = member.guild.id
    if server_id in server_settings:
        wait_time = server_settings[server_id].get("verification_wait", 0)
        if wait_time > 0:
            if is_baby_account(member):
                try:
                    await member.send("Welcome! Before you can chat, you need to wait for verification. Please consult the mods and add them as friends for verification.")
                    await member.edit(mute=True)
                    await asyncio.sleep(wait_time * 60)  # Convert wait_time to seconds
                    await member.edit(mute=False)
                    await member.send("Verification wait time is over. You can now chat in the server.")
                except discord.Forbidden:
                    print(f"Could not send DM to {member.display_name}. Please ensure the user allows DMs from this server.")
            else:
                await member.send("Welcome to the server!")
        else:
            await member.send("Welcome to the server!")


@bot.command()
async def setbabybench(ctx, time_in_hours: int):
    if time_in_hours > 0:
        server_settings[ctx.guild.id] = {
            "baby_account_threshold": time_in_hours,
            "verification_wait": server_settings.get(ctx.guild.id, {}).get("verification_wait", 0)
        }
        await ctx.send(f"Baby account threshold set to {time_in_hours} hours.")
    else:
        await ctx.send("Please provide a positive integer value for the time.")








@bot.command()
async def setmonthlytoprole(ctx, *roles: discord.Role):
    if ctx.author.guild_permissions.administrator:
        server_settings[ctx.guild.id]["monthly_top_roles"] = [role.id for role in roles]
        await ctx.send("The monthly top roles have been set.")
    else:
        await ctx.send("You don't have the required permissions to use this command.")

@bot.command()
async def setdailytoprole(ctx, *roles: discord.Role):
    if ctx.author.guild_permissions.administrator:
        server_settings[ctx.guild.id]["daily_top_roles"] = [role.id for role in roles]
        await ctx.send("The daily top roles have been set.")
    else:
        await ctx.send("You don't have the required permissions to use this command.")

@bot.command()
async def setaimrole(ctx, *roles: discord.Role):
    if ctx.author.guild_permissions.administrator:
        server_settings[ctx.guild.id]["aim_roles"] = [role.id for role in roles]
        await ctx.send("The aim roles have been set.")
    else:
        await ctx.send("You don't have the required permissions to use this command.")

@bot.command()
async def setdailyleadb(ctx, channel: discord.TextChannel):
    if ctx.author.guild_permissions.administrator:
        server_settings[ctx.guild.id]["daily_leaderboard_channel_id"] = channel.id
        await ctx.send(f"The daily leaderboard channel has been set to '{channel.mention}'.")
    else:
        await ctx.send("You don't have the required permissions to use this command.")

@bot.command()
async def setmonthlyleadb(ctx, channel: discord.TextChannel):
    if ctx.author.guild_permissions.administrator:
        server_settings[ctx.guild.id]["monthly_leaderboard_channel_id"] = channel.id
        await ctx.send(f"The monthly leaderboard channel has been set to '{channel.mention}'.")
    else:
        await ctx.send("You don't have the required permissions to use this command.")

@bot.command()
async def setmercytime(ctx, seconds: int):
    if ctx.author.guild_permissions.administrator:
        server_settings[ctx.guild.id]["mercy_time"] = seconds
        await ctx.send(f"The mercy time has been set to {seconds} seconds.")
    else:
        await ctx.send("You don't have the required permissions to use this command.")

# ... (previous code)

@bot.command()
async def topdaily(ctx):
  await generate_daily_leaderboard(ctx.guild, ctx.channel)

@bot.command()
async def topmonthly(ctx):
  await generate_monthly_leaderboard(ctx.guild, ctx.channel)

@bot.command()
async def settracking(ctx, *channels: discord.VoiceChannel):
    if ctx.author.guild_permissions.administrator:
        server_settings[ctx.guild.id]["vc_channels"] = [channel.id for channel in channels]
        await ctx.send("Tracking has been set for the specified voice channels.")
    else:
        await ctx.send("You don't have the required permissions to use this command.")

@bot.command()
async def removetracking(ctx, *channels: discord.VoiceChannel):
    if ctx.author.guild_permissions.administrator:
        for channel in channels:
            server_settings[ctx.guild.id]["vc_channels"].remove(channel.id)
        await ctx.send("Tracking has been removed for the specified voice channels.")
    else:
        await ctx.send("You don't have the required permissions to use this command.")

# ... (previous code)
















@bot.command()
async def setwait(ctx, time_in_minutes: int):
    if time_in_minutes >= 0:
        server_settings[ctx.guild.id] = {
            "baby_account_threshold": server_settings.get(ctx.guild.id, {}).get("baby_account_threshold", 5),
            "verification_wait": time_in_minutes
        }
        await ctx.send(f"Verification wait time set to {time_in_minutes} minutes.")
    else:
        await ctx.send("Please provide a non-negative integer value for the time.")


@bot.command()
async def setnowait(ctx):
    server_id = str(ctx.guild.id)
    if server_id not in server_settings:
        server_settings[server_id] = {}

    server_settings[server_id]["verification_mute"] = False
    save_settings()
    await ctx.send("Verification mute disabled.")
  
##security above

@bot.command()
async def setvcrole(ctx, vc_channel: discord.VoiceChannel,vc_role: discord.Role):
  # Command to set a role for a specific VC channel (only server admins can use this)
  if ctx.author.guild_permissions.administrator:
    vc_roles[ctx.guild.id][vc_channel.id] = vc_role.id
    await ctx.send(
        f"The role '{vc_role.name}' is now set for the VC channel '{vc_channel.name}'."
    )
  else:
    await ctx.send(
        "You don't have the required permissions to use this command.")


@bot.command()
async def removevcrole(ctx, vc_channel: discord.VoiceChannel):
  # Command to remove the role for a specific VC channel (only server admins can use this)
  if ctx.author.guild_permissions.administrator:
    if vc_channel.id in vc_roles[ctx.guild.id]:
      del vc_roles[ctx.guild.id][vc_channel.id]
      await ctx.send(
          f"The role for the VC channel '{vc_channel.name}' has been removed.")
    else:
      await ctx.send("There is no role set for this VC channel.")
  else:
    await ctx.send(
        "You don't have the required permissions to use this command.")


@bot.command()
async def dailylbcheck(ctx):
    # Command to display the remaining time for the next pomodoro session
    current_time = datetime.datetime.now(IST).time()
    next_pomodoro_time = pomodoro_times.get(ctx.guild.id, datetime.time(0, 0))

    # Check if the daily leaderboard has already been sent for the day
    if current_time > upload_time:
        next_pomodoro_time = pomodoro_times.get(ctx.guild.id, datetime.time(0, 0))
    else:
        next_pomodoro_time = upload_time

    time_left = datetime.datetime.combine(
        datetime.date.today(), next_pomodoro_time) - datetime.datetime.combine(
            datetime.date.today(), current_time)
    
    # Calculate the time left in hours, minutes, and seconds
    hours, remainder = divmod(time_left.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    await ctx.send(
        f"The next daily leaderboard will be uploaded in {hours} hours, {minutes} minutes, and {seconds} seconds."
    )

@bot.command()
async def setpomo(ctx, focus_minutes: int, break_minutes: int):
    # Command to set the pomodoro time by the guild
    if focus_minutes < 1 or break_minutes < 1:
        await ctx.send("Invalid input. Both focus and break periods must be at least 1 minute.")
        return

    pomodoro_settings[ctx.guild.id] = {
        "focus_minutes": focus_minutes,
        "break_minutes": break_minutes,
        "is_focus_time": True
    }

    await ctx.send(f"Pomodoro settings have been updated for this guild:\n" f"Focus Time: {focus_minutes} minutes\n" f"Break Time: {break_minutes} minutes")



@bot.command()
async def startpomo(ctx):
    if ctx.guild.id not in pomodoro_settings:
        await ctx.send("Pomodoro timer has not been set. Use `.setpomo` to set the timer.")
        return

    focus_minutes = pomodoro_settings[ctx.guild.id]["focus_minutes"]
    break_minutes = pomodoro_settings[ctx.guild.id]["break_minutes"]
    is_focus_time = pomodoro_settings[ctx.guild.id]["is_focus_time"]

    notify_channel_id = server_settings[ctx.guild.id].get("setnotify_channel_id")
    if notify_channel_id:
        notify_channel = ctx.guild.get_channel(notify_channel_id)
    else:
        notify_channel = None

    if is_focus_time:
        message = "Focus Time"
        duration_minutes = focus_minutes
    else:
        message = "Break Time"
        duration_minutes = break_minutes

    await ctx.send(f"Starting {message}: {duration_minutes} minutes")

    while duration_minutes > 0:
        await asyncio.sleep(60)  # Sleep for 1 minute (60 seconds)
        duration_minutes -= 1
        await ctx.send(f"{message} - {duration_minutes:02d}:{0:02d}")

    # Toggle between focus and break periods
    pomodoro_settings[ctx.guild.id]["is_focus_time"] = not is_focus_time
    await ctx.send(f"{message} ended. Get ready for the next period.")

@bot.command()
async def setnotify(ctx):
    # Command to set the notification channel for pomodoro updates
    server_settings[ctx.guild.id]["setnotify_channel_id"] = ctx.channel.id
    save_server_settings()
    await ctx.send(f"This channel has been set as the notification channel for pomodoro updates.")

@bot.command()
async def myvctime(ctx):
    # Check if the author is in a voice channel
    if not ctx.author.voice or not ctx.author.voice.channel:
        return await ctx.send("You are not currently in a voice channel.")

    # Continue with the rest of the code
    vc_channel = ctx.author.voice.channel
    time_spent = user_voice_times.get(ctx.guild.id, {}).get(vc_channel.id, {}).get(ctx.author.id)
    if time_spent:
        hours, remainder = divmod(time_spent.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        total_time = f"{hours}:{minutes:02d}"

        # Create the daily status embed
        daily_status_embed = discord.Embed(
            title="Daily Status",
            description=f"You have spent {total_time} hours in {vc_channel.mention} today.",
            color=Permanent_color
        )

        daily_status_embed.set_thumbnail(url="THUMBNAIL_URL_HERE")
        daily_status_embed.add_field(name="⭐  User", value=f"{ctx.author.mention}", inline=True)
        daily_status_embed.add_field(name="-       Status", value="Studying", inline=True)
        daily_status_embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", value="\u200b", inline=False)
        daily_status_embed.set_footer(text="Powered by Arjuna", icon_url="ICON_URL_HERE")

        await ctx.send(embed=daily_status_embed)
    else:
        await ctx.send("You have not spent any time in a voice channel today.")



def generate_todo_list(todo_list):
    formatted_list = "\n".join(f" {index}.ㅤㅤ **{task}**"for index, task in enumerate(todo_list, 1))
    return formatted_list

@bot.command()
async def todolist(ctx):
    user_id = ctx.author.id
    todo_tasks.setdefault(ctx.guild.id, {}).setdefault(user_id, [])
    todo_list = todo_tasks[ctx.guild.id][user_id]

    if not todo_list:
        await ctx.send("Your todo list is empty.")
    else:
        formatted_list = generate_todo_list(todo_list)

        # Add yellow color to the lines
        lines = "\n ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ \n "
        description = f"\n{lines}\n{formatted_list}\n{lines}\n"

        todo_list_embed = discord.Embed(
            title="ㅤㅤㅤㅤㅤToday's Task to Follow ! ",
            description=description,
            color=Permanent_color
        )
        todo_list_embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1080886691067338815/1136553714610602024/2FBCNuy.png")
        print
        todo_list_embed.set_footer(
            text="Powered by Arjuna",
            icon_url="https://cdn.discordapp.com/attachments/1080886691067338815/1136553714610602024/2FBCNuy.png" 
        )
        await ctx.send(embed=todo_list_embed)



@bot.command()
async def todo(ctx, *, task):
    user_id = ctx.author.id
    todo_tasks.setdefault(ctx.guild.id, {}).setdefault(user_id, [])
    todo_tasks[ctx.guild.id][user_id].append(task)
    save_todo_tasks()  # Save todo list data to the file

    # Delete the user's command message
    await ctx.message.delete()

    # Send the response message
    response_message = await ctx.send("Task added to your todo list.")
    await asyncio.sleep(1)

    # Delete the bot's response message after 2 seconds
    await response_message.delete()

@bot.command()
async def todorm(ctx, task_index: int):
    # Command to remove a task from the user's todo list
    user_id = ctx.author.id
    todo_tasks.setdefault(ctx.guild.id, {}).setdefault(user_id, [])
    if 1 <= task_index <= len(todo_tasks[ctx.guild.id][user_id]):
        del todo_tasks[ctx.guild.id][user_id][task_index - 1]
        save_todo_tasks()  # Save todo list data to the file

        # Delete the user's command message
        await ctx.message.delete()

        # Send the response message
        response_message = await ctx.send("Task removed from your todo list.")
        await asyncio.sleep(2)

        # Delete the bot's response message after 2 seconds
        await response_message.delete()
    else:
        # Invalid task index, send an error message and delete it after 2 seconds
        response_message = await ctx.send("Invalid task index. Please check your todo list and try again.")
        await asyncio.sleep(2)
        await ctx.message.delete()
        await response_message.delete()

@bot.command()
async def tocheck(ctx, task_index: int):
    # Command to mark a task as completed in the user's todo list
    user_id = ctx.author.id
    todo_tasks.setdefault(ctx.guild.id, {}).setdefault(user_id, [])
    if 1 <= task_index <= len(todo_tasks[ctx.guild.id][user_id]):
        todo_tasks[ctx.guild.id][user_id][task_index - 1] = f"~~{todo_tasks[ctx.guild.id][user_id][task_index - 1]}~~"
        save_todo_tasks()  # Save todo list data to the file

        # Delete the user's command message
        await ctx.message.delete()

        # Send the response message
        response_message = await ctx.send("Task marked as completed in your todo list.")
        await asyncio.sleep(2)

        # Delete the bot's response message after 2 seconds
        await response_message.delete()
    else:
        # Invalid task index, send an error message and delete it after 2 seconds
        response_message = await ctx.send("Invalid task index. Please check your todo list and try again.")
        await asyncio.sleep(2)
        await ctx.message.delete()
        await response_message.delete()

@bot.command()
async def update_vc_count(guild, vc_channel, member, voice_state):
  vc_count_dict = server_settings[guild.id]["vc_count_dict"]
  vc_count_dict[vc_channel.id] = vc_count_dict.get(vc_channel.id, 0) + 1

  if vc_count_dict[vc_channel.id] == 1:
    role_id = vc_roles[guild.id].get(vc_channel.id)
    if role_id:
      vc_role = guild.get_role(role_id)
      if vc_role:
        await member.add_roles(vc_role)
  elif vc_count_dict[vc_channel.id] == 0:
    role_id = vc_roles[guild.id].get(vc_channel.id)
    if role_id:
      vc_role = guild.get_role(role_id)
      if vc_role:
        await member.remove_roles(vc_role)
  server_settings = load_server_settings()

def create_separator_line():
    return "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

async def format_time(time_spent):
    hours, remainder = divmod(time_spent.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    formatted_time = f"{hours:02}:{minutes:02} hr"
    return formatted_time

@bot.event
async def on_disconnect():
    save_server_settings()

@bot.command()
async def generate_daily_leaderboard(ctx):
    server_id = ctx.guild.id
    if server_id in server_settings:
        daily_leaderboard_channel_id = server_settings[server_id].get("daily_leaderboard_channel")
        if daily_leaderboard_channel_id:
            channel = bot.get_channel(daily_leaderboard_channel_id)
            if channel:
                vc_count_dict = server_settings[server_id].get("vc_count_dict")
                if vc_count_dict:
                    sorted_vc_count = sorted(vc_count_dict.items(), key=lambda x: x[1], reverse=True)
                    if sorted_vc_count:
                        embed = discord.Embed(title="Daily Leaderboard", color=Permanent_color)
                        for index, (user_id, vc_time) in enumerate(sorted_vc_count[:5]):
                            user = ctx.guild.get_member(user_id)
                            if user:
                                rank = index + 1
                                time_str = f"{vc_time // 3600}:{(vc_time // 60) % 60:02d}"
                                embed.add_field(name=f"{rank}. {user.display_name}", value=f"Time: {time_str}", inline=False)
                        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
                        await channel.send(embed=embed)
                    else:
                        await ctx.send("No data to display in the daily leaderboard.")
                else:
                    await ctx.send("No data to display in the daily leaderboard.")
            else:
                await ctx.send("The daily leaderboard channel has not been set.")
        else:
            await ctx.send("The daily leaderboard channel has not been set.")
    else:
        await ctx.send("Server settings not found.")

@bot.command()
async def generate_monthly_leaderboard(ctx):
    server_id = ctx.guild.id
    if server_id in server_settings:
        monthly_leaderboard_channel_id = server_settings[server_id].get("monthly_leaderboard_channel")
        if monthly_leaderboard_channel_id:
            channel = bot.get_channel(monthly_leaderboard_channel_id)
            if channel:
                vc_count_dict = server_settings[server_id].get("vc_count_dict")
                if vc_count_dict:
                    sorted_vc_count = sorted(vc_count_dict.items(), key=lambda x: x[1], reverse=True)
                    if sorted_vc_count:
                        embed = discord.Embed(title="Monthly Leaderboard", color=Permanent_color)
                        for index, (user_id, vc_time) in enumerate(sorted_vc_count):
                            user = ctx.guild.get_member(user_id)
                            if user:
                                rank = index + 1
                                time_str = f"{vc_time // 3600}:{(vc_time // 60) % 60:02d}"
                                embed.add_field(name=f"{rank}. {user.display_name}", value=f"Total Time: {time_str}", inline=False)
                        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.avatar_url)
                        await channel.send(embed=embed)
                    else:
                        await ctx.send("No data to display in the monthly leaderboard.")
                else:
                    await ctx.send("No data to display in the monthly leaderboard.")
            else:
                await ctx.send("The monthly leaderboard channel has not been set.")
        else:
            await ctx.send("The monthly leaderboard channel has not been set.")
    else:
        await ctx.send("Server settings not found.")



@tasks.loop(hours=24)
async def update_leaderboard_channels():
    now = datetime.datetime.now()
    if now.hour == 0 and now.minute == 0:  # At midnight
        for guild in bot.guilds:
            ctx = await bot.get_context(guild)  # Pass the guild instead of message
            await generate_daily_leaderboard(ctx)
            await generate_monthly_leaderboard(ctx)

# Function to calculate the time until the next midnight
def time_until_midnight():
    now = datetime.datetime.now()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if now >= midnight:
        midnight += datetime.timedelta(days=1)
    return (midnight - now).seconds


if __name__ == "__main__":
  keep_alive.keep_alive()
  bot.run('TOKEN')
