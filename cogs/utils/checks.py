# Original work Copyright (c) 2015 Rapptz (https://github.com/Rapptz/RoboDanny)
# Modified work Copyright (c) 2017 Perry Fraser
#
# Licensed under the MIT License. https://opensource.org/licenses/MIT

# ~~As of writing this, this is still WIP. Methods are planned to come from
# R. Danny~~ ok that's done. For now using it line for line + formatting

# May tweak it a bit, but I'm hungry and just want to have checks on prefix
# junk

from discord.ext import commands


# Once again, basically mostly stolen from
# https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/utils/checks.py


async def check_permissions(ctx, perms, *, check=all):
    owner = await ctx.bot.is_owner(ctx.author)
    if owner:
        return True

    resolved = ctx.channel.permissions_for(ctx.author)
    return check(
        getattr(resolved, name, None) == value for name, value in perms.items()
    )


def has_permissions(*, check=all, **perms):
    async def pred(ctx):
        return await check_permissions(ctx, perms, check=check)

    return commands.check(pred)


async def check_guild_permissions(ctx, perms, *, check=all):
    is_owner = await ctx.bot.is_owner(ctx.author)
    if is_owner:
        return True

    if ctx.guild is None:
        return False

    resolved = ctx.author.guild_permissions
    return check(
        getattr(resolved, name, None) == value for name, value in perms.items()
    )


def is_mod():
    async def pred(ctx):
        return await check_guild_permissions(ctx, {'ban_members': True})

    return commands.check(pred)


def tor_only():
    async def pred(ctx):
        owner = await ctx.bot.is_owner(ctx.author)
        if owner:
            return True

        ok = ctx.guild.id in [318873523579781132, 369960111679995905]
        if not ok:
            return False

        return True

    return commands.check(pred)
