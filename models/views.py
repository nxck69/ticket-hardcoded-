import datetime
from typing import Any

import hikari
import miru

from models import Colour

SUGGESTIONS_CHANNEL_ID = 983726366283411497


class TicketPanelSelect(miru.Select):
    def __init__(self) -> None:
        super().__init__(
            options=(
                miru.SelectOption(
                    label="Custom Bot Request",
                    value="custom_bot",
                    emoji="⚙",
                ),
                miru.SelectOption(
                    label="General Question",
                    value="general_question",
                    emoji="❓",
                ),
                miru.SelectOption(
                    label="Configuration Question",
                    value="configuration_question",
                    emoji="⚙",
                ),
                miru.SelectOption(
                    label="Apply for Support",
                    value="support_apply",
                    emoji="📩",
                ),
                miru.SelectOption(
                    label="Refund",
                    value="refund",
                    emoji="💵",
                ),
                miru.SelectOption(
                    label="Bug Report", value="bug_report", emoji="⛔"
                ),
            ),
            placeholder="Select a Category ...",
            custom_id="ticket_panel",
        )


class TicketPanelView(miru.View):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs, timeout=None)
        self.add_item(TicketPanelSelect())


class TicketCloseView(miru.View):
    def __init__(self, channel_id: int, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs, timeout=None)
        self.add_item(
            miru.Button(
                label="Close",
                style=hikari.ButtonStyle.DANGER,
                custom_id=f"TICKET:CLOSE:{channel_id}",
            )
        )


class TicketCloseConfirmationView(miru.View):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.add_item(
            miru.Button(
                label="Confirm",
                style=hikari.ButtonStyle.SUCCESS,
                custom_id="TICKET:CONFIRM:CLOSE",
            )
        )
        self.add_item(
            miru.Button(
                label="Cancel",
                style=hikari.ButtonStyle.DANGER,
                custom_id="TICKET:CANCEL:CLOSE",
            )
        )


class CloseRequestConfirmationView(miru.View):
    def __init__(self, user_id: int, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.add_item(
            miru.Button(
                label="Confirm",
                style=hikari.ButtonStyle.SUCCESS,
                custom_id=f"TICKET:CLOSE-REQUEST:CONFIRM:{user_id}",
            )
        )
        self.add_item(
            miru.Button(
                label="Decline",
                style=hikari.ButtonStyle.DANGER,
                custom_id=f"TICKET:CLOSE-REQUEST:CANCEL:{user_id}",
            )
        )


class SuggestionModal(miru.Modal):
    suggestion = miru.TextInput(
        label="Suggestion",
        placeholder="Type your suggestion here.",
        style=hikari.TextInputStyle.PARAGRAPH,
        required=True,
        min_length=1,
        max_length=1024,
    )

    async def callback(self, ctx: miru.ModalContext) -> None:
        suggestion: str = [value for value in ctx.values.values()][0]

        embed = (
            hikari.Embed(
                description=f"> **Suggestion**\n```\n{suggestion}```",
                colour=Colour.BLURPLE,
                timestamp=datetime.datetime.now(datetime.timezone.utc),
            )
            .set_footer(
                text=ctx.bot.footer_text, icon=ctx.bot.display_avatar_url  # type: ignore
            )
            .set_author(
                name=str(ctx.author),
                icon=ctx.author.display_avatar_url,  # type: ignore
                url=f"https://discord.com/users/{ctx.author.id}",
            )
        )

        message_proxy = await ctx.bot.rest.create_message(
            SUGGESTIONS_CHANNEL_ID, embed=embed
        )
        await ctx.bot.rest.add_reaction(
            SUGGESTIONS_CHANNEL_ID, message_proxy, "👍"
        )
        await ctx.bot.rest.add_reaction(
            SUGGESTIONS_CHANNEL_ID, message_proxy, "👎"
        )


class SuggestionPanelView(miru.View):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs, timeout=None)
        self.add_item(
            miru.Button(
                style=hikari.ButtonStyle.SECONDARY,
                label="Suggestion",
                custom_id="SUGGESTION:CREATE",
                emoji="📩",
            )
        )
