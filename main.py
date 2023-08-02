import discord
from discord.ext import commands, tasks
import datetime
import pytz
import asyncio
import random
import keep_alive
import os
import json
bot = commands.Bot(command_prefix='.', intents=discord.Intents.all())

# Dictionary to store server-specific settings
server_settings = {}
vc_roles = {}
todo_tasks = {}
IST = pytz.timezone('Asia/Kolkata')
HH, MM = 0, 0  # Set the time (in 24-hour format) when daily leaderboard should be uploaded
upload_time = datetime.time(HH, MM)
if os.path.exists("server_settings.json"):
    with open("server_settings.json", "r") as file:
        server_settings = json.load(file)
else:
    server_settings = {}



@bot.event
async def on_ready():
  print(f"Logged in as {bot.user.name}")
  for guild in bot.guilds:
    if guild.id not in server_settings:
      server_settings[guild.id] = {
          "vc_channels": [],
          "message_channel_id": None,
          "embed_color": discord.Color.dark_blue(),
          "mercy_time": 5,
          "monthly_top_role": None,
          "vc_count_dict": {}
      }
      vc_roles[guild.id] = {}
  topdaily.start()


categories = {
    "Leaderboard": [
        ".settracking <vc_channel>",
        ".removetracking <vc_channel>",
        ".setdailyleaderboardchannel <message_channel>",
        ".setembedcolor <color>",
        ".setmercytime <minutes>",
        ".setmonthlytoprole <role_id>",
        ".topdaily",
        ".topmonthly",
        ".updateleaderboards <daily/monthly>",
    ],
    "Study VC": [
        ".setvcrole <vc_channel> <vc_role>",
        ".removevcrole <vc_channel>",
    ],
    "Pomodoro": [
        ".svctime",
        ".todolist",
        ".todo <task>",
        ".todorm <task_index>",
        ".tocheck <task_index>",
    ]
}


@bot.command()
async def bot_help(ctx, category=None):
    if category is None:
        # If no category is provided, show the general help message
        bot_avatar_url = bot.user.avatar_url_as(format="png", size=128)

        help_embed = discord.Embed(title="Bot Commands",
                                   color=server_settings[ctx.guild.id]["embed_color"])  # Use the server-specific embed color

        help_embed.set_thumbnail(url=bot_avatar_url)
        help_embed.set_author(name=bot.user.name, icon_url=bot_avatar_url)
        help_embed.set_footer(text="Powered by Garuda", icon_url=bot_avatar_url)

        help_embed.description = "> **The Garuda will help your hardwork shine throughout your studies with the help of its multitasking and easy functioning.**"

        for category_name, category_commands in categories.items():
            commands_list = "\n".join(category_commands)
            help_embed.add_field(name=category_name,
                                 value=commands_list,
                                 inline=False)

        await ctx.send(embed=help_embed)

    else:
        # If a category is provided, show the commands in that category
        category = category.capitalize()
        if category in categories:
            bot_avatar_url = bot.user.avatar_url_as(format="png", size=128)

            category_embed = discord.Embed(
                title=f"{category} Commands", color=server_settings[ctx.guild.id]["embed_color"])  # Use the server-specific embed color
            category_embed.set_thumbnail(url=bot_avatar_url)
            category_embed.set_author(name=bot.user.name,
                                      icon_url=bot_avatar_url)
            category_embed.set_footer(text="Powered by Garuda", icon_url=bot_avatar_url)

            category_commands = categories[category]
            commands_list = "\n".join(category_commands)

            category_embed.description = "Commands related to {}:\n{}".format(
                category, commands_list)

            await ctx.send(embed=category_embed)
        else:
            await ctx.send("Invalid category. Use `.bot_help` to see all commands.")



def get_command_description(command):
  # Add a cool description for each command here
  command_descriptions = {
      ".settracking <vc_channel>": "Set a VC channel for tracking.",
      ".removetracking <vc_channel>": "Remove a VC channel from tracking.",
      ".setdailyleaderboardchannel <message_channel>":
      "Set the channel for daily leaderboards.",
      ".setembedcolor <color>": "Set the embed color for the leaderboard.",
      # Add other command descriptions...
  }
  return command_descriptions.get(command, "No description available.")


@bot.command()
async def settracking(ctx, vc_channel: discord.VoiceChannel):
  # Command to set a VC channel for tracking (only server admins can use this)
  if ctx.author.guild_permissions.administrator:
    server_settings[ctx.guild.id]["vc_channels"].append(vc_channel.id)
    await ctx.send(f"VC channel '{vc_channel.name}' is now set for tracking.")
  else:
    await ctx.send(
        "You don't have the required permissions to use this command.")


@bot.command()
async def removetracking(ctx, vc_channel: discord.VoiceChannel):
  # Command to remove a VC channel from tracking (only server admins can use this)
  if ctx.author.guild_permissions.administrator:
    if vc_channel.id in server_settings[ctx.guild.id]["vc_channels"]:
      server_settings[ctx.guild.id]["vc_channels"].remove(vc_channel.id)
      await ctx.send(
          f"VC channel '{vc_channel.name}' has been removed from tracking.")
    else:
      await ctx.send("This VC channel is not being tracked.")
  else:
    await ctx.send(
        "You don't have the required permissions to use this command.")


@bot.command()
async def setdailyleaderboardchannel(ctx,
                                     message_channel: discord.TextChannel):
  # Command to set the message channel for daily leaderboards (only server admins can use this)
  if ctx.author.guild_permissions.administrator:
    server_settings[ctx.guild.id]["message_channel_id"] = message_channel.id
    await ctx.send(
        f"The daily leaderboard channel has been set to '{message_channel.mention}'."
    )
  else:
    await ctx.send(
        "You don't have the required permissions to use this command.")


@bot.command()
@commands.has_permissions(administrator=True)
async def setembedcolor(ctx, color: discord.Color):
    # Command to set the embed color for the leaderboard (only server administrators can use this)
    server_settings[ctx.guild.id]["embed_color"] = color.value  # Save the color value as an integer
    save_server_settings()
    await ctx.send(
        f"The embed color for the leaderboard has been updated to the specified color."
    )
def save_server_settings():
    # Save the server settings to a JSON file
    with open("server_settings.json", "w") as file:
        json.dump(server_settings, file)


@bot.command()
async def setmercytime(ctx, minutes: int):
  # Command to set the mercy time for the leaderboard (only server admins can use this)
  if ctx.author.guild_permissions.administrator:
    server_settings[ctx.guild.id]["mercy_time"] = minutes
    await ctx.send(
        f"The mercy time for the leaderboard has been set to {minutes} minutes."
    )
  else:
    await ctx.send(
        "You don't have the required permissions to use this command.")


@bot.command()
async def setmonthlytoprole(ctx, role: discord.Role):
  # Command to set the role for the monthly top user (only server admins can use this)
  if ctx.author.guild_permissions.administrator:
    server_settings[ctx.guild.id]["monthly_top_role"] = role.id
    await ctx.send(
        f"The role '{role.name}' is now set as the monthly top user role.")
  else:
    await ctx.send(
        "You don't have the required permissions to use this command.")


@bot.command()
async def topdaily(ctx):
  # Command to show the top users of the day
  await updateleaderboards(ctx, "daily")


@bot.command()
async def updateleaderboards(ctx, leaderboard_type):
  # Command to update and display the daily or monthly leaderboard
  if leaderboard_type.lower() == "daily":
    await topdaily(ctx)
  elif leaderboard_type.lower() == "monthly":
    await topmonthly(ctx)
  else:
    await ctx.send(
        "Invalid leaderboard type. Use `.topdaily` or `.topmonthly`.")


@tasks.loop(minutes=5)
async def topdaily(ctx):
  # Loop to upload the daily leaderboard at the specified time
  current_time = datetime.datetime.now(IST).time()
  if current_time.hour == HH and current_time.minute == MM:
    message_channel_id = server_settings[ctx.guild.id]["message_channel_id"]
    if message_channel_id:
      message_channel = ctx.guild.get_channel(message_channel_id)
      if message_channel:
        await topdaily(ctx.guild, message_channel)


@bot.command()
async def setvcrole(ctx, vc_channel: discord.VoiceChannel,
                    vc_role: discord.Role):
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
async def svctime(ctx):
  # Command to display the remaining time for the next pomodoro session
  current_time = datetime.datetime.now(IST).time()
  time_left = datetime.datetime.combine(
      datetime.date.today(), upload_time) - datetime.datetime.combine(
          datetime.date.today(), current_time)
  hours, minutes, seconds = str(time_left).split(":")
  await ctx.send(
      f"The next pomodoro session will start in {hours} hours, {minutes} minutes."
  )


@bot.command()
async def todolist(ctx):
  # Command to display the current todo list of the user
  user_id = ctx.author.id
  todo_tasks.setdefault(ctx.guild.id, {}).setdefault(user_id, [])
  if not todo_tasks[ctx.guild.id][user_id]:
    await ctx.send("Your todo list is empty.")
  else:
    todo_list_embed = discord.Embed(
        title="Todo List", color=server_settings[ctx.guild.id]["embed_color"])
    for index, task in enumerate(todo_tasks[ctx.guild.id][user_id]):
      todo_list_embed.add_field(name=f"Task {index + 1}",
                                value=task,
                                inline=False)
    await ctx.send(embed=todo_list_embed)


@bot.command()
async def todo(ctx, *, task):
  # Command to add a new task to the user's todo list
  user_id = ctx.author.id
  todo_tasks.setdefault(ctx.guild.id, {}).setdefault(user_id, [])
  todo_tasks[ctx.guild.id][user_id].append(task)
  await ctx.send("Task added to your todo list.")


@bot.command()
async def todorm(ctx, task_index: int):
  # Command to remove a task from the user's todo list
  user_id = ctx.author.id
  todo_tasks.setdefault(ctx.guild.id, {}).setdefault(user_id, [])
  if 1 <= task_index <= len(todo_tasks[ctx.guild.id][user_id]):
    del todo_tasks[ctx.guild.id][user_id][task_index - 1]
    await ctx.send("Task removed from your todo list.")
  else:
    await ctx.send(
        "Invalid task index. Please check your todo list and try again.")


@bot.command()
async def tocheck(ctx, task_index: int):
  # Command to mark a task as completed in the user's todo list
  user_id = ctx.author.id
  todo_tasks.setdefault(ctx.guild.id, {}).setdefault(user_id, [])
  if 1 <= task_index <= len(todo_tasks[ctx.guild.id][user_id]):
    todo_tasks[ctx.guild.id][user_id][
        task_index -
        1] = f"~~{todo_tasks[ctx.guild.id][user_id][task_index - 1]}~~"
    await ctx.send("Task marked as completed in your todo list.")
  else:
    await ctx.send(
        "Invalid task index. Please check your todo list and try again.")


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


@tasks.loop(minutes=5)
async def topdaily():
  # Loop to upload the daily leaderboard at the specified time
  current_time = datetime.datetime.now(IST).time()
  if current_time.hour == HH and current_time.minute == MM:
    for guild_id, settings in server_settings.items():
      message_channel_id = settings["message_channel_id"]
      if message_channel_id:
        guild = bot.get_guild(guild_id)
        message_channel = guild.get_channel(message_channel_id)
        if message_channel:
          await generate_daily_leaderboard(guild, message_channel)


async def generate_daily_leaderboard(guild, message_channel):
  # Generate and send the daily leaderboard
  vc_count_dict = server_settings[guild.id]["vc_count_dict"]
  sorted_vc_channels = sorted(server_settings[guild.id]["vc_channels"],
                              key=lambda x: vc_count_dict.get(x, 0),
                              reverse=True)

  daily_leaderboard_embed = discord.Embed(
      title="Daily Leaderboard",
      color=server_settings[guild.id]["embed_color"])

  if sorted_vc_channels:
    for index, vc_channel_id in enumerate(sorted_vc_channels, 1):
      vc_channel = guild.get_channel(vc_channel_id)
      if vc_channel:
        vc_count = vc_count_dict.get(vc_channel_id, 0)
        daily_leaderboard_embed.add_field(
            name=f"#{index} {vc_channel.name}",
            value=f"**Participants:** {vc_count}",
            inline=False)
  else:
    daily_leaderboard_embed.add_field(
        name="No VC channels being tracked",
        value="Use `.settracking` to set VC channels for tracking.",
        inline=False)

  await message_channel.send(embed=daily_leaderboard_embed)


@bot.command()
async def topmonthly(ctx):
  # Command to show the top users of the month
  await generate_monthly_leaderboard(ctx.guild, ctx.channel)


async def generate_monthly_leaderboard(guild, message_channel):
  # Generate and send the monthly leaderboard
  vc_count_dict = server_settings[guild.id]["vc_count_dict"]
  sorted_vc_channels = sorted(server_settings[guild.id]["vc_channels"],
                              key=lambda x: vc_count_dict.get(x, 0),
                              reverse=True)

  monthly_leaderboard_embed = discord.Embed(
      title="Monthly Leaderboard",
      color=server_settings[guild.id]["embed_color"])

  if sorted_vc_channels:
    for index, vc_channel_id in enumerate(sorted_vc_channels, 1):
      vc_channel = guild.get_channel(vc_channel_id)
      if vc_channel:
        vc_count = vc_count_dict.get(vc_channel_id, 0)
        monthly_leaderboard_embed.add_field(
            name=f"#{index} {vc_channel.name}",
            value=f"**Participants:** {vc_count}",
            inline=False)
  else:
    monthly_leaderboard_embed.add_field(
        name="No VC channels being tracked",
        value="Use `.settracking` to set VC channels for tracking.",
        inline=False)

  await message_channel.send(embed=monthly_leaderboard_embed)


keep_alive.keep_alive()
bot.run('token')
