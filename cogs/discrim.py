from collections import Counter

import discord
import numpy as np
from discord.ext import commands
from scipy import stats

from cogs.utils.paginator import EmbedPages, Pages


class Discriminator(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            if not int(argument) in range(1, 10000):
                raise commands.BadArgument('That isn\'t a valid discriminator.')
        except ValueError:
            raise commands.BadArgument('That isn\'t a valid discriminator.')
        else:
            return int(argument)


class Selector(commands.Converter):
    async def convert(self, ctx, argument):
        if argument not in ['>', '>=', '<', '<=', '=']:
            raise commands.BadArgument('Not a valid selector')
        return argument


class Discrim:
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def discriminfo(self, ctx):
        """Get some stats about the servers discrims"""
        discrim_list = [int(u.discriminator) for u in ctx.guild.members]

        # The range is so we can get any discrims that no one has.
        # Just subtract one from the number of uses.
        count = Counter(discrim_list + [int(i) for i in range(1, 10000)])
        count = sorted(count.items(), key=lambda c: c[1], reverse=True)

        embeds = {
            'Summary': {
                'Most Common': ', '.join(str(d[0]) for d in count[:3])
                               + ', and ' + str(count[4][0]),
                'Least Common': ', '.join(str(d[0]) for d in count[-4:-1][::-1])
                                + ', and ' + str(count[-1][0]),
                'Three Unused': '\n'.join([str(d[0]) for d in count
                                           if d[1] == 1][:3]),
                'Average': np.mean(discrim_list),
            },
            'Statistics': {
                'Average': np.mean(discrim_list),
                'Mode': stats.mode(discrim_list)[0][0],
                'Median': np.median(discrim_list),
                'Standard Deviation': np.std(discrim_list),
            }
        }

        final_embeds = []

        for embed_title in embeds.keys():
            e = discord.Embed(title=embed_title)
            for field_name in embeds[embed_title].keys():
                e.add_field(name=field_name,
                            value=embeds[embed_title][field_name], inline=False)
            final_embeds.append(e)

        p = EmbedPages(ctx, embeds=final_embeds)
        await p.paginate()

    # It's a converter, not a type annotation in this case
    # noinspection PyTypeChecker
    @commands.command()
    async def discrim(self, ctx, discriminator: Discriminator,
                      *, selector: Selector = '='):
        """Search for specific discriminators.

        Optional parameter for ranges to be searched.

        It can be >, >=, <=, or <.

        Ranges between two numbers hasn't been implemented yet."""
        if selector == '>':
            p = Pages(ctx, entries=[
                f'{u.display_name}#{u.discriminator}'
                for u in ctx.guild.members
                if int(u.discriminator) > discriminator
            ])
        elif selector == '<':
            p = Pages(ctx, entries=[
                f'{u.display_name}#{u.discriminator}'
                for u in ctx.guild.members
                if int(u.discriminator) < discriminator
            ])
        elif selector == '>=':
            p = Pages(ctx, entries=[
                f'{u.display_name}#{u.discriminator}'
                for u in ctx.guild.members
                if int(u.discriminator) >= discriminator
            ])
        elif selector == '<=':
            p = Pages(ctx, entries=[
                f'{u.display_name}#{u.discriminator}'
                for u in ctx.guild.members
                if int(u.discriminator) <= discriminator
            ])
        elif selector == '=':
            p = Pages(ctx, entries=[
                f'{u.display_name}#{u.discriminator}'
                for u in ctx.guild.members
                if int(u.discriminator) == discriminator
            ])
        else:
            raise commands.BadArgument('Could not parse arguments')

        if not p.entries:
            return await ctx.send('No results found.')

        await p.paginate()


def setup(bot):
    bot.add_cog(Discrim(bot))
