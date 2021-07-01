import discord
import asyncio

from discord.ext import commands, menus

from Utilities import AssetCreation

import asyncpg

class NoChar(commands.CheckFailure):
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

class HasChar(commands.CheckFailure):
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

class AlreadyInAssociation(commands.CheckFailure):
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

class NotBrotherhoodMember(commands.CheckFailure):
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

class NotGuildMember(commands.CheckFailure):
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

class NotCollegeMember(commands.CheckFailure):
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

class IsNotAssociationLeader(commands.CheckFailure):
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

class IsAssociationLeader(commands.CheckFailure):
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

class IsNotAssociationOfficer(commands.CheckFailure):
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

class AssociationFull(commands.CheckFailure):
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

class NotAdmin(commands.CheckFailure):
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

class NotMayor(commands.CheckFailure):
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

class NotComptroller(commands.CheckFailure):
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

class HasNoBankAccount(commands.CheckFailure):
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

class HasBankAccount(commands.CheckFailure):
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

class IncorrectOccupation(commands.CheckFailure):
    def __init__(self, occupation, player_class, prefix, *args, **kwargs):
        self.message = f'This command is exclusive to the **{occupation}** class only, but you are a **{player_class}**. If you wish to change classes, do `{prefix}class {occupation}`.'
        super().__init__(message=self.message, *args, **kwargs)

async def not_player(ctx):
    async with ctx.bot.pg_con.acquire() as conn:
        result = await conn.fetchrow('SELECT user_id FROM players WHERE user_id = $1', ctx.author.id)
        await ctx.bot.pg_con.release(conn)
    
    if result is None: #Then there is no char for this id
        return True
    else:
        raise HasChar(ctx.author, message='Player has a character and failed not_player check.')

async def is_player(ctx):
    async with ctx.bot.pg_con.acquire() as conn:
        result = await conn.fetchrow('SELECT user_id FROM players WHERE user_id = $1', ctx.author.id)
        await ctx.bot.pg_con.release(conn)
        
    if result is not None: #Then there is a char for this id
        return True
    else:
        raise NoChar(ctx.message.author, message='Player does not have a character. Failed is_player check.')

async def has_char(pool, user : discord.user): #NOT A CHECK --> in-function version of is_player
    async with pool.acquire() as conn:
        result = await conn.fetchrow('SELECT user_id FROM players WHERE user_id = $1', user.id)
        await pool.release(conn)
    
    if result is not None: #Then there is a char for this id
        return True

async def not_in_guild(ctx):
    async with ctx.bot.pg_con.acquire() as conn:
        guild = await conn.fetchval('SELECT guild FROM players WHERE user_id = $1', ctx.author.id)
        await ctx.bot.pg_con.release(conn)
    
    if guild is None:
        return True
    else:
        raise AlreadyInAssociation(ctx.author, message='Player is in an association. Failed not_in_guild check.')

async def target_not_in_guild(pool, user : discord.user): #NOT A CHECK --> in-function version of not_in_guilf
    async with pool.acquire() as conn:
        guild = await conn.fetchval('SELECT guild FROM players WHERE user_id = $1', user.id)
        await pool.release(conn)
    
    if guild is None:
        return True

async def in_brotherhood(ctx):
    async with ctx.bot.pg_con.acquire() as conn:
        guild = await conn.fetchrow('SELECT guild FROM players WHERE user_id = $1', ctx.author.id)
    
        if guild[0] is None:
            raise NotBrotherhoodMember(ctx.author, message='Failed in_brotherhood check.')
        else:
            guild_type = await conn.fetchval('SELECT guild_type FROM guilds WHERE guild_id = $1', guild[0])
            if guild_type == 'Brotherhood':
                return True
            else:
                raise NotBrotherhoodMember(ctx.author, message='Failed in_brotherhood check.')

async def in_guild(ctx):
    async with ctx.bot.pg_con.acquire() as conn:
        guild = await conn.fetchval('SELECT guild FROM players WHERE user_id = $1', ctx.author.id)

        if guild is None:
            raise NotGuildMember(ctx.author, message='Failed in_guild check.')
        else:
            guild_type = await conn.fetchval('SELECT guild_type FROM guilds WHERE guild_id = $1', guild)
            if guild_type == 'Guild':
                return True  
            else:
                raise NotGuildMember(ctx.author, message='Failed in_guild check.')  

async def in_college(ctx):
    async with ctx.bot.pg_con.acquire() as conn:
        guild = await conn.fetchval('SELECT guild FROM players WHERE user_id = $1', ctx.author.id)

        if guild is None:
            raise NotCollegeMember(ctx.author, message='Failed in_college check.')
        else:
            guild_type = await conn.fetchval('SELECT guild_type FROM guilds WHERE guild_id = $1', guild)
            if guild_type == 'College':
                return True    
            else:
                raise NotCollegeMember(ctx.author, message='Failed in_guild check.') 

async def guild_can_be_created(ctx, name): #NOT A CHECK
    async with ctx.bot.pg_con.acquire() as conn:
        is_taken = await conn.fetchrow('SELECT guild_id FROM guilds WHERE guild_name = $1', name)
        if is_taken is not None:
            await ctx.reply('This name is already taken.')
            await ctx.bot.pg_con.release(conn)
            return
        gold = await conn.fetchrow('SELECT gold FROM players WHERE user_id = $1', ctx.author.id)
        if gold[0] < 15000:
            await ctx.reply('You don\'t have enough money form a brotherhood.')
            await ctx.bot.pg_con.release(conn)
            return
        await ctx.bot.pg_con.release(conn)
        return True #Otherwise we're good to go

async def is_guild_leader(ctx):
    async with ctx.bot.pg_con.acquire() as conn:
        playerrank = await conn.fetchval('SELECT guild_rank FROM players WHERE user_id = $1', ctx.author.id)

        if playerrank == 'Leader':
            return True
        else:
            raise IsNotAssociationLeader(ctx.author, message='Player is not an association leader. Failed is_guild_leader check.')

async def is_not_guild_leader(ctx):
    player_guild = await AssetCreation.getGuildFromPlayer(ctx.bot.pg_con, ctx.author.id)
    if ctx.author.id != player_guild['Leader']:
        return True
    else:
        raise IsAssociationLeader(ctx.author, message='Player failed is_not_guild_leader check.')

async def is_guild_officer(ctx):
    async with ctx.bot.pg_con.acquire() as conn:
        rank = await conn.fetchval('SELECT guild_rank FROM players WHERE user_id = $1', ctx.author.id)
        await ctx.bot.pg_con.release(conn)
    
    if rank == 'Officer' or rank == 'Leader':
        return True
    else:
        raise IsNotAssociationOfficer(ctx.author, message='Player failed is_guild_officer check.')

async def target_is_guild_officer(pool, user_id : int): #NOT A CHECK
    async with pool.acquire() as conn:
        rank = await conn.fetchval('SELECT guild_rank FROM players WHERE user_id = $1', user_id)
        await pool.release(conn)

    if rank == 'Officer' or rank == 'Leader':
        return True

    else:
        return False

async def guild_has_vacancy(ctx): 
    guild = await AssetCreation.getGuildFromPlayer(ctx.bot.pg_con, ctx.author.id)
    members = await AssetCreation.getGuildMemberCount(ctx.bot.pg_con, guild['ID'])
    capacity = await AssetCreation.getGuildCapacity(ctx.bot.pg_con, guild['ID'])
    if members < capacity:
        return True
    else:
        raise AssociationFull(ctx.author, message='Guild is full. Failed guild_has_vacancy check.')

async def target_guild_has_vacancy(pool, guild_id : int): #NOT A CHECK. ALT VERSION OF guild_has_vacancy
    guild = await AssetCreation.getGuildByID(pool, guild_id)
    members = await AssetCreation.getGuildMemberCount(pool, guild['ID'])
    capacity = await AssetCreation.getGuildCapacity(pool, guild['ID'])
    if members < capacity:
        return True 

admins = [196465885148479489, 325080171591761921, 530760994289483790, 465388103792590878] #Seb, Sean, Demi, Bort
async def is_admin(ctx):
    if ctx.author.id in admins:
        return True
    else:
        raise NotAdmin(ctx.author, message='Failed is_admin check.')

async def is_mayor(ctx):
    offices = await AssetCreation.get_officeholders(ctx.bot.pg_con)
    if ctx.author.id == offices['Mayor_ID']:
        return True
    else:
        raise NotMayor(ctx.author, message='Failed is_mayor check.')

async def is_comptroller(ctx):
    offices = await AssetCreation.get_officeholders(ctx.bot.pg_con)
    if ctx.author.id == offices['Comptroller_ID']:
        return True
    else:
        raise NotComptroller(ctx.author, message='Failed is_comptroller check.')

async def has_bank_account(ctx):
    async with ctx.bot.pg_con.acquire() as conn:
        account = await conn.fetchval('SELECT id FROM guild_bank_account WHERE user_id = $1', ctx.author.id)
        if account:
            return True
        else:
            raise HasNoBankAccount(ctx.author, message='User lacks a guild bank account. Failed has_bank_account check.')

async def not_has_bank_account(ctx):
    async with ctx.bot.pg_con.acquire() as conn:
        account = await conn.fetchval('SELECT id FROM guild_bank_account WHERE user_id = $1', ctx.author.id)
        if not account:
            return True
        else:
            raise HasBankAccount(ctx.author, message='Failed not_has_bank_account check.')

async def is_blacksmith(ctx):
    player_class = await AssetCreation.getClass(ctx.bot.pg_con, ctx.author.id)
    occupation = 'Blacksmith'
    if player_class == occupation:
        return True
    else:
        raise IncorrectOccupation(occupation, player_class, ctx.prefix)

async def is_farmer(ctx):
    player_class = await AssetCreation.getClass(ctx.bot.pg_con, ctx.author.id)
    occupation = 'Farmer'
    if player_class == occupation:
        return True
    else:
        raise IncorrectOccupation(occupation, player_class, ctx.prefix)

async def is_hunter(ctx):
    player_class = await AssetCreation.getClass(ctx.bot.pg_con, ctx.author.id)
    occupation = 'Hunter'
    if player_class == occupation:
        return True
    else:
        raise IncorrectOccupation(occupation, player_class, ctx.prefix)

async def is_butcher(ctx):
    player_class = await AssetCreation.getClass(ctx.bot.pg_con, ctx.author.id)
    occupation = 'Butcher'
    if player_class == occupation:
        return True
    else:
        raise IncorrectOccupation(occupation, player_class, ctx.prefix)