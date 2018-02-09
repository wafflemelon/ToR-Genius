from discord.ext import commands

from cogs.utils.config import Config
from cogs.utils.paginator import Pages


class CommandName(commands.Converter):

    async def convert(self, ctx, argument):
        first_word, _, _ = argument.partition(' ')

        # hacky but whatever. This is because things.
        command = ctx.bot.get_command('custom')
        if first_word in command.all_commands:
            raise commands.BadArgument("That's already a sub command")

        return argument


class CustomCommands:
    def __init__(self, bot):
        self.bot = bot
        self.config = Config('custom_commands.json')

    @staticmethod
    async def __error(ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(error)

    @commands.group(aliases=['c'], invoke_without_command=True)
    async def custom(self, ctx, *, name: CommandName):
        """Basic tagging like thing just for me."""
        if name not in self.config:
            await ctx.send("That custom command doesn't exist")
        else:
            await ctx.send(self.config[name])

    @custom.command(aliases=['a'])
    @commands.is_owner()
    async def add(self, ctx, name: CommandName, *, content):
        """Add a custom command"""
        if name in self.config:
            return await ctx.send(
                f'There already is a custom command called {name}.'
            )
        await self.config.put(name, content)
        await ctx.auto_react()

    @custom.command(aliases=['rm', 'del'])
    @commands.is_owner()
    async def delete(self, ctx, name: CommandName):
        """Removes a custom command"""
        if name not in self.config:
            return await ctx.send(f"That custom command doesn't exist")

        await self.config.delete(name)
        await ctx.auto_react()

    @custom.command(aliases=['e'])
    @commands.is_owner()
    async def edit(self, ctx, name: CommandName, *, content):
        """Removes a custom command"""
        if name not in self.config:
            return await ctx.send(f"That custom command doesn't exist")

        await self.config.put(name, content)
        await ctx.auto_react()

    @custom.command(aliases=['ls', 'all', 'l'])
    async def list(self, ctx, query=''):
        p = Pages(
            ctx,
            entries=[e for e in self.config.all().keys() if query in e]
        )

        if not p.entries:
            return await ctx.send('No results found.')
        await p.paginate()


def setup(bot):
    bot.add_cog(CustomCommands(bot))
