import asyncio
import datetime
import os
from pathlib import Path
from typing import Literal

import hikari
import lightbulb
import miru
from lightbulb import owner_only
from lightbulb.utils import search

from models import Bot, Emojis
from models.colour import Colour
from models.views import (
    TicketPanelView,
    TicketCloseView,
    TicketCloseConfirmationView,
    CloseRequestConfirmationView,
)

plugin = lightbulb.Plugin(Path(__file__).stem, include_datastore=True)
plugin.add_checks(owner_only)

plugin.d.TICKETS_CATEGORY_ID = int(os.environ["TICKET_CATEGORY_ID"])
plugin.d.LOADING_EMBED = hikari.Embed(
    description="**Creating Ticket Panel ...**", colour=Colour.INVISIBLE
)
plugin.d.SUCCESS_EMBED = hikari.Embed(
    description="**Successfully created the Ticket Panel in {channel}.**",
    colour=Colour.INVISIBLE,
)
plugin.d.SUPPORT_ROLE_ID = int(os.environ["SUPPORT_ROLE_ID"])

TicketCategory = Literal[
    "general_question",
    "configuration_question",
    "support_apply",
    "refund",
    "custom_bot",
]


@plugin.listener(miru.ComponentInteractionCreateEvent)
async def component_interaction_event_handler(
    event: miru.ComponentInteractionCreateEvent,
) -> None:
    if not event.custom_id.startswith("TICKET:CLOSE-REQUEST:CONFIRM:"):
        return

    bot: Bot = plugin.bot  # type: ignore
    channel = bot.cache.get_guild_channel(event.channel_id)
    if not channel:
        return

    ticket_owner_id = int(channel.name.split("-")[-1])
    if event.user.id != ticket_owner_id:
        await event.interaction.create_initial_response(
            response_type=hikari.ResponseType.MESSAGE_CREATE,
            content=f"**Only** the Owner of this Ticket can interact with the close-request. (<@{ticket_owner_id}>)",
            flags=hikari.MessageFlag.EPHEMERAL,
        )
        return

    await event.app.rest.delete_channel(event.channel_id)


@plugin.listener(miru.ComponentInteractionCreateEvent)
async def component_interaction_event_handler(
    event: miru.ComponentInteractionCreateEvent,
) -> None:
    if not event.custom_id.startswith("TICKET:CLOSE-REQUEST:CANCEL:"):
        return

    bot: Bot = plugin.bot  # type: ignore
    channel = bot.cache.get_guild_channel(event.channel_id)
    if not channel:
        return

    ticket_owner_id = int(channel.name.split("-")[-1])
    if event.user.id != ticket_owner_id:
        await event.interaction.create_initial_response(
            response_type=hikari.ResponseType.MESSAGE_CREATE,
            content=f"**Only** the Owner of this Ticket can interact with the close-request. (<@{ticket_owner_id}>)",
            flags=hikari.MessageFlag.EPHEMERAL,
        )
        return

    embed = event.interaction.message.embeds[0]
    embed.description = "**The close-request was declined.**"
    embed.colour = Colour.NEON_RED

    await bot.rest.edit_message(
        channel.id, event.interaction.message, embed=embed, components=[]
    )

    await event.interaction.create_initial_response(
        response_type=hikari.ResponseType.MESSAGE_CREATE,
        content=f"**Declined the close-request.**",
        flags=hikari.MessageFlag.EPHEMERAL,
    )


@plugin.listener(miru.ComponentInteractionCreateEvent)
async def component_interaction_event_handler(
    event: miru.ComponentInteractionCreateEvent,
) -> None:
    if event.custom_id != "TICKET:CANCEL:CLOSE":
        return

    await event.app.rest.delete_message(event.channel_id, event.message)


@plugin.listener(miru.ComponentInteractionCreateEvent)
async def component_interaction_event_handler(
    event: miru.ComponentInteractionCreateEvent,
) -> None:
    if event.custom_id != "TICKET:CONFIRM:CLOSE":
        return

    await event.app.rest.delete_channel(event.channel_id)


@plugin.listener(miru.ComponentInteractionCreateEvent)
async def component_interaction_event_handler(
    event: miru.ComponentInteractionCreateEvent,
) -> None:
    if not event.custom_id.startswith("TICKET:CLOSE:"):
        return

    embed = (
        hikari.Embed(
            description=f"**Please confirm that you want to close this Ticket.**",
            colour=Colour.BLURPLE,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        .set_footer(
            text=plugin.bot.footer_text, icon=plugin.bot.display_avatar_url  # type: ignore
        )
        .set_author(
            name="DayZ++",
            icon=plugin.bot.display_avatar_url,  # type: ignore
            url="https://discord.com/users/867376409965363200",
        )
    )

    await event.interaction.create_initial_response(
        response_type=hikari.ResponseType.MESSAGE_CREATE,
        embed=embed,
        components=TicketCloseConfirmationView().build(),
    )


@plugin.listener(miru.ComponentInteractionCreateEvent)
async def component_interaction_event_handler(
    event: miru.ComponentInteractionCreateEvent,
) -> None:
    bot: Bot = plugin.bot  # type: ignore
    if event.custom_id != "ticket_panel":
        return

    await event.message.edit(embed=event.message.embeds[0])

    user = event.user
    if (
        channel := search.get(
            bot.cache.get_guild_channels_view_for_guild(
                event.guild_id
            ).values(),
            name=f"ticket-{user.username}",
        )
    ) is not None:
        embed = (
            hikari.Embed(
                description=f"**You already have an open Ticket. ({channel.mention})**",
                colour=Colour.BLURPLE,
                timestamp=datetime.datetime.now(datetime.timezone.utc),
            )
            .set_footer(
                text=plugin.bot.footer_text, icon=plugin.bot.display_avatar_url  # type: ignore
            )
            .set_author(
                name="DayZ++",
                icon=plugin.bot.display_avatar_url,  # type: ignore
                url="https://discord.com/users/867376409965363200",
            )
        )
        await event.interaction.create_initial_response(
            response_type=hikari.ResponseType.MESSAGE_CREATE,
            embed=embed,
            flags=hikari.MessageFlag.EPHEMERAL,
        )
        return

    ticket_category: TicketCategory = event.interaction.values[0]  # type: ignore
    permission_overwrites = (
        hikari.PermissionOverwrite(
            id=event.guild_id,
            type=hikari.PermissionOverwriteType.ROLE,
            deny=hikari.Permissions.VIEW_CHANNEL,
        ),
        hikari.PermissionOverwrite(
            id=user.id,
            type=hikari.PermissionOverwriteType.MEMBER,
            allow=hikari.Permissions.SEND_MESSAGES
            | hikari.Permissions.READ_MESSAGE_HISTORY
            | hikari.Permissions.ATTACH_FILES
            | hikari.Permissions.EMBED_LINKS
            | hikari.Permissions.VIEW_CHANNEL,
        ),
        hikari.PermissionOverwrite(
            id=plugin.d.SUPPORT_ROLE_ID,
            type=hikari.PermissionOverwriteType.ROLE,
            allow=hikari.Permissions.all_permissions(),
        ),
    )

    user_is_verified_admin: bool = 904037799316058112 in event.member.role_ids
    shop_feature_owner: bool = 945356446076395520 in event.member.role_ids
    premium_feature_owner: bool = 1003908285465899059 in event.member.role_ids

    if ticket_category == "general_question":
        ticket_channel = await bot.rest.create_guild_text_channel(
            event.guild_id,
            name=f"ticket-{user.username}-{user.id}",
            category=plugin.d.TICKETS_CATEGORY_ID,
            permission_overwrites=permission_overwrites,
        )
        ticket_channel_embed = (
            hikari.Embed(
                description=f"""
                            > **User Information**
                            > • Verified Owner | Admin: {Emojis.CHECK if user_is_verified_admin else Emojis.CROSS}
                            > • Premium Feature Owner: {Emojis.CHECK if premium_feature_owner else Emojis.CROSS}
                            > • Shop Feature Owner: {Emojis.CHECK if shop_feature_owner else Emojis.CROSS}
                            > **Ticket Information**
                            > • Category: General Question
                            """,
                colour=Colour.BLURPLE,
                timestamp=datetime.datetime.now(datetime.timezone.utc),
            )
            .set_footer(
                text=plugin.bot.footer_text, icon=plugin.bot.display_avatar_url  # type: ignore
            )
            .set_author(
                name="DayZ++",
                icon=plugin.bot.display_avatar_url,  # type: ignore
                url="https://discord.com/users/867376409965363200",
            )
        )
        await bot.rest.create_message(
            ticket_channel.id,
            "<@609077285584240715>",
            embed=ticket_channel_embed,
            components=TicketCloseView(channel_id=ticket_channel.id).build(),
        )

        embed = (
            hikari.Embed(
                description=f"**Successfully created your Ticket in {ticket_channel.mention}.**",
                colour=Colour.BLURPLE,
                timestamp=datetime.datetime.now(datetime.timezone.utc),
            )
            .set_footer(
                text=plugin.bot.footer_text, icon=plugin.bot.display_avatar_url  # type: ignore
            )
            .set_author(
                name="DayZ++",
                icon=plugin.bot.display_avatar_url,  # type: ignore
                url="https://discord.com/users/867376409965363200",
            )
        )
        await event.interaction.create_initial_response(
            response_type=hikari.ResponseType.MESSAGE_CREATE,
            embed=embed,
            flags=hikari.MessageFlag.EPHEMERAL,
        )

    elif ticket_category == "configuration_question":
        ticket_channel = await bot.rest.create_guild_text_channel(
            event.guild_id,
            name=f"ticket-{user.username}-{user.id}",
            category=plugin.d.TICKETS_CATEGORY_ID,
            permission_overwrites=permission_overwrites,
        )
        ticket_channel_embed = (
            hikari.Embed(
                description=f"""
                            > **User Information**
                            > • Verified Owner | Admin: {Emojis.CHECK if user_is_verified_admin else Emojis.CROSS}
                            > • Premium Feature Owner: {Emojis.CHECK if premium_feature_owner else Emojis.CROSS}
                            > • Shop Feature Owner: {Emojis.CHECK if shop_feature_owner else Emojis.CROSS}
                            > **Ticket Information**
                            > • Category: Configuration Question
                            """,
                colour=Colour.BLURPLE,
                timestamp=datetime.datetime.now(datetime.timezone.utc),
            )
            .set_footer(
                text=plugin.bot.footer_text, icon=plugin.bot.display_avatar_url  # type: ignore
            )
            .set_author(
                name="DayZ++",
                icon=plugin.bot.display_avatar_url,  # type: ignore
                url="https://discord.com/users/867376409965363200",
            )
        )
        await bot.rest.create_message(
            ticket_channel.id,
            "<@609077285584240715>",
            embed=ticket_channel_embed,
            components=TicketCloseView(channel_id=ticket_channel.id).build(),
        )

        embed = (
            hikari.Embed(
                description=f"**Successfully created your Ticket in {ticket_channel.mention}.**",
                colour=Colour.BLURPLE,
                timestamp=datetime.datetime.now(datetime.timezone.utc),
            )
            .set_footer(
                text=plugin.bot.footer_text, icon=plugin.bot.display_avatar_url  # type: ignore
            )
            .set_author(
                name="DayZ++",
                icon=plugin.bot.display_avatar_url,  # type: ignore
                url="https://discord.com/users/867376409965363200",
            )
        )
        await event.interaction.create_initial_response(
            response_type=hikari.ResponseType.MESSAGE_CREATE,
            embed=embed,
            flags=hikari.MessageFlag.EPHEMERAL,
        )

    elif ticket_category == "support_apply":
        ticket_channel = await bot.rest.create_guild_text_channel(
            event.guild_id,
            name=f"ticket-{user.username}-{user.id}",
            category=plugin.d.TICKETS_CATEGORY_ID,
            permission_overwrites=permission_overwrites,
        )
        ticket_channel_embed = (
            hikari.Embed(
                description=f"""
                            > **User Information**
                            > • Verified Owner | Admin: {Emojis.CHECK if user_is_verified_admin else Emojis.CROSS}
                            > • Premium Feature Owner: {Emojis.CHECK if premium_feature_owner else Emojis.CROSS}
                            > • Shop Feature Owner: {Emojis.CHECK if shop_feature_owner else Emojis.CROSS}
                            > **Ticket Information**
                            > • Category: Support Application
                            """,
                colour=Colour.BLURPLE,
                timestamp=datetime.datetime.now(datetime.timezone.utc),
            )
            .set_footer(
                text=plugin.bot.footer_text, icon=plugin.bot.display_avatar_url  # type: ignore
            )
            .set_author(
                name="DayZ++",
                icon=plugin.bot.display_avatar_url,  # type: ignore
                url="https://discord.com/users/867376409965363200",
            )
        )
        await bot.rest.create_message(
            ticket_channel.id,
            "<@609077285584240715>",
            embed=ticket_channel_embed,
            components=TicketCloseView(channel_id=ticket_channel.id).build(),
        )

        embed = (
            hikari.Embed(
                description=f"**Successfully created your Ticket in {ticket_channel.mention}.**",
                colour=Colour.BLURPLE,
                timestamp=datetime.datetime.now(datetime.timezone.utc),
            )
            .set_footer(
                text=plugin.bot.footer_text, icon=plugin.bot.display_avatar_url  # type: ignore
            )
            .set_author(
                name="DayZ++",
                icon=plugin.bot.display_avatar_url,  # type: ignore
                url="https://discord.com/users/867376409965363200",
            )
        )
        await event.interaction.create_initial_response(
            response_type=hikari.ResponseType.MESSAGE_CREATE,
            embed=embed,
            flags=hikari.MessageFlag.EPHEMERAL,
        )

    elif ticket_category == "bug_report":
        ticket_channel = await bot.rest.create_guild_text_channel(
            event.guild_id,
            name=f"ticket-{user.username}-{user.id}",
            category=plugin.d.TICKETS_CATEGORY_ID,
            permission_overwrites=permission_overwrites,
        )
        ticket_channel_embed = (
            hikari.Embed(
                description=f"""
                            > **User Information**
                            > • Verified Owner | Admin: {Emojis.CHECK if user_is_verified_admin else Emojis.CROSS}
                            > • Premium Feature Owner: {Emojis.CHECK if premium_feature_owner else Emojis.CROSS}
                            > • Shop Feature Owner: {Emojis.CHECK if shop_feature_owner else Emojis.CROSS}
                            > **Ticket Information**
                            > • Category: Bug Report
                            """,
                colour=Colour.BLURPLE,
                timestamp=datetime.datetime.now(datetime.timezone.utc),
            )
            .set_footer(
                text=plugin.bot.footer_text, icon=plugin.bot.display_avatar_url  # type: ignore
            )
            .set_author(
                name="DayZ++",
                icon=plugin.bot.display_avatar_url,  # type: ignore
                url="https://discord.com/users/867376409965363200",
            )
        )
        await bot.rest.create_message(
            ticket_channel.id,
            "<@609077285584240715>",
            embed=ticket_channel_embed,
            components=TicketCloseView(channel_id=ticket_channel.id).build(),
            user_mentions=True,
        )

        embed = (
            hikari.Embed(
                description=f"**Successfully created your Ticket in {ticket_channel.mention}.**",
                colour=Colour.BLURPLE,
                timestamp=datetime.datetime.now(datetime.timezone.utc),
            )
            .set_footer(
                text=plugin.bot.footer_text, icon=plugin.bot.display_avatar_url  # type: ignore
            )
            .set_author(
                name="DayZ++",
                icon=plugin.bot.display_avatar_url,  # type: ignore
                url="https://discord.com/users/867376409965363200",
            )
        )
        await event.interaction.create_initial_response(
            response_type=hikari.ResponseType.MESSAGE_CREATE,
            embed=embed,
            flags=hikari.MessageFlag.EPHEMERAL,
        )

    elif ticket_category == "custom_bot":
        ticket_channel = await bot.rest.create_guild_text_channel(
            event.guild_id,
            name=f"ticket-{user.username}-{user.id}",
            category=plugin.d.TICKETS_CATEGORY_ID,
            permission_overwrites=permission_overwrites,
        )
        ticket_channel_embed = (
            hikari.Embed(
                description=f"""
                                    > **User Information**
                                    > • Verified Owner | Admin: {Emojis.CHECK if user_is_verified_admin else Emojis.CROSS}
                                    > • Premium Feature Owner: {Emojis.CHECK if premium_feature_owner else Emojis.CROSS}
                                    > • Shop Feature Owner: {Emojis.CHECK if shop_feature_owner else Emojis.CROSS}
                                    > **Ticket Information**
                                    > • Category: Custom Bot
                                    """,
                colour=Colour.BLURPLE,
                timestamp=datetime.datetime.now(datetime.timezone.utc),
            )
            .set_footer(
                text=plugin.bot.footer_text, icon=plugin.bot.display_avatar_url  # type: ignore
            )
            .set_author(
                name="DayZ++",
                icon=plugin.bot.display_avatar_url,  # type: ignore
                url="https://discord.com/users/867376409965363200",
            )
        )
        await bot.rest.create_message(
            ticket_channel.id,
            "<@609077285584240715>",
            embed=ticket_channel_embed,
            components=TicketCloseView(channel_id=ticket_channel.id).build(),
            user_mentions=True,
        )

        embed = (
            hikari.Embed(
                description=f"**Successfully created your Ticket in {ticket_channel.mention}.**",
                colour=Colour.BLURPLE,
                timestamp=datetime.datetime.now(datetime.timezone.utc),
            )
            .set_footer(
                text=plugin.bot.footer_text, icon=plugin.bot.display_avatar_url  # type: ignore
            )
            .set_author(
                name="DayZ++",
                icon=plugin.bot.display_avatar_url,  # type: ignore
                url="https://discord.com/users/867376409965363200",
            )
        )
        await event.interaction.create_initial_response(
            response_type=hikari.ResponseType.MESSAGE_CREATE,
            embed=embed,
            flags=hikari.MessageFlag.EPHEMERAL,
        )

    elif ticket_category == "refund":
        ticket_channel = await bot.rest.create_guild_text_channel(
            event.guild_id,
            name=f"ticket-{user.username}-{user.id}",
            category=plugin.d.TICKETS_CATEGORY_ID,
            permission_overwrites=permission_overwrites,
        )
        ticket_channel_embed = (
            hikari.Embed(
                description=f"""
                            > **User Information**
                            > • Verified Owner | Admin: {Emojis.CHECK if user_is_verified_admin else Emojis.CROSS}
                            > • Premium Feature Owner: {Emojis.CHECK if premium_feature_owner else Emojis.CROSS}
                            > • Shop Feature Owner: {Emojis.CHECK if shop_feature_owner else Emojis.CROSS}
                            > **Ticket Information**
                            > • Category: Refund
                            """,
                colour=Colour.BLURPLE,
                timestamp=datetime.datetime.now(datetime.timezone.utc),
            )
            .set_footer(
                text=plugin.bot.footer_text, icon=plugin.bot.display_avatar_url  # type: ignore
            )
            .set_author(
                name="DayZ++",
                icon=plugin.bot.display_avatar_url,  # type: ignore
                url="https://discord.com/users/867376409965363200",
            )
        )
        await bot.rest.create_message(
            ticket_channel.id,
            "<@609077285584240715>",
            embed=ticket_channel_embed,
            components=TicketCloseView(channel_id=ticket_channel.id).build(),
            user_mentions=True,
        )

        embed = (
            hikari.Embed(
                description=f"**Successfully created your Ticket in {ticket_channel.mention}.**",
                colour=Colour.BLURPLE,
                timestamp=datetime.datetime.now(datetime.timezone.utc),
            )
            .set_footer(
                text=plugin.bot.footer_text, icon=plugin.bot.display_avatar_url  # type: ignore
            )
            .set_author(
                name="DayZ++",
                icon=plugin.bot.display_avatar_url,  # type: ignore
                url="https://discord.com/users/867376409965363200",
            )
        )
        await event.interaction.create_initial_response(
            response_type=hikari.ResponseType.MESSAGE_CREATE,
            embed=embed,
            flags=hikari.MessageFlag.EPHEMERAL,
        )


@plugin.command
@lightbulb.app_command_permissions(
    hikari.Permissions.ADMINISTRATOR, dm_enabled=False
)
@lightbulb.option(
    name="channel",
    description="The Channel for the Ticket Panel.",
    type=hikari.TextableGuildChannel,
    channel_types=(hikari.ChannelType.GUILD_TEXT,),
)
@lightbulb.command(
    name="ticket-panel",
    description="Sends the Ticket Panel for the Support System.",
    auto_defer=True,
    pass_options=True,
)
@lightbulb.implements(lightbulb.SlashCommand)
async def ticket_panel_command(
    ctx: lightbulb.SlashContext, channel: hikari.InteractionChannel
) -> None:
    bot: Bot = plugin.bot  # type: ignore
    await ctx.respond(embed=plugin.d.LOADING_EMBED)

    panel_embed = (
        hikari.Embed(
            description="**Click on the button corresponding to the type of ticket you wish to open.**",
            colour=Colour.BLURPLE,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        .set_footer(
            text=plugin.bot.footer_text, icon=plugin.bot.display_avatar_url  # type: ignore
        )
        .set_author(
            name="DayZ++",
            icon=plugin.bot.display_avatar_url,  # type: ignore
            url="https://discord.com/users/867376409965363200",
        )
    )
    view = TicketPanelView()
    await bot.rest.create_message(
        channel.id, embed=panel_embed, components=view.build()
    )

    embed = plugin.d.SUCCESS_EMBED
    embed.description = embed.description.format(channel=f"<#{channel.id}>")
    await ctx.edit_last_response(embed=embed)


@plugin.command
@lightbulb.app_command_permissions(
    hikari.Permissions.MANAGE_ROLES, dm_enabled=False
)
@lightbulb.command(
    name="close-request",
    description="Requests the Ticket to be closed by the Person that opened it.",
    auto_defer=True,
)
@lightbulb.implements(lightbulb.SlashCommand)
async def close_request_command(ctx: lightbulb.SlashContext) -> None:
    bot: Bot = plugin.bot  # type: ignore
    channel = bot.cache.get_guild_channel(ctx.channel_id)

    if channel.parent_id != plugin.d.TICKETS_CATEGORY_ID:
        await ctx.respond(
            "**This is not a Ticket Channel.**",
            flags=hikari.MessageFlag.EPHEMERAL,
        )
        return

    ticket_owner_id = int(channel.name.split("-")[-1])
    if ticket_owner_id not in bot.cache.get_members_view_for_guild(
        int(os.environ["GUILD_ID"])
    ):
        await ctx.respond(
            "The Person that created this Ticket is not in the Server anymore. Closing it automatically in 3 seconds ...",
            flags=hikari.MessageFlag.EPHEMERAL,
        )
        await asyncio.sleep(3)
        await bot.rest.delete_channel(channel)

    embed = (
        hikari.Embed(
            description=f"**{ctx.user.mention} requests to close this Ticket.**",
            colour=Colour.BLURPLE,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        .set_footer(
            text=plugin.bot.footer_text, icon=plugin.bot.display_avatar_url  # type: ignore
        )
        .set_author(
            name="DayZ++",
            icon=plugin.bot.display_avatar_url,  # type: ignore
            url="https://discord.com/users/867376409965363200",
        )
    )

    await ctx.respond(
        f"<@{ticket_owner_id}>",
        embed=embed,
        components=CloseRequestConfirmationView(
            user_id=ticket_owner_id
        ).build(),
        user_mentions=True,
    )


def load(bot: Bot) -> None:
    bot.add_plugin(plugin)


def unload(bot: Bot) -> None:
    bot.remove_plugin(plugin)
