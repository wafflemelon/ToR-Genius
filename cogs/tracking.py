# Original work Copyright (c) 2015 Rapptz (https://github.com/Rapptz/RoboDanny)
# Modified work Copyright (c) 2017 Perry Fraser
#
# Licensed under the MIT License. https://opensource.org/licenses/MIT

# Tracking stuff and table thing from
# https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/stats.py
import logging

from .utils import db

log = logging.getLogger(__name__)


class Tracking(db.Table):
    id = db.PrimaryKeyColumn()
    guild_id = db.Column(db.Integer(big=True), index=True)
    channel_id = db.Column(db.Integer(big=True))
    author_id = db.Column(db.Integer(big=True), index=True)
    used = db.Column(db.Datetime)
    prefix = db.Column(db.String)
    command = db.Column(db.String, index=True)


class BotTracking:

    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    async def on_command(ctx):
        command = ctx.command.qualified_name
        message = ctx.message
        if ctx.guild is None:
            destination = 'PM'
            guild_id = None
        else:
            destination = f'{message.channel.id} ({message.guild.name})'
            guild_id = message.guild.id

        query = """
        INSERT INTO tracking (
          guild_id, channel_id, author_id, used, prefix, command
        )
          VALUES ($1, $2, $3, $4, $5, $6)       
        """

        log.info(
            f'{message.created_at}:'
            f' Message from {message.author} in {destination}. '
            f'Content: {message.content}'
        )
        # await ctx.send(f'{command}')
        print(f'{message.content} and {command}')
        await ctx.db.execute(query, guild_id, message.channel.id,
                             message.author.id, message.created_at, ctx.prefix,
                             command)
        await ctx.send('ur dumb')


def setup(bot):
    bot.add_cog(BotTracking(bot))
