import logging

log = logging.getLogger(__name__)


class BotLogging:
    def __init__(self, bot):
        self.bot = bot

    async def on_command(self, ctx):
        is_owner = await self.bot.is_owner(ctx.author)
        if ctx.guild is None and not is_owner:
            await self.bot.get_channel(400869729323057162).send(
                f'Command ran in DM by {ctx.author}: '
                f'{ctx.command.qualified_name}'
            )

            log.warning(
                f'Command ran in DM by {ctx.author}: '
                f'{ctx.command.qualified_name}'
            )
        else:
            log.info(
                f'Command ran by {ctx.author}: {ctx.command.qualified_name}'
            )


def setup(bot):
    bot.add_cog(BotLogging(bot))
