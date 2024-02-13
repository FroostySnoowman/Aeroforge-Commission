import discord
import aiosqlite
import yaml
from discord import app_commands
from discord.ext import commands

with open('config.yml', 'r') as file:
    data = yaml.safe_load(file)

embed_color = data["General"]["EMBED_COLOR"]
unlock_role_id = data["Roles"]["UNLOCK_ROLE_ID"]

class UnlockCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="unlock", description="Unlocks a channel!")
    @app_commands.describe(locked_channel="What channel do you want to be unlocked?")
    async def unlock(self, interaction: discord.Interaction, locked_channel: discord.TextChannel) -> None:
        await interaction.response.defer(thinking=True, ephemeral=True)

        unlock_role = interaction.guild.get_role(unlock_role_id)
        if unlock_role in interaction.user.roles:
            async with aiosqlite.connect('database.db') as db:

                cursor = await db.execute('SELECT * FROM locked_channels WHERE channel_id=?', (locked_channel.id,))
                a = await cursor.fetchone()

                if a is None:
                    embed = discord.Embed(description=f"{locked_channel.mention} is not a locked channel!", color=discord.Color.red())
                else:
                    await db.execute('DELETE FROM locked_channels WHERE channel_id=?', (locked_channel.id, ))
                    await db.commit()
                    
                    embed = discord.Embed(description=f"Successfully unlocked {locked_channel.mention}!", color=discord.Color.from_str(embed_color))
        else:
            embed = discord.Embed(description=f"You do not have the {unlock_role.mention} role to use this command!", color=discord.Color.red())
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(UnlockCog(bot))
