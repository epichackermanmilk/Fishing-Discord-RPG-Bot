# =============================================================
# OMEGA BOT — GAMBLING COG
# Eternal River Sect
# /gamble buy, /gamble use, /gamble tickets
# 20-button interactive scratch tickets
# =============================================================
from __future__ import annotations

import json
import logging
import random

import discord
from discord import app_commands
from discord.ext import commands

from bot.database import db
from bot.data.scratch_data import TICKET_TIERS, TICKET_ORDER, get_ticket, evaluate_ticket
from bot.utils.formatters  import fmt_stones, error_embed, success_embed

log = logging.getLogger(__name__)

SCRATCH_ROWS    = 4
SCRATCH_COLS    = 5
SCRATCH_TOTAL   = SCRATCH_ROWS * SCRATCH_COLS   # 20 spots


# ──────────────────────────────────────────────────────────────────────────────
# GENERATE TICKET
# ──────────────────────────────────────────────────────────────────────────────

def _generate_ticket(tier_id: str) -> tuple[list[int], list[int]]:
    """Return (win_numbers, scratch_numbers) sampled without replacement from 1-45."""
    tier          = TICKET_TIERS[tier_id]
    pool          = list(range(1, tier["win_pool"] + 1))
    random.shuffle(pool)
    win_numbers   = pool[:tier["win_count"]]
    scratch_numbers = pool[:tier["scratch_count"]]
    # Ensure scratch numbers are shuffled independently
    scratch_pool = list(range(1, tier["win_pool"] + 1))
    random.shuffle(scratch_pool)
    scratch_numbers = scratch_pool[:tier["scratch_count"]]
    return win_numbers, scratch_numbers


# ──────────────────────────────────────────────────────────────────────────────
# SCRATCH TICKET VIEW (20 buttons)
# ──────────────────────────────────────────────────────────────────────────────

class ScratchView(discord.ui.View):
    """
    Renders 20 scratch spots as buttons (4 rows × 5 columns).
    Each click reveals a spot — green if match, grey if not.
    All 20 must be revealed for prize to pay out.
    """

    def __init__(self, ticket_id: int, tier_id: str,
                 win_numbers: list[int], scratch_numbers: list[int],
                 revealed_spots: list[int], user_id: int):
        super().__init__(timeout=300.0)   # 5 minutes
        self.ticket_id      = ticket_id
        self.tier_id        = tier_id
        self.win_numbers    = win_numbers
        self.scratch_numbers = scratch_numbers
        self.revealed       = set(revealed_spots)
        self.user_id        = user_id
        self.win_set        = set(win_numbers)
        self._rebuild_buttons()

    def _rebuild_buttons(self):
        self.clear_items()
        for idx in range(SCRATCH_TOTAL):
            revealed = idx in self.revealed
            value    = self.scratch_numbers[idx] if revealed else None
            is_match = revealed and value in self.win_set

            btn = discord.ui.Button(
                label=str(value) if revealed else "?",
                style=(
                    discord.ButtonStyle.success if is_match else
                    discord.ButtonStyle.secondary if revealed else
                    discord.ButtonStyle.primary
                ),
                disabled=revealed,
                row=idx // SCRATCH_COLS,
                custom_id=f"scratch_{self.ticket_id}_{idx}",
            )
            btn.callback = self._make_callback(idx)
            self.add_item(btn)

    def _make_callback(self, spot_index: int):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("This isn't your ticket!", ephemeral=True)
                return
            if spot_index in self.revealed:
                await interaction.response.defer()
                return

            self.revealed.add(spot_index)
            await db.update_ticket_revealed(self.ticket_id, list(self.revealed))

            result = evaluate_ticket(
                self.tier_id, self.win_numbers,
                list(self.revealed), self.scratch_numbers,
            )

            self._rebuild_buttons()

            if result["is_complete"]:
                await db.mark_ticket_opened(self.ticket_id, result["prize"])
                # Pay out
                if result["prize"] > 0:
                    await db.add_spirit_stones(self.user_id, result["prize"])
                    await db.increment_quest_progress(self.user_id, "gambler", 1)

                embed = self._build_result_embed(result)
                self.stop()
                await interaction.response.edit_message(embed=embed, view=None)
            else:
                embed = self._build_progress_embed(result)
                await interaction.response.edit_message(embed=embed, view=self)

        return callback

    def _build_progress_embed(self, result: dict) -> discord.Embed:
        tier  = TICKET_TIERS[self.tier_id]
        embed = discord.Embed(
            title=f"{tier['emoji']} {tier['name']} — Scratching...",
            color=tier["color"],
        )
        embed.add_field(name="Matches Found",     value=str(result["matches"]),  inline=True)
        embed.add_field(name="Spots Remaining",   value=str(SCRATCH_TOTAL - len(self.revealed)), inline=True)
        embed.add_field(name="Winning Numbers",   value=" · ".join(str(n) for n in sorted(self.win_numbers)), inline=False)
        embed.set_footer(text="Click all spots to reveal your prize!")
        return embed

    def _build_result_embed(self, result: dict) -> discord.Embed:
        tier  = TICKET_TIERS[self.tier_id]
        if result["is_winner"]:
            embed = discord.Embed(
                title=f"🎉 {tier['emoji']} {tier['name']} — WINNER!",
                description=(
                    f"You matched **{result['matches']}** number(s)!\n"
                    f"Prize: **{fmt_stones(result['prize'])}** deposited to your account!"
                ),
                color=0xFFD700,
            )
        else:
            embed = discord.Embed(
                title=f"{tier['emoji']} {tier['name']} — No Match",
                description=(
                    f"You matched **0** numbers.\n"
                    f"Better fortune awaits in your next ticket."
                ),
                color=0x7F8C8D,
            )
        embed.add_field(name="Winning Numbers", value=" · ".join(str(n) for n in sorted(self.win_numbers)), inline=False)
        return embed


# ──────────────────────────────────────────────────────────────────────────────
# GAMBLING COG
# ──────────────────────────────────────────────────────────────────────────────

class GamblingCog(commands.Cog, name="Gambling"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    gamble_group = app_commands.Group(name="gamble", description="Fortune House commands.")

    async def _check_gambling_channel(self, interaction: discord.Interaction) -> bool:
        from bot.database import db
        row = await db.get_channel_config(interaction.channel_id)
        if row and row["channel_type"] == "gambling":
            return True
        await interaction.response.send_message(
            "🎰 Gambling commands can only be used in the **Fortune House** channel.",
            ephemeral=True,
        )
        return False

    # ── /gamble buy ───────────────────────────────────────────────────────────

    @gamble_group.command(name="buy", description="Purchase a scratch ticket.")
    @app_commands.describe(tier="Ticket tier to purchase")
    @app_commands.choices(tier=[
        app_commands.Choice(name="📜 Qi Slip (150 SS)",           value="slip"),
        app_commands.Choice(name="📖 Spirit Scroll (600 SS)",     value="scroll"),
        app_commands.Choice(name="📕 Heavenly Decree (2,500 SS)", value="decree"),
    ])
    async def gamble_buy(self, interaction: discord.Interaction, tier: str) -> None:
        if not await self._check_gambling_channel(interaction):
            return

        ticket_def = get_ticket(tier)
        if not ticket_def:
            await interaction.response.send_message(embed=error_embed("Invalid ticket tier."), ephemeral=True)
            return

        user_id = interaction.user.id
        await db.get_or_create_user(user_id, str(interaction.user))

        ok = await db.spend_spirit_stones(user_id, ticket_def["price"])
        if not ok:
            await interaction.response.send_message(
                embed=error_embed(f"Need {fmt_stones(ticket_def['price'])} to buy a {ticket_def['name']}."),
                ephemeral=True,
            )
            return

        win_numbers, scratch_numbers = _generate_ticket(tier)
        ticket_id = await db.create_scratch_ticket(
            user_id=user_id,
            tier=tier,
            win_numbers=win_numbers,
            scratch_numbers=scratch_numbers,
        )

        await interaction.response.send_message(
            embed=success_embed(
                f"Purchased {ticket_def['emoji']} **{ticket_def['name']}**!\n"
                f"Ticket ID: `#{ticket_id}`\n"
                f"Use it with `/gamble use {ticket_id}`."
            ),
            ephemeral=True,
        )

    # ── /gamble use ───────────────────────────────────────────────────────────

    @gamble_group.command(name="use", description="Scratch a ticket you own.")
    @app_commands.describe(ticket_id="Ticket ID (from /gamble tickets or buy confirmation)")
    async def gamble_use(self, interaction: discord.Interaction, ticket_id: int) -> None:
        if not await self._check_gambling_channel(interaction):
            return

        user_id = interaction.user.id
        ticket  = await db.get_scratch_ticket(ticket_id, user_id)
        if not ticket:
            await interaction.response.send_message(
                embed=error_embed(f"No ticket #{ticket_id} found in your account."), ephemeral=True)
            return
        if ticket["opened"]:
            await interaction.response.send_message(
                embed=error_embed(f"Ticket #{ticket_id} has already been scratched."), ephemeral=True)
            return

        tier_id          = ticket["tier"]
        win_numbers      = json.loads(ticket["win_numbers"])
        scratch_numbers  = json.loads(ticket["scratch_numbers"])
        revealed_spots   = json.loads(ticket["revealed_spots"])

        tier = TICKET_TIERS[tier_id]
        result = evaluate_ticket(tier_id, win_numbers, revealed_spots, scratch_numbers)

        view  = ScratchView(ticket_id, tier_id, win_numbers, scratch_numbers, revealed_spots, user_id)
        embed = discord.Embed(
            title=f"{tier['emoji']} {tier['name']}  •  Ticket #{ticket_id}",
            description=(
                f"*{tier['flavor']}*\n\n"
                f"**Winning Numbers:** {' · '.join(str(n) for n in sorted(win_numbers))}\n"
                f"Click the buttons below to scratch your spots!"
            ),
            color=tier["color"],
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

    # ── /gamble tickets ───────────────────────────────────────────────────────

    @gamble_group.command(name="tickets", description="View your unscratched tickets.")
    async def gamble_tickets(self, interaction: discord.Interaction) -> None:
        user_id = interaction.user.id
        tickets = await db.get_unscratched_tickets(user_id)

        if not tickets:
            await interaction.response.send_message(
                embed=error_embed("You have no unscratched tickets. Buy some with `/gamble buy`!"),
                ephemeral=True,
            )
            return

        embed = discord.Embed(title="🎰 Your Unscratched Tickets", color=0xE74C3C)
        for t in tickets[:25]:
            tier = TICKET_TIERS.get(t["tier"], {})
            embed.add_field(
                name=f"{tier.get('emoji','🎟️')} #{t['id']} — {tier.get('name', t['tier'])}",
                value=f"Purchased <t:{int(t['created_at'])}:R>\nUse: `/gamble use {t['id']}`",
                inline=True,
            )
        embed.set_footer(text=f"{len(tickets)} ticket(s) waiting  •  Use /gamble use <id>")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GamblingCog(bot))
