import asyncio
import random

import discord
from discord.ext import commands
from prawcore.exceptions import NotFound

from cogs.utils import db
from cogs.utils.paginator import Pages


class RedditConfig(db.Table, table_name='reddit_config'):
    user_id = db.Column(db.Integer(big=True), primary_key=True)
    reddit_username = db.Column(db.String)


class Reddit:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='wiki')
    async def reddit_wiki_page(self, ctx, *, search: str = None):
        sub = ctx.r.subreddit('transcribersofreddit')
        if not search:
            embed = discord.Embed(
                color=ctx.author.top_role.color,
                description='[ToR Wiki](https://www.reddit.com/'
                            'r/TranscribersOfReddit/wiki/index)'
            )

            await ctx.send(embed=embed)
            return

        results = []

        for page in sub.wiki:
            if search in str(page.name):
                results.append(
                    f'[{page.name}](https://www.reddit.com'
                    f'/r/TranscribersOfReddit/wiki/{page.name})'
                )

        if results is not []:
            p = Pages(ctx, entries=results)
            p.embed.color = ctx.author.top_role.color
            await p.paginate()
        else:
            await ctx.send("Couldn't find any results for that. Sorry! ):")

    @commands.command()
    async def link(self, ctx, *, username: str):
        if username.startswith('/u/'):
            username = username.replace('/u/', '', 1)
        elif username.startswith('u/'):
            username = username.replace('u/', '', 1)

        # throw away the value, this is just so we can tell if the user is valid
        try:
            _ = ctx.r.redditor(username).fullname
        except AttributeError:
            # seems to happen when a user has no activity, like /u/asdf.
            pass
        except NotFound:
            await ctx.send("Sorry! That username doesn't appear to be valid.")
            return

        msg = await ctx.send(
            'Mods: can you please check that this is correct. If so, react '
            'with :white_check_mark:. Otherwise, react with :no_entry_sign:.'
        )

        await msg.add_reaction('✅')
        await msg.add_reaction('🚫')

        def check(r, u):
            if r.message.id != msg.id:
                return False

            if u == self.bot.user:
                return False

            if u.id == self.bot.owner_id:
                return True

            if r.message.guild is None:
                return False

            if r.emoji is not '✅' or '🚫':
                return False

            resolved = u.guild_permissions
            return resolved.manage_guild is True

        try:
            reaction, _ = await self.bot.wait_for(
                'reaction_add',
                timeout=600.0,
                check=check
            )

            await reaction.message.delete()
        except asyncio.TimeoutError:
            await ctx.send(
                'Looks like a mod took too long to respond. Try again later :)'
            )
        else:
            if reaction.emoji == '🚫':
                await ctx.send('Sorry mate. A mod denied your request.')
                return

            # has to be normal reaction now

            query = """
INSERT INTO reddit_config (user_id, reddit_username) VALUES ($1, $2)
ON CONFLICT (user_id)
  DO UPDATE SET
    reddit_username = EXCLUDED.reddit_username;"""

            await ctx.db.execute(query, ctx.author.id, username)

            await ctx.auto_react()
            await ctx.send("You've been approved! Woo!")

    @commands.command()
    async def account(self, ctx, user: discord.Member = None):
        query = """
SELECT reddit_username
FROM reddit_config
WHERE user_id = $1;"""

        is_self = user is None
        user = ctx.author if not user else user

        val = await ctx.db.fetchval(query, user.id)
        if val is None:
            if is_self:
                message = f'You have not set up your account yet. You can do ' \
                          f'this with `{ctx.prefix}link <reddit username>`.'
            else:
                message = "That user hasn't set up their account yet."

            await ctx.send(message)
            return

        description = f'{user.display_name}\'s Reddit account is' \
                      f' [/u/{val}](https://reddit.com/u/{val}).'

        if random.randrange(1, 100) == 5:
            description += ' Please enjoy stalking them.'

        await ctx.send(embed=discord.Embed(description=description))
        return


def setup(bot):
    bot.add_cog(Reddit(bot))
