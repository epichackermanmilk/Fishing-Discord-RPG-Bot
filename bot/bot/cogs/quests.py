# =============================================================
# OMEGA BOT — QUESTS COG
# Eternal River Sect
# /quests — view progress, claim rewards
# =============================================================
from __future__ import annotations

import logging
import math

import discord
from discord import app_commands
from discord.ext import commands

from bot.database import db
from bot.data.quest_data import QUESTS, QUEST_BY_ID, get_level, next_level
from bot.utils.formatters import fmt_stones, error_embed, success_embed, base_embed

log = logging.getLogger(__name__)

QUESTS_PER_PAGE = 6


class QuestsCog(commands.Cog, name="Quests"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── /quests ───────────────────────────────────────────────────────────────

    @app_commands.command(name="quests", description="View your quest progress.")
    @app_commands.describe(category="Filter by quest category")
    @app_commands.choices(category=[
        app_commands.Choice(name="All",         value="all"),
        app_commands.Choice(name="Fishing",     value="fishing"),
        app_commands.Choice(name="Collecting",  value="collecting"),
        app_commands.Choice(name="Selling",     value="selling"),
        app_commands.Choice(name="Adventure",   value="adventure"),
        app_commands.Choice(name="Cultivation", value="cultivation"),
        app_commands.Choice(name="Gambling",    value="gambling"),
    ])
    async def quests(self, interaction: discord.Interaction,
                     category: str = "all") -> None:
        user_id = interaction.user.id
        await db.get_or_create_user(user_id, str(interaction.user))

        # Load all quest DB rows
        quest_rows = await db.get_all_quest_progress(user_id)   # {quest_id: row}

        # Filter
        display_quests = QUESTS if category == "all" else [q for q in QUESTS if q["category"] == category]

        view  = QuestsView(interaction.user, quest_rows, display_quests)
        embed = view.build_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    # ── /quest claim ──────────────────────────────────────────────────────────

    @app_commands.command(name="quest_claim", description="Claim a completed quest reward.")
    @app_commands.describe(quest_id="Quest ID to claim (shown in /quests)")
    async def quest_claim(self, interaction: discord.Interaction, quest_id: str) -> None:
        user_id = interaction.user.id
        quest   = QUEST_BY_ID.get(quest_id)
        if not quest:
            await interaction.response.send_message(embed=error_embed(f"Unknown quest: `{quest_id}`"), ephemeral=True)
            return

        row = await db.get_quest_progress(user_id, quest_id)
        current_progress = row["current_progress"] if row else 0
        level_reached    = row["level_reached"]    if row else 0

        # Find claimable level
        next_lvl = get_level(quest, level_reached + 1)
        if not next_lvl:
            await interaction.response.send_message(embed=error_embed("This quest is already fully completed!"), ephemeral=True)
            return
        if current_progress < next_lvl["goal"]:
            await interaction.response.send_message(
                embed=error_embed(
                    f"Not yet! You need **{next_lvl['goal']:,}** to complete level {next_lvl['level']} "
                    f"(currently at **{current_progress:,}**)."
                ),
                ephemeral=True,
            )
            return

        # Claim
        await db.advance_quest_level(user_id, quest_id, level_reached + 1)
        await db.add_spirit_stones(user_id, next_lvl["reward_stones"])
        await db.add_fishing_xp(user_id, next_lvl["reward_xp"])

        embed = discord.Embed(
            title=f"✅ Quest Reward Claimed — {quest['name']}",
            description=(
                f"**Level {next_lvl['level']} Complete!**\n"
                f"{next_lvl['description']}\n\n"
                f"💎 +{fmt_stones(next_lvl['reward_stones'])}\n"
                f"⬆️ +{next_lvl['reward_xp']:,} Fishing XP"
            ),
            color=0xFFD700,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class QuestsView(discord.ui.View):
    def __init__(self, user: discord.User | discord.Member,
                 quest_rows: dict, quests: list[dict]):
        super().__init__(timeout=120.0)
        self.user       = user
        self.quest_rows = quest_rows
        self.quests     = quests
        self.page       = 0

    @property
    def max_page(self) -> int:
        return max(0, math.ceil(len(self.quests) / QUESTS_PER_PAGE) - 1)

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(title=f"📋 {self.user.display_name}'s Quests", color=0x3498DB)
        start = self.page * QUESTS_PER_PAGE
        chunk = self.quests[start:start + QUESTS_PER_PAGE]

        for quest in chunk:
            row     = self.quest_rows.get(quest["id"], {})
            prog    = row.get("current_progress", 0)
            lvl_done = row.get("level_reached", 0)
            max_lvl = len(quest["levels"])

            if lvl_done >= max_lvl:
                status = "🏆 COMPLETE"
                bar    = ""
            else:
                next_lvl = get_level(quest, lvl_done + 1)
                goal     = next_lvl["goal"] if next_lvl else 1
                pct      = min(1.0, prog / goal)
                filled   = int(pct * 10)
                bar      = f"\n`{'█'*filled}{'░'*(10-filled)}` {prog:,}/{goal:,}"
                ready    = "✅ **READY TO CLAIM**" if prog >= goal else ""
                status   = f"Level {lvl_done + 1}/{max_lvl}{' — ' + ready if ready else ''}"

            embed.add_field(
                name=f"{quest['name']}  [{status}]",
                value=f"{quest['description']}{bar}\n`/quest_claim {quest['id']}`",
                inline=False,
            )

        embed.set_footer(text=f"Page {self.page+1}/{self.max_page+1}  •  {len(self.quests)} quest(s)")
        self._update_buttons()
        return embed

    def _update_buttons(self):
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                if child.custom_id == "qprev":
                    child.disabled = (self.page == 0)
                elif child.custom_id == "qnext":
                    child.disabled = (self.page >= self.max_page)

    @discord.ui.button(label="◀", style=discord.ButtonStyle.secondary, custom_id="qprev")
    async def prev(self, interaction: discord.Interaction, _: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.defer(); return
        self.page -= 1
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="▶", style=discord.ButtonStyle.secondary, custom_id="qnext")
    async def next(self, interaction: discord.Interaction, _: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.defer(); return
        self.page += 1
        await interaction.response.edit_message(embed=self.build_embed(), view=self)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(QuestsCog(bot))
