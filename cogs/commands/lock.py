import discord
import aiosqlite
import yaml
from discord import app_commands
from discord.ext import commands

with open('config.yml', 'r') as file:
    data = yaml.safe_load(file)

embed_color = data["General"]["EMBED_COLOR"]
lock_role_id = data["Roles"]["LOCK_ROLE_ID"]

class EnterPasswordModal(discord.ui.Modal, title='Enter Password'):
    def __init__(self, bot: commands.Bot, channel_id: int, button_channel_id: int, button_channel_msg_id: int, password: str):
        super().__init__(timeout=None)
        self.bot = bot
        self.channel_id = channel_id
        self.button_channel_id = button_channel_id
        self.button_channel_msg_id = button_channel_msg_id
        self.password = password

    input_password = discord.ui.TextInput(
        label="What is the password?",
        placeholder='Type the password here...',
        max_length=4000,
        style=discord.TextStyle.short,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)

        if str(self.input_password.value) == str(self.password):
            try:
                channel = self.bot.get_channel(self.channel_id)
                overwrites = discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True)
                await channel.set_permissions(interaction.user, overwrite=overwrites)

                embed = discord.Embed(description=f"Successfully added you to {channel.mention}!", color=discord.Color.from_str(embed_color))
            except:
                embed = discord.Embed("Failed to add you to the channel. Please report this error! \n\nError Code: **1**", color=discord.Color.red())
        else:
            embed = discord.Embed(description="Incorrect password!", color=discord.Color.red())
        
        await interaction.followup.send(embed=embed)

class EnterPasswordButton(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
    
    @discord.ui.button(label='Enter Password', style=discord.ButtonStyle.gray, custom_id='enter_password:1')
    async def enter_password(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with aiosqlite.connect('database.db') as db:
            cursor = await db.execute('SELECT * FROM locked_channels WHERE button_channel_msg_id = ?', (interaction.message.id,))
            a = await cursor.fetchone()
            if a is None:
                embed = discord.Embed(description="This button is invalid! Deleting...", color=discord.Color.red())
                await interaction.message.delete()
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_modal(EnterPasswordModal(self.bot, a[0], a[1], a[2], a[3]))

class LockCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.bot.add_view(EnterPasswordButton(self.bot))

    @app_commands.command(name="lock", description="Locks a channel!")
    @app_commands.describe(locked_channel="What channel do you want to be locked?")
    @app_commands.describe(button_channel="Where should the password button be placed?")
    @app_commands.describe(password="What is the password for that channel?")
    async def lock(self, interaction: discord.Interaction, locked_channel: discord.TextChannel, button_channel: discord.TextChannel, password: int) -> None:
        await interaction.response.defer(thinking=True, ephemeral=True)

        lock_role = interaction.guild.get_role(lock_role_id)
        if lock_role in interaction.user.roles:
            async with aiosqlite.connect('database.db') as db:

                embed = discord.Embed(title="Locked Channel", description=f"Enter the password for {locked_channel.name}!", color=discord.Color.from_str(embed_color))
                button_channel_msg = await button_channel.send(embed=embed, view=EnterPasswordButton(self.bot))

                embed = discord.Embed(description=f"Successfully locked {locked_channel.mention}, set the button channel to {button_channel.mention}, and set the password to ||**{password}**||!", color=discord.Color.from_str(embed_color))
                await db.execute('INSERT INTO locked_channels VALUES (?,?,?,?);', (locked_channel.id, button_channel.id, button_channel_msg.id, password))

                await db.commit()
        else:
            embed = discord.Embed(description=f"You do not have the {lock_role.mention} role to use this command!", color=discord.Color.red())
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(LockCog(bot))