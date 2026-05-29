# =============================================================
# OMEGA BOT — INVENTORY COG
# Eternal River Sect
# /inventory — paginated, tabbed fish/gear viewer
# =============================================================
from __future__ import annotations

import math
import logging

import discord
from discord import app_commands
from discord.ext import commands

from bot.database import db
from bot.data.fish_data import FISH_BY_ID, QUALITY_TIERS, get_size_multiplier
from bot.data.rod_data  import get_rod
from bot.data.bait_data import get_bait, get_max_stack
from bot.data.lure_data import get_lure
from bot.utils.formatters import (
    fmt_stones, fmt_quality, fmt_size, base_embed, error_embed,
)

log = logging.getLogger(__name__)

ITEMS_PER_PAGE = 10

CATEGORY_LABELS = {
    "freshwater": "🟢 Freshwater Fish",
    "saltwater":  "🌊 Saltwater Fish",
    "elemental":  "⚡ Elemental Fish",
    "junk":       "🗑️ Junk & Misc",
    "misc":       "🗑️ Junk & Misc",
    "gear":       "🎣 Gear",
}

# ──────────────────────────────────────────────────────────────────────────────
# PAGINATED INVENTORY VIEW
# ──────────────────────────────────────────────────────────────────────────────

class InventoryView(discord.ui.View):
    """
    Tabbed + paginated inventory viewer.
    Tab buttons switch between fish categories.
    Prev/Next navigate within the current category.
    """

    FISH_CATEGORIES = ["freshwater", "saltwater", "elemental", "junk"]

    def __init__(self, user_id: int, user: discord.User | discord.Member):
        super().__init__(timeout=120.0)
        self.user_id  = user_id
        self.user     = user
        self.category = "freshwater"
        self.page     = 0
        self._cache: dict[str, list[dict]] = {}

    # ── Data loading ──────────────────────────────────────────────────────────

    async def load_category(self, category: str) -> list[dict]:
        if category in self._cache:
            return self._cache[category]

        if category == "gear":
            data = await self._load_gear()
        else:
            raw = await db.get_fish_inventory(self.user_id, category=category)
            data = []
            for row in raw:
                fish_def = FISH_BY_ID.get(row["species_id"], {})
                _, size_label = get_size_multiplier(row["size"], fish_def.get("avg_size", row["size"]))
                data.append({
                    "id":         row["id"],
                    "name":       fish_def.get("name", row["species_id"]),
                    "quality":    row["quality"],
                    "size":       row["size"],
                    "size_label": size_label,
                    "avg_size":   fish_def.get("avg_size", row["size"]),
                    "value":      row["value"],
                    "caught_at":  row["caught_at"],
                })

        self._cache[category] = data
        return data

    async def _load_gear(self) -> list[dict]:
        row      = await db.get_user(self.user_id)
        upgr     = await db.get_rod_upgrades(self.user_id) or {}
        stock    = await db.get_bait_stock(self.user_id)
        owned_rs = await db.get_owned_rod_ids(self.user_id)
        owned_ls = await db.get_owned_lure_ids(self.user_id)

        items = []
        # Active rod
        rod = get_rod(row["rod_id"])
        if rod:
            items.append({"type": "rod", "name": rod["name"], "status": "✅ Equipped",
                          "detail": f"Tier {rod['tier']}  •  Cooldown: {rod['base_cooldown']:.0f}s"})
        # Other owned rods
        for rid in owned_rs:
            if rid != row["rod_id"]:
                r = get_rod(rid)
                if r:
                    items.append({"type": "rod", "name": r["name"], "status": "📦 Stored",
                                  "detail": f"Tier {r['tier']}"})
        # Active lure
        lure = get_lure(row["lure_id"])
        if lure:
            items.append({"type": "lure", "name": lure["name"], "status": "✅ Equipped",
                          "detail": f"Tier {lure['tier']}"})
        # Other lures
        for lid in owned_ls:
            if lid != row["lure_id"]:
                l = get_lure(lid)
                if l:
                    items.append({"type": "lure", "name": l["name"], "status": "📦 Stored",
                                  "detail": f"Tier {l['tier']}"})
        # Bait stock
        for bait_id, qty in stock.items():
            if qty > 0:
                b = get_bait(bait_id)
                if b:
                    active = "✅ Active  " if bait_id == row["bait_id"] else ""
                    items.append({"type": "bait", "name": b["name"],
                                  "status": f"{active}×{qty}",
                                  "detail": f"Tier {b['tier']}"})
        return items

    # ── Embed builder ─────────────────────────────────────────────────────────

    async def build_embed(self) -> discord.Embed:
        data     = await self.load_category(self.category)
        total    = len(data)
        max_page = max(0, math.ceil(total / ITEMS_PER_PAGE) - 1)
        self.page = min(self.page, max_page)

        start = self.page * ITEMS_PER_PAGE
        end   = start + ITEMS_PER_PAGE
        chunk = data[start:end]

        cat_label = CATEGORY_LABELS.get(self.category, self.category.capitalize())
        embed = discord.Embed(
            title=f"📦 {self.user.display_name}'s Inventory — {cat_label}",
            color=0x2ECC71,
        )

        if not chunk:
            embed.description = "*Nothing here.*"
        elif self.category == "gear":
            lines = []
            for item in chunk:
                icon = {"rod": "🎣", "lure": "🪝", "bait": "🪱"}.get(item["type"], "•")
                lines.append(f"{icon} **{item['name']}** — {item['status']}  *{item['detail']}*")
            embed.description = "\n".join(lines)
        else:
            lines = []
            for item in chunk:
                qual_str = fmt_quality(item["quality"])
                lines.append(
                    f"`#{item['id']:>5}` **{item['name']}**\n"
                    f"    {qual_str} · {item['size_label']} ({fmt_size(item['size'])}) · {fmt_stones(item['value'])}"
                )
            embed.description = "\n".join(lines)
            # Show total value of visible fish
            visible_val = sum(i["value"] for i in chunk)
            all_val     = sum(i["value"] for i in data)
            embed.add_field(
                name="Page Value",
                value=f"{fmt_stones(visible_val)} (page)  •  {fmt_stones(all_val)} (tab total)",
                inline=False,
            )

        embed.set_footer(
            text=f"Page {self.page+1}/{max(1, max_page+1)}  •  {total} item(s)"
                 + ("\n⚠️ Sell All only sells fish shown in the Fish tabs, not gear." if self.category in self.FISH_CATEGORIES else "")
        )
        self._update_buttons(max_page)
        return embed

    def _update_buttons(self, max_page: int):
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                if child.custom_id == "prev":
                    child.disabled = (self.page == 0)
                elif child.custom_id == "next":
                    child.disabled = (self.page >= max_page)

    # ── Buttons ───────────────────────────────────────────────────────────────

    @discord.ui.button(label="◀ Prev", style=discord.ButtonStyle.secondary, custom_id="prev", row=1)
    async def prev_page(self, interaction: discord.Interaction, _: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.defer()
            return
        self.page = max(0, self.page - 1)
        embed = await self.build_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary, custom_id="next", row=1)
    async def next_page(self, interaction: discord.Interaction, _: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.defer()
            return
        self.page += 1
        embed = await self.build_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    # Tab buttons
    @discord.ui.button(label="🟢 Freshwater", style=discord.ButtonStyle.success, row=0)
    async def tab_fw(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self._switch_tab(interaction, "freshwater")

    @discord.ui.button(label="🌊 Saltwater", style=discord.ButtonStyle.primary, row=0)
    async def tab_sw(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self._switch_tab(interaction, "saltwater")

    @discord.ui.button(label="⚡ Elemental", style=discord.ButtonStyle.danger, row=0)
    async def tab_el(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self._switch_tab(interaction, "elemental")

    @discord.ui.button(label="🗑️ Junk", style=discord.ButtonStyle.secondary, row=0)
    async def tab_junk(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self._switch_tab(interaction, "junk")

    @discord.ui.button(label="🎣 Gear", style=discord.ButtonStyle.secondary, row=0)
    async def tab_gear(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self._switch_tab(interaction, "gear")

    async def _switch_tab(self, interaction: discord.Interaction, category: str):
        if interaction.user.id != self.user_id:
            await interaction.response.defer()
            return
        self.category = category
        self.page     = 0
        embed = await self.build_embed()
        await interaction.response.edit_message(embed=embed, view=self)


# ──────────────────────────────────────────────────────────────────────────────
# INVENTORY COG
# ──────────────────────────────────────────────────────────────────────────────

class InventoryCog(commands.Cog, name="Inventory"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="inventory", description="View your fish inventory and gear.")
    @app_commands.describe(member="View another member's inventory (read-only)")
    async def inventory(self, interaction: discord.Interaction,
                        member: discord.Member | None = None) -> None:
        target = member or interaction.user
        await db.get_or_create_user(target.id, str(target))

        view  = InventoryView(target.id, target)
        embed = await view.build_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=(member is None))


# ──────────────────────────────────────────────────────────────────────────────
# COG SETUP
# ──────────────────────────────────────────────────────────────────────────────

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(InventoryCog(bot))
