import discord
from discord.ext import commands

from cogs.utils import db


class BostonTable(db.Table, table_name='boston'):
    user_id = db.Column(db.Integer(big=True), primary_key=True)
    documents = db.Column(db.Integer)
    pages = db.Column(db.Integer)


class Boston:
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    async def __local_check(ctx):
        return ctx.guild.id in [318873523579781132, 369960111679995905]

    @commands.group(aliases=['bost', 'bst', 'bt'])
    async def boston(self, ctx):
        """Tools for tracking boston transcriptions"""
        if ctx.invoked_subcommand is None:
            await ctx.show_help('boston')

    @boston.command(aliases=['lb', 'top', 'all'])
    async def leaderboard(self, ctx):
        """View a leaderboard of the top transcriptions"""
        query = """
SELECT *
FROM boston
ORDER BY pages, documents
LIMIT 30;"""

        result = await ctx.db.fetch(query)

        total_docs = sum([r['documents'] for r in result])
        total_pages = sum([r['pages'] for r in result])

        top_pages = [(r['user_id'], r['pages']) for r in result]

        e = discord.Embed(
            title='Leaderboard',
            description=f'**Total amount of documents transcribed:** '
                        f'{total_docs}\n**Total amount of pages transcribed**:'
                        f' {total_pages}',
            color=ctx.author.color

        )

        leaderboard = []

        for user, count in top_pages:
            user = ctx.guild.get_member(user)
            leaderboard.append(
                f'{"Unknown" if not user else user.display_name}: {count}'
            )

        if not leaderboard:
            return await ctx.send('No transcriptions yet.')

        e.add_field(name='Top transcribers', value='\n'.join(leaderboard))
        await ctx.send(embed=e)

    @boston.command(aliases=['a'])
    async def add(self, ctx, pages: int, documents: int = 1):
        """Add your pages/documents"""
        query = """
INSERT INTO boston (user_id, documents, pages) VALUES ($1, $2, $3)
ON CONFLICT (user_id)
  DO UPDATE SET
    documents = boston.documents + EXCLUDED.documents,
    pages     = boston.pages + EXCLUDED.pages;
        """

        res = await ctx.prompt(
            f'You are about to add {documents} document'
            f'{"s" if documents > 1 else ""} and '
            f'{pages} page{"s" if pages > 1 else ""}',
            reacquire=False
        )

        if res is None:
            return await ctx.send('Timed out.')

        if res:
            await ctx.db.execute(query, ctx.author.id, documents, pages)
            await ctx.auto_react()


def setup(bot):
    bot.add_cog(Boston(bot))
