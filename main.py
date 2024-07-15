import logging
import json
import discord
from discord.ext import commands
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import asyncio
from datetime import datetime
from keep_alive import keep_alive

BOT_VERSION = "1.8"  # Bot version

logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(name)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

client = commands.Bot(command_prefix='!', intents=intents)
client.help_command = None

tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-large")
model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-large")

chat_histories = {}

def save_designated_channels(designated_channels):
    with open('designated_channels.json', 'w') as file:
        json.dump(designated_channels, file, indent=4)
    logging.info("Designated channels saved to file.")

def load_designated_channels():
    try:
        with open('designated_channels.json', 'r') as file:
            logging.info("Designated channels loaded from file.")
            return json.load(file)
    except FileNotFoundError:
        logging.warning("Designated channels file not found. Starting with an empty dictionary.")
        return {}

designated_channels = load_designated_channels()

def respond_to_message(message, text):
    user_id = message.author.id
    chat_history = chat_histories.get(user_id, torch.tensor([]))
    new_user_input_ids = tokenizer.encode(text + tokenizer.eos_token, return_tensors='pt')

    logging.info(f"User input: {text}")
    logging.info(f"New user input IDs: {new_user_input_ids}")

    if chat_history.numel() > 0:
        bot_input_ids = torch.cat([chat_history, new_user_input_ids], dim=-1)
        logging.info("Appended new user input to existing chat history.")
    else:
        bot_input_ids = new_user_input_ids
        logging.info("Starting new chat history with user input.")

    attention_mask = torch.ones(bot_input_ids.shape, dtype=torch.long)

    chat_histories[user_id] = model.generate(
        bot_input_ids,
        max_length=250,  # Adjusted max length for longer responses
        pad_token_id=tokenizer.eos_token_id,
        no_repeat_ngram_size=3,
        do_sample=True,
        top_k=5000,
        top_p=0.95,
        temperature=1,  # Increased temperature for more diverse responses
        attention_mask=attention_mask
    )

    response = tokenizer.decode(chat_histories[user_id][:, bot_input_ids.shape[-1]:][0], skip_special_tokens=True)
    logging.info(f"Generated response: {response}")

    if len(response.strip()) < 3 or response.lower() in ["no", "yes", "sure"]:
        response = "Can you please rephrase?"
        logging.info("Response was too short or unclear, using fallback response.")

    return response

@client.command()
async def servercount(ctx):
    num_servers = len(client.guilds)
    logging.info(f"Server count command used. Bot is in {num_servers} servers.")
    await ctx.send(f'This bot is in {num_servers} servers.')

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f'{len(client.guilds)} servers'))
    logging.info("Bot is ready and displaying the server count!")

@client.command()
async def help(ctx):
    logging.info("Help command used.")
    embed = discord.Embed(
        title="Bot Help",
        description="Learn how to interact with the bot and use its commands.",
        color=discord.Color.blue()
    )
    embed.add_field(name="!setchannel", value="Sets a designated channel for the bot to respond to messages.", inline=False)
    embed.add_field(name="!setup", value="Automatically sets the current channel as the designated channel.", inline=False)
    embed.add_field(name="!help", value="Displays this help message.", inline=False)
    embed.add_field(name="Operating the Bot", value="Mention the bot or reply to its messages to interact with it.", inline=False)
    embed.set_footer(text="Bot created using Discord.py and GPT-2. Enjoy chatting!")
    await ctx.send(embed=embed)

@client.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    guild_id = str(ctx.guild.id)
    channel_id = str(ctx.channel.id)
    logging.info(f"Setup command used in guild {guild_id}, channel {channel_id}.")
    if guild_id not in designated_channels:
        designated_channels[guild_id] = []
    if channel_id not in designated_channels[guild_id]:
        designated_channels[guild_id].append(channel_id)
        save_designated_channels(designated_channels)
        embed = discord.Embed(
            title="Setup Complete",
            description=f"The bot is now ready to use in {ctx.channel.mention}.",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
        logging.info(f"Channel {channel_id} added to designated channels.")
    else:
        await ctx.send(f"{ctx.channel.mention} is already a designated channel in this server.")
        logging.info(f"Channel {channel_id} was already a designated channel.")

@client.command()
@commands.has_permissions(administrator=True)
async def setchannel(ctx, channel: discord.TextChannel):
    guild_id = str(ctx.guild.id)
    channel_id = str(channel.id)
    logging.info(f"Setchannel command used to set channel {channel_id} in guild {guild_id}.")
    if guild_id not in designated_channels:
        designated_channels[guild_id] = []
    if channel_id not in designated_channels[guild_id]:
        designated_channels[guild_id].append(channel_id)
        save_designated_channels(designated_channels)
        await ctx.send(f"Designated channel set to {channel.mention}")
        logging.info(f"Channel {channel_id} added to designated channels.")
    else:
        await ctx.send(f"{channel.mention} is already a designated channel in this server.")
        logging.info(f"Channel {channel_id} was already a designated channel.")

@setchannel.error
async def setchannel_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You do not have the required permissions to use this command.")
        logging.warning("User attempted to use setchannel command without permissions.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Invalid channel specified. Please mention a valid text channel.")
        logging.warning("User provided invalid channel argument in setchannel command.")
    else:
        await ctx.send(f"An error occurred: {error}")
        logging.error(f"An error occurred in setchannel command: {error}")


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    guild_id = str(message.guild.id)
    channel_id = str(message.channel.id)
    if guild_id in designated_channels and channel_id in designated_channels[guild_id]:
        if client.user.mentioned_in(message) or message.reference:
            logging.info(f"Bot was mentioned or replied to by user {message.author.id} in guild {guild_id}, channel {channel_id}: {message.content}")
            async with message.channel.typing():
                text = message.clean_content.replace(f"@{client.user.name}", "").strip()
                response = respond_to_message(message, text)
                await asyncio.sleep(len(response) * 0.05)
                embed = discord.Embed(
                    title="Chatbot Response",
                    description=response,
                    color=discord.Color.blue()
                )
                embed.set_footer(text=f"Response generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                if message.reference:
                    await message.reply(embed=embed)
                else:
                    await message.channel.send(f"{message.author.mention}", embed=embed)
            logging.info(f"Sent response to user {message.author.id}: {response}")
    await client.process_commands(message)

# Run the bot
keep_alive()
client.run('your-token')

