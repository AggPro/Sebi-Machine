import discord
from discord.ext import commands


class BotManager:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='claim', aliases=['makemine', 'gimme'])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def _claim_bot(self, ctx, bot: discord.Member=None, prefix: str=None, owner : discord.Member =None):
        if not bot:
            raise Warning('You must include the name of the bot you are trying to claim... Be exact.')
        if not bot.bot:
            raise Warning('You can only claim bots.')
        if not prefix:
            if bot.display_name.startswith('['):
                prefix = bot.display_name.split(']')[0].strip('[')
            else:
                raise Warning('Prefix not provided and can\'t be found in bot name.')
        
        if owner != None and ctx.author.guild_permissions.manage_guild:
            author_id = owner.id
        else:
            author_id = ctx.author.id
        em = discord.Embed()

        if await self.bot.db_con.fetchval('select count(*) from bots where owner = $1', author_id) >= 10:
            em.colour = self.bot.error_color
            em.title = 'Too Many Bots Claimed'
            em.description = 'Each person is limited to claiming 10 bots as that is how ' \
                             'many bots are allowed by the Discord API per user.'
            return await ctx.send(embed=em)
        existing = await self.bot.db_con.fetchrow('select * from bots where id = $1', bot.id)
        if not existing:
            await self.bot.db_con.execute('insert into bots (id, owner, prefix) values ($1, $2, $3)',
                                          bot.id, author_id, prefix)
            em.colour = self.bot.embed_color
            em.title = 'Bot Claimed'
            em.description = f'You have claimed {bot.display_name} with a prefix of {prefix}\n' \
                             f'If there is an error please run command again to correct the prefix,\n' \
                             f'or {ctx.prefix}unclaim {bot.mention} to unclaim the bot.'
        elif existing['owner'] and existing['owner'] != author_id:
            em.colour = self.bot.error_color
            em.title = 'Bot Already Claimed'
            em.description = 'This bot has already been claimed by someone else.\n' \
                             'If this is actually your bot please let the guild Administrators know.'
        elif existing['owner'] and existing['owner'] == author_id:
            em.colour = self.bot.embed_color
            em.title = 'Bot Already Claimed'
            em.description = 'You have already claimed this bot.\n' \
                             'If the prefix you provided is different from what is already in the database' \
                             ' it will be updated for you.'
            if existing['prefix'] != prefix:
                await self.bot.db_con.execute("update bots set prefix = $1 where id = $2", prefix, bot.id)
        elif not existing['owner']:
            await self.bot.db_con.execute('update bots set owner = $1, prefix = $2 where id = $3',
                                          author_id, prefix, bot.id)
            em.colour = self.bot.embed_color
            em.title = 'Bot Claimed'
            em.description = f'You have claimed {bot.display_name} with a prefix of {prefix}\n' \
                             f'If there is an error please run command again to correct the prefix,\n' \
                             f'or {ctx.prefix}unclaim {bot.mention} to unclaim the bot.'
        else:
            em.colour = self.bot.error_color
            em.title = 'Something Went Wrong...'
        await ctx.send(embed=em)

    @commands.command(name='unclaim')
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def _unclaim_bot(self, ctx, bot: discord.Member=None):
        if not bot:
            raise Warning('You must include the name of the bot you are trying to claim... Be exact.')
        if not bot.bot:
            raise Warning('You can only unclaim bots.')

        em = discord.Embed()

        existing = await self.bot.db_con.fetchrow('select * from bots where id = $1', bot.id)
        if not existing or not existing['owner']:
            em.colour = self.bot.error_color
            em.title = 'Bot Not Found'
            em.description = 'That bot is not claimed'
        elif existing['owner'] != ctx.author.id and ctx.author.guild_permissions.manage_guild:
            em.colour = self.bot.error_color
            em.title = 'Not Claimed By You'
            em.description = 'That bot is claimed by someone else.\n' \
                             'You can\'t unclaim someone else\'s bot'
        else:
            await self.bot.db_con.execute('update bots set owner = null where id = $1', bot.id)
            em.colour = self.bot.embed_color
            em.title = 'Bot Unclaimed'
            em.description = f'You have unclaimed {bot.display_name}\n' \
                             f'If this is an error please reclaim using\n' \
                             f'{ctx.prefix}claim {bot.mention} {existing["prefix"]}'
        await ctx.send(embed=em)

    @commands.command(name='listclaims', aliases=['claimed', 'mybots'])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def _claimed_bots(self, ctx, usr: discord.Member=None):
        if usr is None:
            usr = ctx.author
        bots = await self.bot.db_con.fetch('select * from bots where owner = $1', usr.id)
        if bots:
            em = discord.Embed(title=f'{usr.display_name} has claimed the following bots:',
                               colour=self.bot.embed_color)
            for bot in bots:
                member = ctx.guild.get_member(int(bot['id']))
                em.add_field(name=member.display_name, value=f'Stored Prefix: {bot["prefix"]}', inline=False)
        else:
            em = discord.Embed(title='You have not claimed any bots.',
                               colour=self.bot.embed_color)
        await ctx.send(embed=em)

    @commands.command(name='whowns')
    async def _whowns(self, ctx, bot: discord.Member):
        if not bot.bot:
            await ctx.send('this commands only for bots')
        else:
            owner = await self.bot.db_con.fetchrow('select * from bots where id = $1', bot.id)
            await ctx.send(ctx.guild.get_member(owner['owner']).display_name)



def setup(bot):
    bot.add_cog(BotManager(bot))