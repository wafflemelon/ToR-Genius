import json
import random

from discord.ext import commands

from cogs.reddit import RedditAccountConverter, RedditMember
from cogs.utils import reddit_stats


def insult():
    with open('insults.json') as f:
        return ' '.join([random.choice(sub_list) for sub_list in json.load(f)])


class Stats:
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def torstats(self, ctx, user: RedditAccountConverter = None):
        """Get some of your latest stats from Transcribers of Reddit!"""
        await ctx.send(
            'I\'m only in beta, so forgive me for mistakes please\nSadly I '
            'can only see and count your last 1000 comments.\nThe numbers can '
            'even be higher than your official Γ count, because I am just '
            'counting all of your comments that look like transcriptions.'
        )
        await ctx.channel.trigger_typing()

        user = await RedditMember.create(ctx, ctx.author) if not user else user

        e = await reddit_stats.stats(ctx, user.reddit)
        await ctx.send(embed=e)

    @commands.command()
    async def goodbad(self, ctx, user: RedditAccountConverter = None):
        """Are you good? Are you bad? We will never know!"""
        await ctx.channel.trigger_typing()
        user = await RedditMember.create(ctx, ctx.author) if not user else user

        await ctx.send(embed=reddit_stats.goodbad(ctx, user.reddit))

    @staticmethod
    async def on_message(message):
        if 'good bot' in message.content.lower():
            await message.add_reaction('🤖')

        if 'bad bot' in message.content.lower():
            await message.add_reaction('😢')

        if 'jarvin' in message.content.lower():
            await message.add_reaction('👍')

        if 'send rudes' in message.content.lower():
            await message.channel.send(f'Thou {insult()}!')


def setup(bot):
    bot.add_cog(Stats(bot))
