# Original work Copyright (c) 2015 Rapptz (https://github.com/Rapptz/RoboDanny)
# Modified work Copyright (c) 2017 Perry Fraser
#
# Licensed under the MIT License. https://opensource.org/licenses/MIT

# As of writing this, this is still WIP. Methods are planned to come from
# R. Danny

from discord.ext import commands

# Once again, basically mostly stolen from
# https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/utils/checks.py


async def check_permissions(ctx, perms, *, check=all):
    owner = ctx.bot.is_owner(ctx.author)
    if owner:
        return True

    resolved = ctx.channel.permissions_for(ctx.author)
    return check(
        getattr(resolved, name, None) == value for name, value in perms.items()
    )
