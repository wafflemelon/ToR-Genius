# Original work Copyright (c) 2015 Rapptz (https://github.com/Rapptz/RoboDanny)
# Modified work Copyright (c) 2017 Perry Fraser
#
# Licensed under the MIT License. https://opensource.org/licenses/MIT

# error junk
# from https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/mod.py

import discord
from discord.ext import commands

import logging

log = logging.getLogger(__name__)


class Mod:
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    async def __error(ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(error)
        elif isinstance(error, commands.CommandInvokeError):
            original = error.original
            if isinstance(original, discord.Forbidden):
                await ctx.send(
                    'I do not have permission to execute this action.'
                )
            elif isinstance(original, discord.NotFound):
                await ctx.send(
                    f'This entity does not exist: {original.text}'
                )
            elif isinstance(original, discord.HTTPException):
                await ctx.send(
                    'Somehow, an unexpected error occurred. Try again later?'
                )

# Not in use yet, won't load
