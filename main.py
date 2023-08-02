import discord
from discord.ext import commands, tasks
import datetime
import pytz
import asyncio
import random

# Replace 'YOUR_BOT_TOKEN' with your actual bot token
bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

# Timezone settings (replace 'Asia/Kolkata' with your timezone if needed)
IST = pytz.timezone('Asia/Kolkata')
HH, MM = 18, 0  # Hour and minute in 24-hour format for the daily leaderboard upload time

# Dictionary to store server settings
server_settings = {}

# Dictionary to store video usage data for each guild
video_usage_data = {}

# Dictionary to store VC roles for multiple VCs
vc_roles = {}

# Define the time for leaderboard upload in IST (replace 'HH' with the hour and 'MM' with the minute)
upload_time = datetime.time(hour=HH, minute=MM)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')


@bot.event
async def on_guild_join(guild):
    # Initialize server settings when the bot joins a new guild
    server_settings[guild.id] = {
        "vc_channels": [],
        "message_channel_id": None,
        "vc_count_dict": {},
        "top_user_role": None,
        "embed_color": discord.Color.blue().value,
        "mercy_time": 30,
        "monthly_top_role": None
    }
    vc_roles[guild.id] = {}


@bot.event
async def on_command(ctx):
    # Send a message prefixing each bot-generated message
    await ctx.send("Hey there! For a list of available commands, use `!help`.")


@bot.command()
async def help(ctx):
    # Display the help command with dedicated sections for guild-specific commands
    help_embed = discord.Embed(title="Study Bot Commands", color=discord.Color.blurple())
    help_embed.add_field(name="Server Settings", value="Commands for managing server settings:", inline=False)
    help_embed.add_field(name="!set_vc_channel <channel_id>", value="Set a VC channel for tracking.", inline=False)
    help_embed.add_field(name="!remove_vc_channel <channel_id>", value="Remove a VC channel from tracking.", inline=False)
    help_embed.add_field(name="!set_message_channel <channel_id>", value="Set the message channel for daily leaderboards.", inline=False)
    help_embed.add_field(name="!set_embed_color <color>", value="Set the embed color for the leaderboard.", inline=False)
    help_embed.add_field(name="!set_mercy_time <seconds>", value="Set the mercy time interval.", inline=False)
    help_embed.add_field(name="!set_monthly_top_role <role>", value="Set the monthly top role.", inline=False)

    help_embed.add_field(name="VC Roles", value="Commands for managing roles for VC channels:", inline=False)
    help_embed.add_field(name="!set_vc_role <vc_channel> <vc_role>", value="Set a role for a VC channel.", inline=False)
    help_embed.add_field(name="!remove_vc_role <vc_channel>", value="Remove the role set for a VC channel.", inline=False)

    help_embed.add_field(name="Study Bot Features", value="Commands for the study bot features:", inline=False)
    help_embed.add_field(name="!daily_leaderboard", value="Manually trigger the daily leaderboard upload.", inline=False)
    help_embed.add_field(name="!monthly_leaderboard", value="Display the monthly study time leaderboard.", inline=False)
    help_embed.add_field(name="!stats", value="Display server statistics.", inline=False)

    await ctx.send(embed=help_embed)


@bot.command()
async def set_vc_channel(ctx, channel_id: int):
    # Command to set a VC channel for tracking (only server admins can use this)
    if ctx.author.guild_permissions.administrator:
        vc_channels = server_settings[ctx.guild.id].get("vc_channels", [])
        if channel_id not in vc_channels:
            vc_channels.append(channel_id)
            server_settings[ctx.guild.id]["vc_channels"] = vc_channels
            await ctx.send(f"VC channel <#{channel_id}> added for tracking.")
        else:
            await ctx.send("This VC channel is already being tracked.")
    else:
        await ctx.send("You don't have the required permissions to use this command.")


@bot.command()
async def remove_vc_channel(ctx, channel_id: int):
    # Command to remove a VC channel from tracking (only server admins can use this)
    if ctx.author.guild_permissions.administrator:
        vc_channels = server_settings[ctx.guild.id].get("vc_channels", [])
        if channel_id in vc_channels:
            vc_channels.remove(channel_id)
            server_settings[ctx.guild.id]["vc_channels"] = vc_channels
            await ctx.send(f"VC channel <#{channel_id}> removed from tracking.")
        else:
            await ctx.send("This VC channel is not being tracked.")
    else:
        await ctx.send("You don't have the required permissions to use this command.")


@bot.command()
async def set_message_channel(ctx, channel_id: int):
    # Command to set the message channel for sending daily leaderboards (only server admins can use this)
    if ctx.author.guild_permissions.administrator:
        server_settings[ctx.guild.id]["message_channel_id"] = channel_id
        await ctx.send(f"Message channel set to <#{channel_id}> for daily leaderboards.")
    else:
        await ctx.send("You don't have the required permissions to use this command.")


@bot.command()
async def set_embed_color(ctx, color: str):
    # Command to set the embed color for the leaderboard (only server admins can use this)
    if ctx.author.guild_permissions.administrator:
        try:
            color_value = int(color, 16)
            server_settings[ctx.guild.id]["embed_color"] = color_value
            await ctx.send(f"Embed color set to #{color}.")
        except ValueError:
            await ctx.send("Invalid color format. Please use a valid hexadecimal color (e.g., FF0000 for red).")
    else:
        await ctx.send("You don't have the required permissions to use this command.")


@bot.command()
async def set_mercy_time(ctx, mercy_time: int):
    # Command to set the mercy time interval (only server admins can use this)
    if ctx.author.guild_permissions.administrator:
        server_settings[ctx.guild.id]["mercy_time"] = mercy_time
        await ctx.send(f"Mercy time interval set to {mercy_time} seconds.")
    else:
        await ctx.send("You don't have the required permissions to use this command.")


@bot.command()
async def set_monthly_top_role(ctx, role: discord.Role):
    # Command to set the monthly top role (only server admins can use this)
    if ctx.author.guild_permissions.administrator:
        server_settings[ctx.guild.id]["monthly_top_role"] = role.id
        await ctx.send(f"Monthly top role set to {role.name}.")
    else:
        await ctx.send("You don't have the required permissions to use this command.")


@bot.command()
async def daily_leaderboard(ctx):
    # Command to manually trigger the daily leaderboard upload (only server admins can use this)
    if ctx.author.guild_permissions.administrator:
        await update_leaderboards(ctx.guild)
    else:
        await ctx.send("You don't have the required permissions to use this command.")


async def update_leaderboards(guild):
    # Function to update the daily leaderboards for the guild
    settings = server_settings.get(guild.id)
    if not settings:
        return

    vc_channels = settings.get("vc_channels", [])
    message_channel_id = settings.get("message_channel_id")
    vc_count_dict = settings.get("vc_count_dict")
    top_user_role_id = settings.get("top_user_role")
    embed_color = settings.get("embed_color", discord.Color.blue().value)

    if not vc_channels or not message_channel_id or not vc_count_dict:
        return

    # Sort the VC count dictionary by values (descending)
    sorted_vc_count = sorted(vc_count_dict.items(), key=lambda item: item[1], reverse=True)

    # Prepare the daily leaderboard message
    leaderboard_embed = discord.Embed(title="Daily Study Time Leaderboard", color=embed_color)

    for i, (member_id, vc_time) in enumerate(sorted_vc_count[:6], 1):
        member = guild.get_member(member_id)
        if member and member.voice and member.voice.channel and member.voice.channel.id in vc_channels:
            leaderboard_embed.add_field(name=f"{i}. {member.display_name}", value=f"{vc_time // 60:02d}:{vc_time % 60:02d} minutes", inline=False)

    message_channel = guild.get_channel(message_channel_id)
    await message_channel.send(embed=leaderboard_embed)


@tasks.loop(hours=24)
async def daily_upload():
    # Loop to trigger the daily leaderboard upload
    now = datetime.datetime.now(IST)
    if now.time() == upload_time:
        for guild in bot.guilds:
            await update_leaderboards(guild)


def get_vc_channel(member):
    # Function to get the VC channel where the member is currently connected
    if member.voice and member.voice.channel:
        return member.voice.channel.id
    return None


@bot.event
async def on_voice_state_update(member, before, after):
    if not member.bot:
        if before.channel != after.channel:
            # If the member was in a VC channel, update the VC count and check for video usage
            if before.channel:
                await update_vc_count(before.channel.guild, before.channel, member, before)

            # If the member is now in a VC channel, update the VC count and check for video usage
            if after.channel:
                await update_vc_count(after.channel.guild, after.channel, member, after)

                # Check for video usage after 8 seconds of joining the study VC
                if after.channel.id in server_settings[member.guild.id]["vc_channels"] and after.channel.id not in video_usage_data.get(member.guild.id, {}):
                    await asyncio.sleep(8)  # Wait for 8 seconds
                    vc_state = member.guild.voice_client
                    if vc_state and vc_state.is_playing() and not member.voice.self_video:
                        video_usage_data.setdefault(member.guild.id, {})[after.channel.id] = member.id
                        await member.send("Your video is not allowed in the study VC. Please turn it off or you will be kicked.")


async def update_vc_count(guild, vc_channel, member, voice_state):
    # Function to update the VC count for the given member and channel
    settings = server_settings.get(guild.id)
    if not settings:
        return

    vc_count_dict = settings.get("vc_count_dict")
    if not vc_count_dict:
        return

    vc_time = vc_count_dict.get(member.id, 0)
    current_time = datetime.datetime.now(IST)

    if voice_state.channel and voice_state.channel == vc_channel:
        if not member.bot:
            # Calculate the time spent in the VC
            vc_time += (current_time - voice_state.channel.connect_time).seconds
            vc_count_dict[member.id] = vc_time
    else:
        # Calculate the time spent in the VC before disconnecting
        vc_time += (current_time - voice_state.channel.connect_time).seconds
        vc_count_dict[member.id] = vc_time


@tasks.loop(seconds=1)
async def check_video_usage():
    # Loop to check for video usage in the study VCs and kick if required
    for guild_id, guild_data in video_usage_data.items():
        guild = bot.get_guild(guild_id)
        mercy_time = server_settings[guild_id]["mercy_time"]

        for channel_id, user_id in guild_data.items():
            vc_channel = guild.get_channel(channel_id)
            if not vc_channel:
                continue

            member = guild.get_member(user_id)
            if not member:
                continue

            vc_state = guild.voice_client
            if vc_state and vc_state.channel == vc_channel and vc_state.is_playing():
                if not member.voice.self_video:
                    if (datetime.datetime.now() - vc_state.connect_time).seconds >= mercy_time:
                        del video_usage_data[guild_id][channel_id]
                        await member.send("You were kicked from the study VC because your video was on for too long.")
                        await vc_state.disconnect()
                else:
                    if vc_state.is_playing():
                        del video_usage_data[guild_id][channel_id]
                        await member.send("You were kicked from the study VC because videos are not allowed.")
                        await vc_state.disconnect()


@tasks.loop(minutes=25)
async def check_pomodoro_loop():
    # Loop to check and send a message when a pomodoro session is completed
    for guild_id, guild_data in server_settings.items():
        vc_channels = guild_data.get("vc_channels", [])
        if not vc_channels:
            continue

        for channel_id in vc_channels:
            vc_channel = bot.get_channel(channel_id)
            vc_state = vc_channel.guild.voice_client

            if vc_state and vc_state.is_playing():
                try:
                    await vc_channel.send("The current pomodoro session has ended. Take a break and be back for the next session.")
                except discord.Forbidden:
                    pass


@tasks.loop(hours=24)
async def erase_data():
    # Loop to erase unnecessary data after two days
    for guild_id, guild_data in video_usage_data.items():
        two_days_ago = datetime.datetime.now() - datetime.timedelta(days=2)
        guild_data_copy = guild_data.copy()
        for channel_id, timestamp in guild_data_copy.items():
            if timestamp < two_days_ago.timestamp():
                del guild_data[channel_id]


@bot.command()
async def monthly_leaderboard(ctx):
    # Command to display the monthly leaderboard
    settings = server_settings.get(ctx.guild.id)
    if not settings:
        return

    vc_channels = settings.get("vc_channels", [])
    vc_count_dict = settings.get("vc_count_dict")
    top_user_role_id = settings.get("top_user_role")
    embed_color = settings.get("embed_color", discord.Color.blue().value)

    if not vc_channels or not vc_count_dict:
        return

    # Sort the VC count dictionary by values (descending)
    sorted_vc_count = sorted(vc_count_dict.items(), key=lambda item: item[1], reverse=True)

    # Prepare the monthly leaderboard message
    leaderboard_embed = discord.Embed(title="Monthly Study Time Leaderboard", color=embed_color)

    top_members = []
    for i, (member_id, vc_time) in enumerate(sorted_vc_count[:10], 1):
        member = ctx.guild.get_member(member_id)
        if member and get_vc_channel(member) in vc_channels:
            top_members.append(member)

    center_member = top_members[0]
    center_pfp = center_member.avatar_url_as(size=256)

    leaderboard_embed.set_author(name=f"{center_member.display_name} - {sorted_vc_count[0][1] // 60:02d}:{sorted_vc_count[0][1] % 60:02d} hours")
    leaderboard_embed.set_image(url=center_pfp)

    member_chunk_size = 3  # Number of members in each chunk
    member_chunks = [top_members[i:i + member_chunk_size] for i in range(1, len(top_members), member_chunk_size)]

    for i, chunk in enumerate(member_chunks):
        chunk_str = "\n".join(f"{member.display_name} - {sorted_vc_count[top_members.index(member)][1] // 60:02d}:{sorted_vc_count[top_members.index(member)][1] % 60:02d} hours" for member in chunk)
        chunk_pfps = "\n".join(member.avatar_url_as(size=64) for member in chunk)

        # Add padding between the chunks
        if i > 0:
            leaderboard_embed.add_field(name="\u200b", value="\u200b", inline=False)

        leaderboard_embed.add_field(name="\u200b", value=chunk_str, inline=True)
        leaderboard_embed.set_thumbnail(url=chunk_pfps)

    await ctx.send(embed=leaderboard_embed)


@bot.command()
async def set_vc_role(ctx, vc_channel: discord.VoiceChannel, vc_role: discord.Role):
    # Command to set a role for a specific VC channel (only server admins can use this)
    if ctx.author.guild_permissions.administrator:
        if vc_channel.id in server_settings[ctx.guild.id]["vc_channels"]:
            vc_roles[ctx.guild.id][vc_channel.id] = vc_role.id
            await ctx.send(f"Role '{vc_role.name}' is set for VC channel '{vc_channel.name}'.")
        else:
            await ctx.send("This VC channel is not being tracked.")
    else:
        await ctx.send("You don't have the required permissions to use this command.")


@bot.command()
async def remove_vc_role(ctx, vc_channel: discord.VoiceChannel):
    # Command to remove the role set for a specific VC channel (only server admins can use this)
    if ctx.author.guild_permissions.administrator:
        if vc_channel.id in vc_roles.get(ctx.guild.id, {}):
            del vc_roles[ctx.guild.id][vc_channel.id]
            await ctx.send(f"Role for VC channel '{vc_channel.name}' removed.")
        else:
            await ctx.send("No role is set for this VC channel.")
    else:
        await ctx.send("You don't have the required permissions to use this command.")


@bot.command()
async def stats(ctx):
    # Command to display server statistics
    settings = server_settings.get(ctx.guild.id)
    if not settings:
        await ctx.send("Server statistics are not available.")
        return

    vc_channels_count = len(settings.get("vc_channels", []))
    vc_count_dict = settings.get("vc_count_dict", {})
    member_count = len(vc_count_dict)

    stats_embed = discord.Embed(title="Server Statistics", color=discord.Color.green())

    stats_embed.add_field(name="Total VC Channels Tracked", value=vc_channels_count)
    stats_embed.add_field(name="Total Members Tracked", value=member_count)

    await ctx.send(embed=stats_embed)


# Start the leaderboard update loop, daily upload loop, video usage check loop, erase data loop, and the bot
update_leaderboards.start()
daily_upload.start()
check_pomodoro_loop.start()
check_video_usage.start()
erase_data.start()

# Replace 'YOUR_BOT_TOKEN' with your actual bot token
bot.run('YOUR_BOT_TOKEN')
