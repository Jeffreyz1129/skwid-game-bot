import discord
import topgg
from discord.ext import commands
import asyncio
from discord_components import *
from src.constants.timeouts import honeycomb_reply_timeout
from src.constants.scramble_words import words, easy_words
from src.constants.urls import bot_icon, bot_vote_url
from src.constants.vars import TOPGG_TOKEN
import random
from src.constants.games import games


def scramble(word) -> str:
    """Scrambles a word"""

    scrambled_word = ""
    word = list(word)

    while word:
        random_index = random.randint(0, len(word) - 1)
        scrambled_word += word[random_index]
        word.pop(random_index)

    return scrambled_word


async def honey_solo(dbl_client: topgg.DBLClient, client: commands.Bot, ctx: commands.Context, word: str,
                     user: discord.User):
    voted = await dbl_client.get_user_vote(user.id)
    add_on_text = "Vote the bot to get an easier word using the button below and then dm `voted`."
    vote_button = Button(label="Vote", url=bot_vote_url, style=ButtonStyle.URL)
    scrambled_word = scramble(word)
    await user.create_dm()
    if voted:
        await user.dm_channel.send(f"Your word is `{scrambled_word}`. You have `{honeycomb_reply_timeout}s`")
    else:
        await user.dm_channel.send(f"Your word is `{scrambled_word}`. You have `{honeycomb_reply_timeout}s`"
                                   f"\n{add_on_text}", components=[vote_button])
    try:
        msg = await client.wait_for('message', timeout=honeycomb_reply_timeout,
                                    check=lambda x: x.author == user and isinstance(x.channel, discord.DMChannel))
    except asyncio.TimeoutError:
        await ctx.send(f"{user.mention} Took too long to respond. Player Eliminated!")
        return None
    else:
        if msg.content.lower() == "voted" and not voted:
            _voted = await dbl_client.get_user_vote(user.id)
            if _voted:
                return await honey_solo(dbl_client, client, ctx, random.choice(easy_words), user)
        if msg.content.lower() == word.lower():
            await user.dm_channel.send("That is correct!")
            return user
        else:
            await user.dm_channel.send("Oops. Wrong answer. Player Eliminated!")
            return None


async def honey_collected(client: commands.Bot, ctx: commands.Context, users: list):
    embed = discord.Embed(
        title="Welcome to the Honeycomb game.",
        description=games['honeycomb']['desc'],
        color=discord.Colour.purple()
    )

    dbl_client = topgg.DBLClient(client, TOPGG_TOKEN)

    embed.set_thumbnail(url=bot_icon)
    embed.set_footer(text="Game will begin in 10 seconds.")
    await ctx.send(embed=embed)

    _passed = await asyncio.gather(*[honey_solo(dbl_client, client, ctx, random.choice(words), user) for user in users])
    passed = [user for user in _passed if user is not None]
    return passed
