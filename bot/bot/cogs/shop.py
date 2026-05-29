# =============================================================
# OMEGA BOT — SHOP COG
# Eternal River Sect
# /shop, /buy, /equip, /upgrade, /sell
# =============================================================
from __future__ import annotations

import logging
import math

import discord
from discord import app_commands
from discord.ext import commands

from bot.database import db
from bot.data.bait_data  import BAITS, BAIT_ORDER, get_bait, get_max_stack, MAX_BAIT_BONUS
from bot.data.lure_data  import LURES, LURE_ORDER, get_lure
from bot.data.rod_data   import (RODS, ROD_ORDER, get_rod,
                                  REEL_SPEED_REDUCTION, XP_BONUS_DELTA, ROD_LUCK_BONUS,
                                  effective_cooldown, effective_xp_bonus, effective_pouch_luck)
from bot.utils.checks    import app_is_shop_channel, app_is_fishing_channel
from bot.utils.formatters import (
    fmt_stones, fmt_quality, base_embed, error_embed, success_embed, fmt_number,
)

log = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Breakthrough pill prices (base cost; doubles per failure via DB)
# ──────────────────────────────────────────────────────────────────────────────

PILL_BASE_PRICES = {
    1: 500,      # Qi Condensation pill
    2: 1_500,    # Foundation Establishment
    3: 4_500,    # Golden Core
    4: 12_000,   # Nascent Soul
    5: 35_000,   # Spirit Severing
    6: 90_000,   # Void Crossing
    7: 250_000,  # Dao Manifestation
    8: 700_000,  # Immortal Ascension
    9: 2_000_000,# Eternal Sovereign
}

PILL_NAMES = {
    1: "Qi Condensation Pill",
    2: "Foundation Establishment Pill",
    3: "Golden Core Consolidation Pill",
    4: "Nascent Soul Gestation Pill",
    5: "Spirit Severing Pill",
    6: "Void Crossing Enlightenment Pill",
    7: "Dao Manifestation Pill",
    8: "Immortal Ascension Pill",
    9: "Eternal Sovereign Pill",
}

# Rod upgrade costs per tier (cumulative — total to reach that tier)
UPGRADE_COSTS = {
    "reel_speed": [0, 800, 2_000, 4_500, 10_000, 25_000],
    "xp_bonus":   [0, 400, 1_000, 2_000, 3_500, 5_500, 8_500, 13_000, 20_000, 32_000],
    "rod_luck":   [0, 600, 1_500, 3_500, 8_000, 20_000],
    "max_bait":   [0, 300, 700,  1_400, 2_500, 4_000, 6_500, 10_000, 15_000, 24_000],
}

UPGRADE_LABELS = {
    "reel_speed": "Reel Speed",
    "xp_bonus":   "XP Bonus",
    "rod_luck":   "Rod Luck",
    "max_bait":   "Max Bait",
}


# ──────────────────────────────────────────────────────────────────────────────
# SHOP EMBED BUILDERS
# ──────────────────────────────────────────────────────────────────────────────

def _rod_shop_embed(owned_rod_ids: list[str], current_rod_id: str) -> discord.Embed:
    embed = discord.Embed(title="🎣 Rods — Spirit Stone Market", color=0x2ECC71)
    for rod in RODS:
        owned = rod["id"] in owned_rod_ids
        active = rod["id"] == current_rod_id
        status = "✅ Equipped" if active else ("📦 Owned" if owned else f"{fmt_stones(rod['price'])}")
        embed.add_field(
            name=f"{'⭐ ' if active else ''}{rod['name']} (Tier {rod['tier']})",
            value=(
                f"{rod['description']}\n"
                f"**Cooldown:** {rod['base_cooldown']:.0f}s base  "
                f"**XP:** ×{rod['xp_bonus']:.2f}  "
                f"**Luck:** {rod['pouch_luck']}\n"
                f"*{status}*"
                + (f"\n🔒 Requires Realm {rod['unlock_realm']}" if rod["unlock_realm"] > 0 else "")
            ),
            inline=False,
        )
    embed.set_footer(text="Buy with /buy rod <name>  •  Equip with /equip rod <name>")
    return embed


def _bait_shop_embed(stock: dict[str, int], licenses: list[str], max_bait_tier: int) -> discord.Embed:
    embed = discord.Embed(title="🪱 Bait — Spirit Stone Market", color=0x7BC8A4)
    for bait in BAITS:
        has_lic    = bait["license_cost"] == 0 or bait["id"] in licenses
        max_carry  = get_max_stack(bait["id"], max_bait_tier)
        qty        = stock.get(bait["id"], 0)
        lic_str    = "" if has_lic else f"\n🔒 License: {fmt_stones(bait['license_cost'])}"
        embed.add_field(
            name=f"{bait['name']} (Tier {bait['tier']})",
            value=(
                f"{bait['description']}\n"
                f"**Price:** {fmt_stones(bait['price'])}/unit  "
                f"**You have:** {qty}/{max_carry}\n"
                f"**Rare bonus:** +{bait['rare_bonus']*100:.0f}%"
                f"{lic_str}"
            ),
            inline=False,
        )
    embed.set_footer(text="Buy with /buy bait <name> <quantity>")
    return embed


def _lure_shop_embed(owned_lure_ids: list[str], current_lure_id: str) -> discord.Embed:
    embed = discord.Embed(title="🪝 Lures — Spirit Stone Market", color=0xF7DC6F)
    for lure in LURES:
        owned  = lure["id"] in owned_lure_ids
        active = lure["id"] == current_lure_id
        status = "✅ Equipped" if active else ("📦 Owned" if owned else fmt_stones(lure["price"]))
        embed.add_field(
            name=f"{'⭐ ' if active else ''}{lure['name']} (Tier {lure['tier']})",
            value=(
                f"{lure['description']}\n"
                f"**Rare:** +{lure['rare_bonus']*100:.0f}%  "
                f"**Bite:** +{lure['bite_bonus']*100:.0f}%  "
                f"**Size:** {lure['size_bias'] or 'neutral'}\n"
                f"*{status}*"
                + (f"\n🔒 Requires Realm {lure['unlock_realm']}" if lure["unlock_realm"] > 0 else "")
            ),
            inline=False,
        )
    embed.set_footer(text="Buy with /buy lure <name>  •  Equip with /equip lure <name>")
    return embed


def _pill_shop_embed(user_realm: int, pill_inv: dict[int, int],
                     tracker: dict[int, dict]) -> discord.Embed:
    embed = discord.Embed(title="💊 Breakthrough Pills — Spirit Stone Market", color=0xA569BD)
    for realm in range(1, 10):
        pill_name = PILL_NAMES[realm]
        base_cost = PILL_BASE_PRICES[realm]
        t         = tracker.get(realm, {})
        failures  = t.get("failure_count", 0)
        cur_cost  = t.get("current_pill_cost", base_cost)
        qty_owned = pill_inv.get(realm, 0)
        can_use   = user_realm == realm - 1   # pill for next realm
        embed.add_field(
            name=pill_name,
            value=(
                f"**Cost:** {fmt_stones(cur_cost)}"
                + (f"  *(×{2**failures} base after {failures} failure(s))*" if failures > 0 else "")
                + f"\n**You own:** {qty_owned}"
                + ("\n✅ *Current realm — buy this one*" if can_use else "")
            ),
            inline=False,
        )
    embed.set_footer(text="Buy with /buy pill <realm_number>")
    return embed


def _upgrade_embed(rod_id: str, upgrades: dict) -> discord.Embed:
    rod   = get_rod(rod_id)
    embed = discord.Embed(
        title=f"🔧 Rod Upgrades — {rod['name']}",
        color=0xE67E22,
    )
    tiers_map = {
        "reel_speed": ("reel_speed_tier", "Reel Speed", REEL_SPEED_REDUCTION, "sec reduction"),
        "xp_bonus":   ("xp_bonus_tier",   "XP Bonus",   XP_BONUS_DELTA,       "+multiplier"),
        "rod_luck":   ("rod_luck_tier",    "Rod Luck",   ROD_LUCK_BONUS,       "+luck"),
        "max_bait":   ("max_bait_tier",    "Bait Cap",   MAX_BAIT_BONUS,       "+slots"),
    }
    for key, (db_key, label, scale, unit) in tiers_map.items():
        cur_tier  = upgrades.get(db_key, 0)
        max_tier  = len(UPGRADE_COSTS[key]) - 1
        cur_val   = scale[min(cur_tier, len(scale)-1)]
        next_tier = cur_tier + 1
        if next_tier <= max_tier:
            next_cost = UPGRADE_COSTS[key][next_tier]
            next_val  = scale[min(next_tier, len(scale)-1)]
            cost_str  = f"Next: {fmt_stones(next_cost)} (+{next_val-cur_val:.2f} {unit})"
        else:
            cost_str  = "**MAX**"
        embed.add_field(
            name=f"{label}  [{cur_tier}/{max_tier}]",
            value=f"Current: `{cur_val} {unit}`\n{cost_str}",
            inline=True,
        )
    embed.set_footer(text="Upgrade with /upgrade <stat>")
    return embed


# ──────────────────────────────────────────────────────────────────────────────
# SHOP / SELL COG
# ──────────────────────────────────────────────────────────────────────────────

class ShopCog(commands.Cog, name="Shop"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── /shop ─────────────────────────────────────────────────────────────────

    @app_commands.command(name="shop", description="Browse the Spirit Stone Market.")
    @app_commands.describe(category="Which section to view")
    @app_commands.choices(category=[
        app_commands.Choice(name="Rods",    value="rods"),
        app_commands.Choice(name="Bait",    value="bait"),
        app_commands.Choice(name="Lures",   value="lures"),
        app_commands.Choice(name="Pills",   value="pills"),
        app_commands.Choice(name="Upgrades",value="upgrades"),
    ])
    async def shop(self, interaction: discord.Interaction,
                   category: str = "rods") -> None:
        if not await self._check_shop(interaction):
            return
        user = interaction.user
        row  = await db.get_or_create_user(user.id, str(user))

        if category == "rods":
            owned  = await db.get_owned_rod_ids(user.id)
            embed  = _rod_shop_embed(owned, row["rod_id"])
        elif category == "bait":
            stock  = await db.get_bait_stock(user.id)
            lics   = await db.get_bait_licenses(user.id)
            upgr   = await db.get_rod_upgrades(user.id) or {}
            embed  = _bait_shop_embed(stock, lics, upgr.get("max_bait_tier", 0))
        elif category == "lures":
            owned  = await db.get_owned_lure_ids(user.id)
            embed  = _lure_shop_embed(owned, row["lure_id"])
        elif category == "pills":
            pill_inv = await db.get_pill_inventory(user.id)
            tracker  = await db.get_cultivation_tracker(user.id)
            embed    = _pill_shop_embed(row["realm"], pill_inv, tracker)
        else:  # upgrades
            upgr  = await db.get_rod_upgrades(user.id) or {}
            embed = _upgrade_embed(row["rod_id"], upgr)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── /buy ──────────────────────────────────────────────────────────────────

    buy_group = app_commands.Group(name="buy", description="Purchase items from the market.")

    @buy_group.command(name="rod", description="Purchase a rod.")
    @app_commands.describe(rod_name="Name of the rod (e.g. 'Jade Serpent Rod')")
    async def buy_rod(self, interaction: discord.Interaction, rod_name: str) -> None:
        if not await self._check_shop(interaction):
            return
        rod = next((r for r in RODS if r["name"].lower() == rod_name.lower()), None)
        if not rod:
            await interaction.response.send_message(embed=error_embed(f"No rod named **{rod_name}** exists."), ephemeral=True)
            return
        user_row = await db.get_or_create_user(interaction.user.id, str(interaction.user))
        if user_row["realm"] < rod["unlock_realm"]:
            await interaction.response.send_message(
                embed=error_embed(f"You must be at least Realm {rod['unlock_realm']} to purchase this rod."),
                ephemeral=True,
            )
            return
        owned = await db.get_owned_rod_ids(interaction.user.id)
        if rod["id"] in owned:
            await interaction.response.send_message(embed=error_embed("You already own this rod."), ephemeral=True)
            return
        if rod["price"] == 0:
            await interaction.response.send_message(embed=error_embed("This rod cannot be purchased."), ephemeral=True)
            return
        ok = await db.spend_spirit_stones(interaction.user.id, rod["price"])
        if not ok:
            await interaction.response.send_message(embed=error_embed(f"Insufficient Spirit Stones. You need {fmt_stones(rod['price'])}."), ephemeral=True)
            return
        await db.add_owned_rod(interaction.user.id, rod["id"])
        await interaction.response.send_message(
            embed=success_embed(f"You purchased **{rod['name']}**!\nEquip it with `/equip rod {rod['name']}`."),
            ephemeral=True,
        )

    @buy_group.command(name="bait", description="Purchase bait.")
    @app_commands.describe(bait_name="Name of the bait", quantity="How many to buy (default 10)")
    async def buy_bait(self, interaction: discord.Interaction, bait_name: str, quantity: int = 10) -> None:
        if not await self._check_shop(interaction):
            return
        bait = next((b for b in BAITS if b["name"].lower() == bait_name.lower()), None)
        if not bait:
            await interaction.response.send_message(embed=error_embed(f"No bait named **{bait_name}** exists."), ephemeral=True)
            return
        if quantity < 1:
            quantity = 1

        user_id  = interaction.user.id
        user_row = await db.get_or_create_user(user_id, str(interaction.user))
        upgr     = await db.get_rod_upgrades(user_id) or {}
        licenses = await db.get_bait_licenses(user_id)

        # License check
        if bait["license_cost"] > 0 and bait["id"] not in licenses:
            # Offer to buy license
            view = _LicensePurchaseView(bait, user_id, self.bot)
            await interaction.response.send_message(
                embed=error_embed(
                    f"You need a **{bait['name']} License** to purchase this bait.\n"
                    f"License cost: {fmt_stones(bait['license_cost'])}"
                ),
                view=view,
                ephemeral=True,
            )
            return

        # Carry limit
        max_carry = get_max_stack(bait["id"], upgr.get("max_bait_tier", 0))
        stock     = await db.get_bait_stock(user_id)
        current   = stock.get(bait["id"], 0)
        can_buy   = max(0, max_carry - current)
        quantity  = min(quantity, can_buy)

        if quantity == 0:
            await interaction.response.send_message(
                embed=error_embed(f"You're at your carry limit ({max_carry}) for **{bait['name']}**."),
                ephemeral=True,
            )
            return

        total_cost = bait["price"] * quantity
        ok = await db.spend_spirit_stones(user_id, total_cost)
        if not ok:
            await interaction.response.send_message(
                embed=error_embed(f"Insufficient Spirit Stones. You need {fmt_stones(total_cost)}."),
                ephemeral=True,
            )
            return

        await db.add_bait_stock(user_id, bait["id"], quantity)
        new_qty = current + quantity
        await interaction.response.send_message(
            embed=success_embed(
                f"Purchased **{quantity}× {bait['name']}** for {fmt_stones(total_cost)}.\n"
                f"Stock: {new_qty}/{max_carry}"
            ),
            ephemeral=True,
        )

    @buy_group.command(name="lure", description="Purchase a lure.")
    @app_commands.describe(lure_name="Name of the lure")
    async def buy_lure(self, interaction: discord.Interaction, lure_name: str) -> None:
        if not await self._check_shop(interaction):
            return
        lure = next((l for l in LURES if l["name"].lower() == lure_name.lower()), None)
        if not lure:
            await interaction.response.send_message(embed=error_embed(f"No lure named **{lure_name}** exists."), ephemeral=True)
            return
        user_id  = interaction.user.id
        user_row = await db.get_or_create_user(user_id, str(interaction.user))
        if user_row["realm"] < lure["unlock_realm"]:
            await interaction.response.send_message(
                embed=error_embed(f"Realm {lure['unlock_realm']} required."), ephemeral=True)
            return
        owned = await db.get_owned_lure_ids(user_id)
        if lure["id"] in owned:
            await interaction.response.send_message(embed=error_embed("You already own this lure."), ephemeral=True)
            return
        ok = await db.spend_spirit_stones(user_id, lure["price"])
        if not ok:
            await interaction.response.send_message(embed=error_embed(f"Need {fmt_stones(lure['price'])}."), ephemeral=True)
            return
        await db.add_owned_lure(user_id, lure["id"])
        await interaction.response.send_message(
            embed=success_embed(f"Purchased **{lure['name']}**! Equip with `/equip lure {lure['name']}`."),
            ephemeral=True,
        )

    @buy_group.command(name="pill", description="Purchase a Breakthrough Pill.")
    @app_commands.describe(realm="The realm number this pill is for (1-9)")
    async def buy_pill(self, interaction: discord.Interaction, realm: int) -> None:
        if not await self._check_shop(interaction):
            return
        if realm < 1 or realm > 9:
            await interaction.response.send_message(embed=error_embed("Realm must be 1-9."), ephemeral=True)
            return
        user_id  = interaction.user.id
        user_row = await db.get_or_create_user(user_id, str(interaction.user))
        tracker  = await db.get_cultivation_tracker(user_id)
        t        = tracker.get(realm, {})
        cost     = t.get("current_pill_cost", PILL_BASE_PRICES[realm])

        ok = await db.spend_spirit_stones(user_id, cost)
        if not ok:
            await interaction.response.send_message(embed=error_embed(f"Need {fmt_stones(cost)}."), ephemeral=True)
            return
        await db.add_pill(user_id, realm, 1)
        await interaction.response.send_message(
            embed=success_embed(f"Purchased **{PILL_NAMES[realm]}** for {fmt_stones(cost)}."),
            ephemeral=True,
        )

    # ── /equip ────────────────────────────────────────────────────────────────

    equip_group = app_commands.Group(name="equip", description="Equip owned gear.")

    @equip_group.command(name="rod", description="Equip a rod you own.")
    @app_commands.describe(rod_name="Name of the rod")
    async def equip_rod(self, interaction: discord.Interaction, rod_name: str) -> None:
        rod = next((r for r in RODS if r["name"].lower() == rod_name.lower()), None)
        if not rod:
            await interaction.response.send_message(embed=error_embed(f"Unknown rod: {rod_name}"), ephemeral=True)
            return
        owned = await db.get_owned_rod_ids(interaction.user.id)
        if rod["id"] not in owned:
            await interaction.response.send_message(embed=error_embed("You don't own this rod."), ephemeral=True)
            return
        await db.set_user_rod(interaction.user.id, rod["id"])
        await interaction.response.send_message(embed=success_embed(f"Equipped **{rod['name']}**."), ephemeral=True)

    @equip_group.command(name="bait", description="Set your active bait.")
    @app_commands.describe(bait_name="Name of the bait")
    async def equip_bait(self, interaction: discord.Interaction, bait_name: str) -> None:
        bait = next((b for b in BAITS if b["name"].lower() == bait_name.lower()), None)
        if not bait:
            await interaction.response.send_message(embed=error_embed(f"Unknown bait: {bait_name}"), ephemeral=True)
            return
        stock = await db.get_bait_stock(interaction.user.id)
        if stock.get(bait["id"], 0) == 0:
            await interaction.response.send_message(embed=error_embed("You don't have any of this bait."), ephemeral=True)
            return
        await db.set_user_bait(interaction.user.id, bait["id"])
        await interaction.response.send_message(embed=success_embed(f"Active bait set to **{bait['name']}**."), ephemeral=True)

    @equip_group.command(name="lure", description="Set your active lure.")
    @app_commands.describe(lure_name="Name of the lure")
    async def equip_lure(self, interaction: discord.Interaction, lure_name: str) -> None:
        lure = next((l for l in LURES if l["name"].lower() == lure_name.lower()), None)
        if not lure:
            await interaction.response.send_message(embed=error_embed(f"Unknown lure: {lure_name}"), ephemeral=True)
            return
        owned = await db.get_owned_lure_ids(interaction.user.id)
        if lure["id"] not in owned:
            await interaction.response.send_message(embed=error_embed("You don't own this lure."), ephemeral=True)
            return
        await db.set_user_lure(interaction.user.id, lure["id"])
        await interaction.response.send_message(embed=success_embed(f"Active lure set to **{lure['name']}**."), ephemeral=True)

    # ── /upgrade ──────────────────────────────────────────────────────────────

    @app_commands.command(name="upgrade", description="Upgrade your equipped rod's stats.")
    @app_commands.describe(stat="Stat to upgrade")
    @app_commands.choices(stat=[
        app_commands.Choice(name="Reel Speed",  value="reel_speed"),
        app_commands.Choice(name="XP Bonus",    value="xp_bonus"),
        app_commands.Choice(name="Rod Luck",    value="rod_luck"),
        app_commands.Choice(name="Bait Capacity",value="max_bait"),
    ])
    async def upgrade(self, interaction: discord.Interaction, stat: str) -> None:
        if not await self._check_shop(interaction):
            return
        user_id  = interaction.user.id
        user_row = await db.get_or_create_user(user_id, str(interaction.user))
        upgr     = await db.get_rod_upgrades(user_id) or {}
        db_key   = f"{stat}_tier"
        cur_tier = upgr.get(db_key, 0)
        max_tier = len(UPGRADE_COSTS[stat]) - 1

        if cur_tier >= max_tier:
            await interaction.response.send_message(
                embed=error_embed(f"**{UPGRADE_LABELS[stat]}** is already at MAX tier!"),
                ephemeral=True,
            )
            return

        next_tier = cur_tier + 1
        cost      = UPGRADE_COSTS[stat][next_tier]
        ok        = await db.spend_spirit_stones(user_id, cost)
        if not ok:
            await interaction.response.send_message(
                embed=error_embed(f"Need {fmt_stones(cost)} to upgrade **{UPGRADE_LABELS[stat]}**."),
                ephemeral=True,
            )
            return

        await db.set_rod_upgrade_tier(user_id, db_key, next_tier)
        await interaction.response.send_message(
            embed=success_embed(
                f"**{UPGRADE_LABELS[stat]}** upgraded to Tier {next_tier}/{max_tier}!\n"
                f"Cost: {fmt_stones(cost)}"
            ),
            ephemeral=True,
        )

    # ── /sell ─────────────────────────────────────────────────────────────────

    sell_group = app_commands.Group(name="sell", description="Sell your caught fish.")

    @sell_group.command(name="all", description="Sell all fish in your inventory.")
    async def sell_all(self, interaction: discord.Interaction) -> None:
        user_id = interaction.user.id
        count   = await db.fish_inventory_count(user_id)
        if count == 0:
            await interaction.response.send_message(
                embed=error_embed("Your fish inventory is empty."),
                ephemeral=True,
            )
            return

        # Confirmation
        view = _SellConfirmView(user_id, "all", None, count)
        await interaction.response.send_message(
            embed=discord.Embed(
                title="💰 Sell All Fish?",
                description=(
                    f"You are about to sell all **{count} fish** in your inventory.\n\n"
                    f"This cannot be undone. Auto-cancels in 30 seconds."
                ),
                color=0xF39C12,
            ),
            view=view,
            ephemeral=True,
        )

    @sell_group.command(name="fish", description="Sell a specific fish by inventory ID.")
    @app_commands.describe(fish_id="The inventory ID shown in /inventory")
    async def sell_fish(self, interaction: discord.Interaction, fish_id: int) -> None:
        user_id = interaction.user.id
        fish_row = await db.get_fish_by_id(fish_id, user_id)
        if not fish_row:
            await interaction.response.send_message(
                embed=error_embed(f"No fish with ID #{fish_id} found in your inventory."),
                ephemeral=True,
            )
            return
        view = _SellConfirmView(user_id, "fish", fish_id, 1, fish_row["value"])
        embed = discord.Embed(
            title="💰 Sell This Fish?",
            description=(
                f"**#{fish_id} — {fish_row['name']}**\n"
                f"Quality: {fmt_quality(fish_row['quality'])}  •  Value: {fmt_stones(fish_row['value'])}\n\n"
                f"Auto-cancels in 30 seconds."
            ),
            color=0xF39C12,
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @sell_group.command(name="species", description="Sell all fish of a specific species.")
    @app_commands.describe(species_name="Species name (e.g. Jade River Carp)")
    async def sell_species(self, interaction: discord.Interaction, species_name: str) -> None:
        user_id  = interaction.user.id
        from bot.data.fish_data import FISH
        fish_def = next((f for f in FISH if f["name"].lower() == species_name.lower()), None)
        if not fish_def:
            await interaction.response.send_message(embed=error_embed(f"Unknown species: {species_name}"), ephemeral=True)
            return
        count = await db.fish_count_by_species(user_id, fish_def["id"])
        if count == 0:
            await interaction.response.send_message(embed=error_embed(f"You have no **{fish_def['name']}** to sell."), ephemeral=True)
            return
        view = _SellConfirmView(user_id, "species", fish_def["id"], count)
        embed = discord.Embed(
            title=f"💰 Sell All {fish_def['name']}?",
            description=f"You have **{count}** of this species in your inventory.\n\nAuto-cancels in 30 seconds.",
            color=0xF39C12,
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    # ── Internal check ────────────────────────────────────────────────────────

    async def _check_shop(self, interaction: discord.Interaction) -> bool:
        from bot.utils.checks import channel_is_shop
        if not await channel_is_shop(interaction.channel_id):
            await interaction.response.send_message(
                "⛔ Shop commands can only be used in the **Spirit Stone Market** channel.",
                ephemeral=True,
            )
            return False
        return True


# ──────────────────────────────────────────────────────────────────────────────
# SELL CONFIRMATION VIEW
# ──────────────────────────────────────────────────────────────────────────────

class _SellConfirmView(discord.ui.View):
    def __init__(self, user_id: int, mode: str, target, count: int, known_value: int = 0):
        super().__init__(timeout=30.0)
        self.user_id     = user_id
        self.mode        = mode       # "all" | "fish" | "species"
        self.target      = target     # fish_id (int) or species_id (str) or None
        self.count       = count
        self.known_value = known_value
        self.done        = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user_id

    @discord.ui.button(label="✅ Confirm Sell", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, _: discord.ui.Button):
        self.done = True
        self.stop()
        if self.mode == "all":
            total, count = await db.sell_all_fish(self.user_id)
        elif self.mode == "fish":
            ok    = await db.sell_fish_by_id(self.user_id, self.target)
            total = self.known_value if ok else 0
            count = 1 if ok else 0
        else:  # species
            total, count = await db.sell_fish_by_species(self.user_id, self.target)

        if count == 0:
            await interaction.response.edit_message(
                embed=error_embed("Nothing was sold — inventory may have changed."), view=None)
        else:
            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="💰 Sold!",
                    description=f"Sold **{count}** fish for **{fmt_stones(total)}**!",
                    color=0x2ECC71,
                ),
                view=None,
            )
            # Trigger channel unlock checks (Celestial Peak Reservoir condition)
            if interaction.guild and isinstance(interaction.user, discord.Member):
                import asyncio
                from bot.utils.unlock_checker import check_unlocks
                asyncio.create_task(check_unlocks(
                    interaction.client, interaction.user, interaction.guild
                ))

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, _: discord.ui.Button):
        self.done = True
        self.stop()
        await interaction.response.edit_message(
            embed=discord.Embed(title="❌ Sale Cancelled", color=0x7F8C8D), view=None)

    async def on_timeout(self):
        # Auto-cancel
        self.stop()


# ──────────────────────────────────────────────────────────────────────────────
# LICENSE PURCHASE VIEW
# ──────────────────────────────────────────────────────────────────────────────

class _LicensePurchaseView(discord.ui.View):
    def __init__(self, bait: dict, user_id: int, bot: commands.Bot):
        super().__init__(timeout=30.0)
        self.bait    = bait
        self.user_id = user_id
        self.bot     = bot

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user_id

    @discord.ui.button(label="✅ Buy License", style=discord.ButtonStyle.success)
    async def buy_license(self, interaction: discord.Interaction, _: discord.ui.Button):
        self.stop()
        ok = await db.spend_spirit_stones(self.user_id, self.bait["license_cost"])
        if not ok:
            await interaction.response.edit_message(
                embed=error_embed(f"Need {fmt_stones(self.bait['license_cost'])} for the license."),
                view=None,
            )
            return
        await db.add_bait_license(self.user_id, self.bait["id"])
        await interaction.response.edit_message(
            embed=success_embed(
                f"**{self.bait['name']} License** purchased!\n"
                f"You can now buy this bait with `/buy bait {self.bait['name']}`."
            ),
            view=None,
        )

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, _: discord.ui.Button):
        self.stop()
        await interaction.response.edit_message(content="Cancelled.", embed=None, view=None)


# ──────────────────────────────────────────────────────────────────────────────
# COG SETUP
# ──────────────────────────────────────────────────────────────────────────────

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ShopCog(bot))
