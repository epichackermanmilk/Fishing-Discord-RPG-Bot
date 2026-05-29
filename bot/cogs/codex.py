# =============================================================
# OMEGA BOT — CODEX COG
# Eternal River Sect
# /codex — browse all discovered fish species
# =============================================================
from __future__ import annotations

import math
import logging

import discord
from discord import app_commands
from discord.ext import commands

from bot.database import db
from bot.data.fish_data import FISH, FISH_BY_ID, QUALITY_TIERS, QUALITY_DISPLAY
from bot.utils.formatters import (
    fmt_quality, fmt_size, fmt_stones, base_embed, error_embed,
    quality_color,
)

log = logging.getLogger(__name__)

CODEX_PER_PAGE = 8


class CodexCog(commands.Cog, name="Codex"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── /codex ────────────────────────────────────────────────────────────────

    @app_commands.command(name="codex", description="Browse your fish codex.")
    @app_commands.describe(
        filter_cat="Filter by category",
        member="View another member's codex",
    )
    @app_commands.choices(filter_cat=[
        app_commands.Choice(name="All",        value="all"),
        app_commands.Choice(name="Freshwater", value="freshwater"),
        app_commands.Choice(name="Saltwater",  value="saltwater"),
        app_commands.Choice(name="Elemental",  value="elemental"),
        app_commands.Choice(name="Junk",       value="junk"),
    ])
    async def codex(self, interaction: discord.Interaction,
                    filter_cat: str = "all",
                    member: discord.Member | None = None) -> None:
        target = member or interaction.user
        await db.get_or_create_user(target.id, str(target))

        codex_rows = await db.get_full_codex(target.id)          # {species_id: row}
        total_species = len(FISH)
        discovered    = len(codex_rows)

        # Filter fish list
        all_fish = FISH if filter_cat == "all" else [f for f in FISH if f["category"] == filter_cat]

        view  = CodexView(target, codex_rows, all_fish, discovered, total_species)
        embed = view.build_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=(member is None))

    # ── /codex species ────────────────────────────────────────────────────────

    @app_commands.command(name="species", description="Detailed codex entry for a specific fish.")
    @app_commands.describe(name="Species name (e.g. Jade River Carp)")
    async def species(self, interaction: discord.Interaction, name: str) -> None:
        fish_def = next((f for f in FISH if f["name"].lower() == name.lower()), None)
        if not fish_def:
            await interaction.response.send_message(embed=error_embed(f"Unknown species: **{name}**"), ephemeral=True)
            return

        user_id = interaction.user.id
        await db.get_or_create_user(user_id, str(interaction.user))
        row = await db.get_codex_entry(user_id, fish_def["id"])

        if not row or row["caught_count"] == 0:
            # Not yet discovered — reveal nothing
            embed = discord.Embed(
                title="❓ Undiscovered Species",
                description=(
                    "This species has not yet been recorded in your codex.\n\n"
                    "*Cast your line and explore different waters — all secrets reveal themselves to the patient fisher.*"
                ),
                color=0x7F8C8D,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(
            title=f"📖 {fish_def['name']}",
            color=0x2ECC71,
        )
        embed.add_field(name="Category", value=fish_def["category"].capitalize(), inline=True)
        embed.add_field(name="Tier",     value=f"{'⭐'*fish_def['tier'] if fish_def['tier']>0 else '🗑️'}", inline=True)
        embed.add_field(name="Avg Size", value=fmt_size(fish_def["avg_size"]), inline=True)

        embed.add_field(name="Times Caught", value=str(row["caught_count"]), inline=True)
        embed.add_field(name="Best Quality", value=fmt_quality(row["best_quality"]) if row["best_quality"] else "—", inline=True)
        embed.add_field(name="Largest",      value=fmt_size(row["largest_size"]) if row["largest_size"] else "—", inline=True)
        embed.add_field(name="Smallest",     value=fmt_size(row["smallest_size"]) if row["smallest_size"] else "—", inline=True)
        embed.add_field(name="Most Valuable",value=fmt_stones(row["largest_value"]) if row["largest_value"] else "—", inline=True)

        biomes = ", ".join(b.replace("freshwater", "FW").replace("saltwater", "SW")
                           .replace("special", "SP").replace("secret", "Secret") for b in fish_def["biomes"])
        embed.add_field(name="Found In", value=biomes, inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class CodexView(discord.ui.View):
    def __init__(self, user: discord.User | discord.Member, codex: dict,
                 fish_list: list[dict], discovered: int, total: int):
        super().__init__(timeout=120.0)
        self.user       = user
        self.codex      = codex
        self.fish_list  = fish_list
        self.discovered = discovered
        self.total      = total
        self.page       = 0

    @property
    def max_page(self) -> int:
        return max(0, math.ceil(len(self.fish_list) / CODEX_PER_PAGE) - 1)

    def build_embed(self) -> discord.Embed:
        pct   = self.discovered / self.total * 100 if self.total else 0
        embed = discord.Embed(
            title=f"📚 {self.user.display_name}'s Codex",
            description=(
                f"**Discovered:** {self.discovered}/{self.total} species  ({pct:.1f}%)\n​"
            ),
            color=0x3498DB,
        )
        start = self.page * CODEX_PER_PAGE
        chunk = self.fish_list[start:start + CODEX_PER_PAGE]

        for fish in chunk:
            row = self.codex.get(fish["id"])
            if row and row["caught_count"] > 0:
                embed.add_field(
                    name=f"{'⭐'*fish['tier'] if fish['tier']>0 else '🗑️'} {fish['name']}",
                    value=(
                        f"✅ Caught ×{row['caught_count']}  "
                        f"| Best: {fmt_quality(row['best_quality'])}  "
                        f"| Largest: {fmt_size(row['largest_size'])}"
                    ),
                    inline=False,
                )
            else:
                embed.add_field(
                    name="❓ ???",
                    value="🔒 *Undiscovered — catch it to reveal!*",
                    inline=False,
                )

        embed.set_footer(text=f"Page {self.page+1}/{self.max_page+1}  •  /species <name> for details")
        self._update_buttons()
        return embed

    def _update_buttons(self):
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                if child.custom_id == "cprev":
                    child.disabled = (self.page == 0)
                elif child.custom_id == "cnext":
                    child.disabled = (self.page >= self.max_page)

    @discord.ui.button(label="◀ Prev", style=discord.ButtonStyle.secondary, custom_id="cprev")
    async def prev(self, interaction: discord.Interaction, _: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.defer(); return
        self.page -= 1
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary, custom_id="cnext")
    async def next(self, interaction: discord.Interaction, _: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.defer(); return
        self.page += 1
        await interaction.response.edit_message(embed=self.build_embed(), view=self)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CodexCog(bot))
