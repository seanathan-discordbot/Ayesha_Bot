import discord
import asyncio

from discord.ext import commands, menus
from discord.ext.commands.cooldowns import BucketType

from Utilities import Checks
from Utilities.PageSourceMaker import PageMaker

import random
import asyncpg

# The dictionary used is words_alpha given here: https://github.com/dwyl/english-words

point_conversion = {'k' : 5}

for key in ['a', 'e', 'i', 'l', 'n', 'o', 'r', 's', 't', 'u']:
    point_conversion[key] = 1
for key in ['d', 'g']:
    point_conversion[key] = 2
for key in ['b', 'c', 'm', 'p']:
    point_conversion[key] = 3
for key in ['f', 'h', 'v', 'w', 'y']:
    point_conversion[key] = 4
for key in ['j', 'x']:
    point_conversion[key] = 8
for key in ['q', 'z']:
    point_conversion[key] = 10

class WordChain:
    """A word chain instance. Instantiate the class with the required parameters and run either
    the 'play_public' or 'play_solo' method to begin a game.

    Attributes
    ----------
    client : discord.Client
        The bot
    ctx : commands.Context
        The context of the class instantiation
    type : str
        "Public", "Solo", "Scrabble", "Lightning" - determines game rules
    host : discord.User
        The player who invoked this object instance
    db : asyncpg.pool
        The database the game will connect to
    alphabet : list
        The alphabet. Used to get valid letters to start the game with
    timeout : float
        The length of a turn ingame, in seconds
    players : list
        A list containing the 'discord.User's playing the game
    points : dict
        Counts the amount of points each player has (Scrabble Mode Only)

    Methods
    -------
    deny_repeats(players : list, user : discord.User)
        Return True if given user is already in the list of players
    await valid_word(player, letter : str, word : str)
        Checks to see if a word is valid for use in-game. Also calculates points in Scrabble Mode
    await prompt_join()
        Send message asking players to join the game
    await end_game(used_words : int)
        Ends the game and logs entries in the database
    await input_solo_game(score : int)
        Like end_game(), but only inputs entries in the database for solo mode
    await play_public
        Begin a multiplayer instance: Public, Lightning, or Scrabble rulesets
    await play_solo
        Begin a singleplayer instance: Solo ruleset
    """
    def __init__(self, client : discord.Client, ctx : commands.Context, type : str, 
                 db : asyncpg.pool):
        """
        Parameters
        ----------
        ctx : commands.Context
            The context of the class instantiation
        type : str
            "Public", "Solo", "Scrabble", "Lightning" - determines game rules
        db : asyncpg.pool
            The database the game will connect to
        """
        # Input setters
        self.client = client
        self.ctx = ctx
        self.type = type
        self.host = ctx.author
        self.db = db

        # Other useful variables
        self.alphabet = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o',
                         'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
        self.timeout = 0
        self.players = [self.host]
        self.points = {} # For Scrabble Mode

        if self.type == 'Lightning':
            self.timeout = 10.0
        else:
            self.timeout = 30.0

    def deny_repeats(self, players : list, user : discord.User):
        """Return True if given user is already in the list of players."""
        player_ids = [player.id for player in players]
        if user.id in player_ids:
            return True

    async def valid_word(self, player : discord.User, letter : str, word : str):
        """Checks to see if the word meets following criteria:
        1. Word begins with the passed letter
        2. Word is valid (its in the dictionary database)

        Returns a dict containing 'next' - the last letter of the word if its valid
            If its invalid, returns None
            If type == 'Scrabble', 'points' describes the amount of points that word earned
        """
        if not word.startswith(letter):
            return None
        
        async with self.db.acquire() as conn:
            psql = """
                    SELECT id 
                    FROM word_list 
                    WHERE word = $1
                    """
            word_id = await conn.fetch(psql, word)

            if len(word_id) > 0:
                if self.type == 'Scrabble': # Calc points for Scrabble Mode
                    word_score = 0
                    for char in word:
                        word_score += point_conversion[char]
                        self.points[player] += point_conversion[char]
                    return {'next' : word[-1], 'points' : word_score}

                return {'next' : word[-1], 'points' : None}
            else:
                return None

    async def prompt_join(self):
        """Send message asking players to join the game."""
        # Send the message and add reaction
        join_msg = await self.ctx.send((f"{self.host.mention} has begun a game of **Word Chain: "
                                        f"{self.type}**\n Hit the \N{CROSSED SWORDS} to join!"))
        await join_msg.add_reaction('\N{CROSSED SWORDS}')

        # Wait 30 seconds for players to join the game
        def valid_player(reaction, user):
            return not user.bot and reaction.message.id == join_msg.id

        reaction = None
        while True:
            if str(reaction) == '\N{CROSSED SWORDS}':
                if not self.deny_repeats(self.players, user):
                    self.players.append(user)
                    await self.ctx.send(f'{user.mention} joined {self.host.display_name}\'s game.')

            try:
                reaction, user = await self.client.wait_for('reaction_add', 
                                                            timeout=15.0, 
                                                            check=valid_player)
            except asyncio.TimeoutError:
                await join_msg.delete()
                break

        if len(self.players) < 2:
            return await self.ctx.reply('Not enough players joined the game.')

    async def end_game(self, word_count : int):
        """End the game"""
        if self.type == 'Scrabble':
            # await self.ctx.send(self.points)
            high_score = 0
            winners = []
            for score in list(self.points.values()):
                if score > high_score:
                    high_score = score

            for player in list(self.points):
                if self.points[player] == high_score:
                    winners.append(player.mention)

            win_message = f"The winner(s) are {''.join(winners)}, with {high_score} points!\n\n"

            for player in self.players:
                win_message += f"{player.mention} : {self.points[player]} points\n"

            win_message += f"Players gave a collective {word_count} words."

            await self.ctx.send(win_message)

            # Input all players into database
            # This is a repeat of the above for-loop, but I thought it better to send the output
            # before making any database operations, which are invisible to the player
            async with self.db.acquire() as conn:
                for player in list(self.points): 
                    psql = """
                            INSERT INTO scrabble_wins (player, score)
                            VALUES ($1, $2)
                            """
                    await conn.execute(psql, player.id, self.points[player])

        else:
            await self.ctx.send((f"{self.players[0].mention} wins!\n"
                                 f"Players gave a collective {word_count} words."))

            # Now input winner into database (Public and Lightning Modes)
            async with self.db.acquire() as conn:
                if self.type == 'Public':
                    psql = """SELECT id FROM public_wins WHERE player = $1"""
                    in_db = await conn.fetchval(psql, self.players[0].id)
                    if in_db is not None: 
                        psql = """
                                UPDATE public_wins
                                SET win_amount = win_amount + 1
                                WHERE player = $1
                                """
                        await conn.execute(psql, self.players[0].id)
                    else:
                        psql = """
                                INSERT INTO public_wins (player)
                                VALUES ($1)
                                """
                        await conn.execute(psql, self.players[0].id)

                elif self.type == 'Lightning': # Why doesn't upsert work here?
                    # psql = """
                    #         INSERT INTO lightning_wins (player)
                    #         VALUES ($1)
                    #         ON CONFLICT (player)
                    #         DO UPDATE SET win_amount = win_amount + 1
                    #         """
                    # await conn.execute(psql, self.players[0].id)
                    psql = """SELECT id FROM lightning_wins WHERE player = $1"""
                    in_db = await conn.fetchval(psql, self.players[0].id)
                    if in_db is not None: 
                        psql = """
                                UPDATE lightning_wins
                                SET win_amount = win_amount + 1
                                WHERE player = $1
                                """
                        await conn.execute(psql, self.players[0].id)
                    else:
                        psql = """
                                INSERT INTO lightning_wins (player)
                                VALUES ($1)
                                """
                        await conn.execute(psql, self.players[0].id)

    async def input_solo_game(self, score : int):
        """Input game entry into database"""
        async with self.db.acquire() as conn:
            psql = """
                    INSERT INTO solo_wins (player, score)
                    VALUES ($1, $2)
                    """
            await conn.execute(psql, self.host.id, score)

    async def play_public(self):
        """Begin a public word chain game: Public, Lightning, or Scrabble rulesets."""
        # Let players join game
        await self.prompt_join()
        if len(self.players) < 2:
            return

        # Give game rules
        mentions = [player.mention for player in self.players]
        mention_str = "".join(mentions)

        game_rules = (f"**Welcome to Word Chain: {self.type}!** {mention_str}\n\n"
                      f"Word Chain is the ultimate test of your vocabulary. Each player must give "
                      f"a word that *begins* with the *last letter* of the prior person's own "
                      f"word. Each player has **{int(self.timeout)} seconds** to give a valid "
                      f"word.\nValid words are English, one string, and have no punctuation. "
                      f"Players are eliminated when they give an invalid word or time runs out."
                      f"\n\n")

        if self.type == 'Scrabble':
            game_rules += (f"In **Scrabble Mode**, each word you give will earn you a varying "
                           f"amount of points depending on the rarity of letters used. Try to "
                           f"come up with the longest word! Play continues until someone is "
                           f"eliminated; the winner is the player with the most points. "
                           f"Have fun! \n\n"
                           f"__Example:__ happy --> your --> rig --> guy... and so on")
        else:
            game_rules += (f"In **Public/Lightning** Mode, play continues until one person "
                           f"remains. Have fun!\n\n"
                           f"__Example:__ happy --> your --> rig --> guy... and so on")

        await self.ctx.send(game_rules)
        await asyncio.sleep(15)

        # Setup game
        used_words = []
        next_letter = random.choice(self.alphabet)

        self.points = {player : 0 for player in self.players}

        # Begin game loop

        while len(self.players) > 1: # Scrabble mode will break the loop manually
            if len(used_words) > 0 and self.type == 'Scrabble':
                prompt = await self.ctx.send((f"**{word}** was worth **{validity['points']}** "
                                            f"points!\n{self.players[0].mention}, give me a word "
                                            f"beginning with **{next_letter}**!"))
            else:
                prompt = await self.ctx.send((f"{self.players[0].mention}, give me a word beginning"
                                              f" with **{next_letter}**!"))

            def word_reader(message):
                return message.author == self.players[0] and message.channel == self.ctx.channel

            try:
                msg = await self.client.wait_for("message", timeout=self.timeout, check=word_reader)
                word = msg.content.lower()

                if word in used_words:
                    await self.ctx.reply(f'Word already used! | You have been eliminated.')

                    if self.type == 'Scrabble':
                        return await self.end_game(len(used_words))

                    self.players.pop(0)

                old_letter = next_letter
                validity = await self.valid_word(self.players[0], next_letter, word)
                if validity is not None:
                    next_letter = validity['next']
                    used_words.append(word)
                    self.players.append(self.players[0])
                    self.players.pop(0)
                else:
                    await self.ctx.reply(f'Invalid Word! | You have been eliminated.')
                    if self.type == 'Scrabble':
                        return await self.end_game(len(used_words))

                    self.players.pop(0)
                    next_letter = old_letter

            except asyncio.TimeoutError:
                await self.ctx.reply(f'Out of time! | You have been eliminated.')

                if self.type == 'Scrabble':
                    return await self.end_game(len(used_words))

                self.players.pop(0)        

            # await prompt.delete()
            # await msg.delete()

        await self.end_game(len(used_words))

    async def play_solo(self):
        """Begin a singleplayer word chain game: solo ruleset"""
        # Setup game
        used_words = []
        next_letter = random.choice(self.alphabet)

        # Begin game loop
        first_turn = True
        bot_word = None
        while True:
            # Prompt user to give a word
            if first_turn:
                prompt = await self.ctx.send((f"{self.host.mention}, give me a word beginning "
                                              f"with **{next_letter}**!"))
            else:
                prompt = await self.ctx.send((f"My Word: **{bot_word}**\n\n"
                                              f"{self.host.mention}, give me a word beginning "
                                              f"with **{next_letter}**!"))
            
            # Wait for player to give a word and check validity
            def word_reader(message):
                return message.author == self.host and message.channel == self.ctx.channel

            try:
                msg = await self.client.wait_for("message", timeout=self.timeout, check=word_reader)
                word = msg.content.lower()

                if word in used_words:
                    await self.ctx.reply((f"Word already used! | "
                                          f"Score: {int(len(used_words)/2)}"))
                    return await self.input_solo_game(int(len(used_words)/2))

                validity = await self.valid_word(self.host, next_letter, word)
                if validity is not None: # ONLY CASE IN WHICH PLAY CONTINUES
                    next_letter = validity['next']
                    used_words.append(word)
                else:
                    await self.ctx.reply(f'Invalid Word! | Score: {int(len(used_words)/2)}')
                    return await self.input_solo_game(int(len(used_words)/2))

            except asyncio.TimeoutError:
                await self.ctx.reply(f'Out of time! | Score: {int(len(used_words)/2)}')
                return await self.input_solo_game(int(len(used_words)/2))

            # Bot finds a word to respond with - word is printed at beginning of next loop
            first_turn = False

            # Bot first gets all words with the valid letter
            async with self.db.acquire() as conn:
                psql = """
                        SELECT word
                        FROM word_list
                        WHERE word LIKE $1
                        LIMIT 300;
                        """ # Change the limit to adjust difficulty
                possible_words = await conn.fetch(psql, f"{next_letter}%")

            bot_word = random.choice(possible_words)['word']

            if bot_word in used_words:
                await self.ctx.reply((f"I tried **{bot_word}** but it was already used!\n"
                                      f"You win! | Score : {int((len(used_words)+1)/2)}"))
                return await self.input_solo_game(int((len(used_words)+1)/2))
            
            next_letter = bot_word[-1]
            used_words.append(bot_word)

            # await prompt.delete()
            # await msg.delete()

class Minigames(commands.Cog):
    """Some fun minigames!"""

    def __init__(self, client):
        self.client = client
        self.active_channels = [] # Prevent multiple games in one channel

    #EVENTS
    @commands.Cog.listener() # needed to create event in cog
    async def on_ready(self): # YOU NEED SELF IN COGS
        print('Minigames is ready.')

    #COMMANDS
    @commands.group(aliases=['wc'], 
                    invoke_without_command=True, 
                    case_insensitive=True)
    async def wordchain(self, ctx):
        """Play the Word Chain minigame here!"""

        p = ctx.prefix
        wordchain_info = (f"**Welcome to Word Chain!**\n\n"
                          f"Word Chain is a game of vocabulary and speed. One player gives a word "
                          f"and the following player must give a word that begins with the last "
                          f"letter of the first person's word.\n\n"
                          f"For Example: 'hello' ends with 'o', so the next player can give "
                          f"the word 'olive'\n\n"
                          f"No character for Ayesha-proper is required to participate in Word "
                          f"Chain. Simply join the game and your games will be saved should you "
                          f"beat a record! This game currently only supports the English "
                          f"dictionary. You can find all the valid words under *words_alpha.txt* "
                          f"here: https://github.com/dwyl/english-words \n\n"
                          f"Browse the list of games here:\n"
                          f"1. `{p}wordchain solo` - Play against me!\n"
                          f"2. `{p}wordchain public` -  Begin a game with your friends; Play until "
                          f"death.\n"
                          f"3. `{p}wordchain lightning` - Shorter turn times\n"
                          f"4. `{p}wordchain scrabble` - Rather than playing by elimination, earn "
                          f"points by giving longer words!")

        await ctx.reply(wordchain_info)

    @wordchain.command(aliases=['s'])
    async def solo(self, ctx):
        """Play a game of word chain against me!"""
        self.active_channels.append(ctx.channel)
        new_game = WordChain(self.client, ctx, "Solo", self.client.en_dict)
        await new_game.play_solo()
        self.active_channels.remove(ctx.channel)

    @wordchain.command(aliases=['p','m','multiplayer'])
    async def public(self, ctx):
        """Start a multiplayer game with standard rules."""
        self.active_channels.append(ctx.channel)
        new_game = WordChain(self.client, ctx, "Public", self.client.en_dict)
        await new_game.play_public()
        self.active_channels.remove(ctx.channel)

    @wordchain.command(aliases=['l'])
    async def lightning(self, ctx):
        """Start a multiplayer game with a shorter time-limit than public."""
        self.active_channels.append(ctx.channel)
        new_game = WordChain(self.client, ctx, "Lightning", self.client.en_dict)
        await new_game.play_public()
        self.active_channels.remove(ctx.channel)

    @wordchain.command()
    async def scrabble(self, ctx):
        """Start a multiplayer game, gaining points based off letters used."""
        self.active_channels.append(ctx.channel)
        new_game = WordChain(self.client, ctx, "Scrabble", self.client.en_dict)
        await new_game.play_public()
        self.active_channels.remove(ctx.channel)

    @wordchain.command()
    async def help(self, ctx):
        """Get a list of all word-chain related commands!"""
        desc = 'Word Chain is fun.'
        helper = menus.MenuPages(source=PageMaker(PageMaker.paginate_help(ctx=ctx,
                                                                          command='wordchain',
                                                                          help_for='Word Chain',
                                                                          description=desc)), 
                                 clear_reactions_after=True, 
                                 delete_message_after=True)
        await helper.start(ctx)

    @solo.before_invoke
    @public.before_invoke
    @lightning.before_invoke
    @scrabble.before_invoke
    async def prevent_concurrency(self, ctx):
        if ctx.channel in self.active_channels:
            raise Checks.WordChainError

    @wordchain.command(aliases=['lb'])
    async def leaderboard(self, ctx, mode : str = None):
        """View the word chain leaderboards."""
        if mode is None:
            p = ctx.prefix
            await ctx.reply((f"`{p}wc lb solo` : View the highest scores for solo mode\n"
                             f"`{p}wc lb scrabble` : View the highest scores for scrabble mode\n"
                             f"`{p}wc lb public` : See who has the most wins in public mode\n"
                             f"`{p}wc lb lightning` : See who has the most wins in lightning mode"))
            return

        mode = mode.lower()

        if mode == 'scrabble':
            async with self.client.en_dict.acquire() as conn:
                psql1 = """
                            SELECT ROW_NUMBER() OVER(ORDER BY score DESC) AS rank, player, score
                            FROM scrabble_wins
                            LIMIT 10
                            """
                psql2 = """
                            WITH scrabble_ranks AS (
                                SELECT ROW_NUMBER() OVER(ORDER BY score DESC) AS rank, player, score
                                FROM scrabble_wins
                            )
                            SELECT rank, player, score
                            FROM scrabble_ranks
                            WHERE player = $1
                            LIMIT 1
                        """
                board = await conn.fetch(psql1)
                user_best = await conn.fetchrow(psql2, ctx.author.id)

            embed = discord.Embed(title='AyeshaBot Leaderboards',
                                  color=self.client.ayesha_blue)

            output = ''
            for entry in board:
                player = await self.client.fetch_user(entry['player'])
                output += f"**{entry['rank']} | {player.name}#{player.discriminator}**: "
                output += f"{entry['score']} points\n"

            embed.add_field(name='Word Chain Scrabble', value=output)

            try:
                embed.add_field(name='Your Personal Best',
                                value=f"**{user_best['rank']} | You**: {user_best['score']} points",
                                inline=False)

                await ctx.reply(embed=embed)
            except TypeError:
                await ctx.reply(embed=embed)

        if mode == 'solo':
            async with self.client.en_dict.acquire() as conn:
                psql1 = """
                            SELECT ROW_NUMBER() OVER(ORDER BY score DESC) AS rank, player, score
                            FROM solo_wins
                            LIMIT 5
                            """
                psql2 = """
                            WITH solo_ranks AS (
                                SELECT ROW_NUMBER() OVER(ORDER BY score DESC) AS rank, player, score
                                FROM solo_wins
                            )
                            SELECT rank, player, score
                            FROM solo_ranks
                            WHERE player = $1
                            LIMIT 1
                        """
                board = await conn.fetch(psql1)
                user_best = await conn.fetchrow(psql2, ctx.author.id)

            embed = discord.Embed(title='AyeshaBot Leaderboards',
                                  color=self.client.ayesha_blue)

            output = ''
            for entry in board:
                player = await self.client.fetch_user(entry['player'])
                output += f"**{entry['rank']} | {player.name}#{player.discriminator}**: "
                output += f"{entry['score']} words\n"

            embed.add_field(name='Word Chain Solo', value=output)

            try:
                embed.add_field(name='Your Personal Best',
                                value=f"**{user_best['rank']} | You**: {user_best['score']} words",
                                inline=False)

                await ctx.reply(embed=embed)
            except TypeError:
                await ctx.reply(embed=embed)

        if mode == 'public':
            async with self.client.en_dict.acquire() as conn:
                psql1 = """
                            SELECT ROW_NUMBER() OVER(ORDER BY win_amount DESC) AS rank, player, 
                                win_amount
                            FROM public_wins
                            LIMIT 5
                        """
                psql2 = """
                            WITH public_ranks AS (
                                SELECT ROW_NUMBER() OVER(ORDER BY win_amount DESC) AS rank, player, 
                                    win_amount
                                FROM public_wins
                            )
                            SELECT rank, player, win_amount
                            FROM public_ranks
                            WHERE player = $1
                        """

                board = await conn.fetch(psql1)
                user_best = await conn.fetchrow(psql2, ctx.author.id)

            embed = discord.Embed(title='AyeshaBot Leaderboards',
                                  color=self.client.ayesha_blue)

            output = ''
            for entry in board:
                player = await self.client.fetch_user(entry['player'])
                output += f"**{entry['rank']} | {player.name}#{player.discriminator}**: "
                output += f"{entry['win_amount']} wins\n"

            embed.add_field(name='Word Chain Public', value=output)

            try:
                embed.add_field(name='Your Personal Best',
                                value=(f"**{user_best['rank']} | You**: {user_best['win_amount']} "
                                       f"wins"),
                                inline=False)

                await ctx.reply(embed=embed)
            except TypeError:
                await ctx.reply(embed=embed)

        if mode == 'lightning':
            async with self.client.en_dict.acquire() as conn:
                psql1 = """
                            SELECT ROW_NUMBER() OVER(ORDER BY win_amount DESC) AS rank, player, 
                                win_amount
                            FROM lightning_wins
                            LIMIT 5
                        """
                psql2 = """
                            WITH lightning_ranks AS (
                                SELECT ROW_NUMBER() OVER(ORDER BY win_amount DESC) AS rank, player, 
                                    win_amount
                                FROM lightning_wins
                            )
                            SELECT rank, player, win_amount
                            FROM lightning_ranks
                            WHERE player = $1
                        """

                board = await conn.fetch(psql1)
                user_best = await conn.fetchrow(psql2, ctx.author.id)

            embed = discord.Embed(title='AyeshaBot Leaderboards',
                                  color=self.client.ayesha_blue)

            output = ''
            for entry in board:
                player = await self.client.fetch_user(entry['player'])
                output += f"**{entry['rank']} | {player.name}#{player.discriminator}**: "
                output += f"{entry['win_amount']} wins\n"

            embed.add_field(name='Word Chain Lightning', value=output)

            try:
                embed.add_field(name='Your Personal Best',
                                value=(f"**{user_best['rank']} | You**: {user_best['win_amount']} "
                                       f"wins"),
                                inline=False)

                await ctx.reply(embed=embed)
            except TypeError:
                await ctx.reply(embed=embed)

    @wordchain.command(name='check')
    async def _check(self, ctx, word : str):
        """See if a word exists in our database and how many points you'd earn for using it in 
        scrabble mode!
        """
        word = word.lower()
        psql = """SELECT id FROM word_list WHERE word = $1"""

        async with self.client.en_dict.acquire() as conn:
            word_id = await conn.fetchval(psql, word)

        if word_id is None:
            return await ctx.reply((f'**{word}** is not currently in our database.\nThink it '
                                    f'should be? Submit it for review with `%wc add`!'))
        else:
            word_score = sum([point_conversion[char] for char in word])
            await ctx.reply((f"**{word}** is a valid term for use in Word Chain!\nUsing it in "
                             f"Scrabble Mode would net you **{word_score}** points!"))

    @wordchain.command(aliases=['contest', 'add'])
    async def submit(self, ctx, word : str = None):
        """Lost on a word you think should be valid? Submit it here!"""
        if word is None:
            await ctx.reply((f"**Lost on a word you think should be valid? Submit it here!**\n\n"
                             f"Unfortunately, getting every little word in the English language "
                             f"is difficult. We apologize if you lost your potentially "
                             f"record-winning game due to using a word that wasn't in our "
                             f"database.\n\nIf you feel a word should be added in the database, "
                             f"please do `%wc add <word>` to add it to a list for review. "
                             f"There are, however, some guidelines to follow: "
                             f"1. All words are __alphabetic__, meaning each character in that "
                             f"word is one of the 26 letters. Hyphenated words such as 'x-ray' "
                             f"have been shortened to xray. Likewise, words with spaces like "
                             f"'a cappella' are simply 'acappella'.\n"
                             f"2. All words, even proper nouns, will become lowercase. Common "
                             f"first names such as 'John' are permissible to be added, but not "
                             f"last names or company names. Place names are also permissible.\n"
                             f"3. Commonly used slang terms are currently not included in the "
                             f"database. They can also be submitted for review.\n"
                             f"4. The character limit is 32 characters."))
            return

        # Make sure word could possibly be valid
        word = word.lower()

        if not word.isalpha():
            return await ctx.reply('Every character in this word must be one of 26 letters.')

        if len(word) > 32:
            return await ctx.reply('The character limit is 32 characters.')

        # See if word already exists in database
        psql = """SELECT id FROM word_list WHERE word = $1"""
        async with self.client.en_dict.acquire() as conn:
            if await conn.fetchval(psql, word) is not None:
                return await ctx.reply('The word you submitted is already in our database.')

            # Add it to list of words to be reviewed
            psql = """INSERT INTO word_review (word) VALUES ($1)"""
            await conn.execute(psql, word)
            await ctx.reply('Your word has been submitted for review.')
    
    @wordchain.command(aliases=['aa'])
    @commands.check(Checks.is_admin)
    async def admin_add(self, ctx, word : str = None):
        """There seems to be a little fungus among us."""
        if word is None:
            psql = """SELECT * FROM word_review LIMIT 10"""
            async with self.client.en_dict.acquire() as conn:
                word_list = await conn.fetch(psql)

            return await ctx.reply(word_list)

        if word.startswith('_reject:'): # _ as failsafe ; reject words in this fashion
            psql = """DELETE FROM word_review WHERE word = $1"""
            async with self.client.en_dict.acquire() as conn:
                await conn.execute(psql, word[8:])

            return await ctx.reply(f"Rejected word '{word[8:]}'")

        # Make sure word could possibly be valid
        word = word.lower()

        if not word.isalpha():
            return await ctx.reply('Every character in this word must be one of 26 letters.')

        if len(word) > 32:
            return await ctx.reply('The character limit is 32 characters.')

        # See if word already exists in database
        psql = """SELECT id FROM word_list WHERE word = $1"""
        async with self.client.en_dict.acquire() as conn:
            if await conn.fetchval(psql, word) is not None:
                return await ctx.reply('The word you submitted is already in our database.')

            # Add it to list of words to be reviewed
            psql = """INSERT INTO word_list (word) VALUES ($1)"""
            psql2 = """DELETE FROM word_review WHERE word = $1"""
            await conn.execute(psql, word)
            await conn.execute(psql2, word)
            await ctx.reply('Added to database.')

def setup(client):
    client.add_cog(Minigames(client))