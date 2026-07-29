"""
Auto-responder for BOXX chatbot test conversations.

Analyses bot replies and generates contextual follow-up responses
so each test case runs a full conversation until the bot naturally
concludes the session.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

logger = logging.getLogger("auto_responder")

# Hard cap — no conversation runs longer than this
MAX_TURNS = 25

# Stuck detection thresholds
SAME_REPLY_THRESHOLD = 3       # same pattern matched N times → stuck
STALLED_JOURNEY_THRESHOLD = 5  # turns without journey change → stuck
EMPTY_REPLY_LIMIT = 2          # empty replies → stuck


# ---------------------------------------------------------------------------
# CTA / Button tracking
# ---------------------------------------------------------------------------


def extract_buttons(messages: list[dict]) -> list[dict]:
    """Extract all unique CTA buttons from API response messages.

    Each message may have ``type="interactive"`` with ``interactive_data``
    containing ``buttons`` with ``title``, ``url``, and ``type`` fields.
    Returns deduplicated list keyed by ``title``.
    """
    if not messages:
        return []
    buttons: list[dict] = []
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        if msg.get("type") != "interactive":
            continue
        idata = msg.get("interactive_data")
        if not idata or not isinstance(idata, dict):
            continue
        for btn in idata.get("buttons") or []:
            if isinstance(btn, dict) and btn.get("title"):
                buttons.append(btn)
    # Deduplicate by title (first occurrence wins)
    seen: set[str] = set()
    unique: list[dict] = []
    for b in buttons:
        t = b.get("title", "")
        if t and t not in seen:
            seen.add(t)
            unique.append(b)
    return unique


def extract_choice_buttons(messages: list[dict]) -> list[dict]:
    """Like :func:`extract_buttons` but filters out action-link buttons.

    Action links (e.g. "Call 1930" → ``tel:1930``, "Open link" → ``https://…``)
    have a ``url`` field and represent external actions.  Choice buttons have
    *no* ``url`` field and represent navigation options (e.g. "Yes", "No",
    "Continue current journey") — these are the ones a real user would click
    to choose a conversation path.
    """
    all_buttons = extract_buttons(messages)
    return [b for b in all_buttons if not b.get("url")]


class ButtonTracker:
    """Tracks which CTA buttons have been presented and clicked during a conversation."""

    def __init__(self):
        self._seen: list[dict] = []       # all unique buttons seen, in order
        self._clicked: set[str] = set()    # titles that have been clicked

    def register(self, buttons: list[dict]):
        """Register newly-seen buttons that haven't been seen before."""
        known = {b.get("title", "") for b in self._seen}
        for b in buttons:
            t = b.get("title", "")
            if t and t not in known:
                self._seen.append(b)
                known.add(t)

    def next_unclicked(self) -> Optional[dict]:
        """Return the first button whose title hasn't been clicked yet, or None."""
        for b in self._seen:
            if b.get("title", "") not in self._clicked:
                return b
        return None

    def mark_clicked(self, title: str):
        """Record that a button with *title* was clicked."""
        if title:
            self._clicked.add(title)

    @property
    def all_clicked(self) -> bool:
        """True when every seen button has been clicked at least once."""
        return not bool(self._seen) or len(self._clicked) >= len(self._seen)

    @property
    def pending(self) -> int:
        return len(self._seen) - len(self._clicked)


# ---------------------------------------------------------------------------
# Pattern → response tables
# ---------------------------------------------------------------------------

# Each entry: (patterns, response_for_self, response_for_other)
# where response_for_other is used when original message names a third party.
_QUERIES = [
    # ── Identity / family question ──
    (
        [r"is this happening to you", r"to you.*or.*family", r"aapke sath.*ho raha",
         r"aap.*ya.*parivar"],
        "Yes, it's happening to me. Please help.",
        None,  # dynamic — extracted from original message
    ),
    # ── Money deducted? ──
    (
        [r"(any |has |was )?money.*(deduct|debit|gone|lost|cut)",
         r"loss of fund", r"paise.*kata", r"kya paisa kata",
         r"any amount.*(debit|deduct)"],
        "Yes, money was deducted from my account. I have suffered a loss.",
        "No, no money has been deducted yet but I am worried.",
    ),
    # ── OTP shared? ──
    (
        [r"(share|gave|told).*otp", r"otp.*(share|bataya|diya|shared|given|used)",
         r"did you.*otp", r"otp.*(pin|password)",
         r"kya.*otp.*diya", r"aapne.*otp",
         r"otp.*(was )?(shared|entered|compromised)"],
        "Yes, I shared the OTP with them.",
        "No, I did not share any OTP.",
    ),
    # ── Link clicked / visited? ──
    (
        [r"click.*link", r"link.*(click|open|visit)", r"visit.*(site|page|website)",
         r"did you (click|open|visit)", r"aapne.*link.*(click|khol)"],
        "Yes, I clicked on the link.",
        "No, I did not click any link but I am still worried.",
    ),
    # ── Transaction / payment method ──
    (
        [r"(through|using|via).*(upi|card|banking)", r"how.*(pay|transact|money.*taken)",
         r"payment method", r"(debit|credit).*card", r"net banking",
         r"(upi|card|net.*banking).*(,|or|via)",
         r"how.*(sent|transferred|send).*(money|payment)",
         r"upi.*or.*card", r"kaise.*payment", r"kis.*(tarah|madhyam).*paise"],
        "I paid through UPI using Google Pay.",
        None,
    ),
    # ── When did this happen? ──
    (
        [r"when did this happen", r"how long ago", r"when.*occur",
         r"kab hua", r"kab.*happen"],
        "This just happened a short while ago, maybe an hour back.",
        None,
    ),
    # ── App / software installation (AnyDesk / TeamViewer) ──
    (
        [r"install.*(app|anydesk|teamviewer|software)",
         r"download.*(app|anything)",
         r"(anydesk|teamviewer|remote).*(app|install)",
         r"aapne.*(app|kuch).*(install|download)",
         r"koi.*app.*(install|download)"],
        "Yes, I installed the app they told me to install.",
        "No, I did not install anything on my phone.",
    ),
    # ── Complaint filed? ──
    (
        [r"(file|register|report).*(complaint|fir|report)",
         r"report.*(1930|cybercrime|police|portal)",
         r"did you.*(call|contact).*(1930|cyber|police)",
         r"have you.*(file|report).*(complaint|fir)",
         r"shikayat.*ki"],
        "No, I have not filed any complaint yet. That is why I am here.",
        None,
    ),
    # ── Which bank? ──
    (
        [r"which bank", r"bank.*(name|account)", r"aapka.*bank",
         r"kis.*bank"],
        "SBI Bank.",
        None,
    ),
    # ── Amount? ──
    (
        [r"how much (money|amount)", r"transaction amount",
         r"kitna paisa", r"amount.*(deduct|gone|lost)",
         r"kitan.*(rasheed|number|paise)"],
        "Around ₹15,000 was involved.",
        None,
    ),
    # ── Tell me what happened / elaborate ──
    (
        [r"please tell me what happened", r"tell me more",
         r"share what happened", r"describe.*situation",
         r"kya hua", r"tell me.*details", r"what.*happened",
         r"can you (share|tell|describe)", r"kya.*happened"],
        None,  # dynamic — _elaborate_scenario()
        None,
    ),
    # ── Confirmation request (bot summarised and asks "Is that correct?") ──
    (
        [r"is that correct", r"does that (look|sound) right",
         r"am i correct", r"confirmation",
         r"is this what you meant", r"acknowledge"],
        "Yes, that is correct. Please go ahead.",
        None,
    ),
    # ── Processing / checking reply ──
    (
        [r"give me a second", r"checking this properly",
         r"let me look", r"let me check", r"one moment"],
        "Yes please, I am waiting for your help.",
        None,
    ),
    # ── Bot gives advice / next steps (call bank, report, block, etc.) ──
    # When bot provides concrete action items, acknowledge and try to close.
    (
        [r"(call|contact).*(bank|helpline|1930|police|support)",
         r"report.*(cybercrime|portal|crime|website)",
         r"(take|follow).*(steps|action|these)",
         r"secure.*(account|card|fund|bank)",
         r"block.*(account|card|transaction)",
         r"next steps",
         r"here (are|is|(')?s).*(step|what).*(do|next)",
         r"please.*(visit|go to).*(cybercrime|gov)"],
        "Thank you, I understand what to do. Is there anything else I should be aware of?",
        None,
    ),
    # ── Bot could not match / unsure ──
    (
        [r"couldn't match this", r"can't confirm", r"cannot confirm",
         r"not a scam pattern", r"could not match"],
        "What should I do to stay safe? Please guide me.",
        None,
    ),
    # ── Anti-scam / can't assist (user sounded like a scammer) ──
    (
        [r"(sorry|cannot|can not|won't).*(scam|defraud|thag|cheat)",
         r"instructions to scam", r"doosron ko thagne",
         r"nahee.*madad.*kar"],
        "__BLOCKED__",  # bot refused to help — session effectively dead
        None,
    ),
    # ── Anything else? (closing question) ──
    (
        [r"(is there )?anything else", r"any other (question|help|thing)",
         r"can i help you with anything", r"what else (can|would)",
         r"aur kuch", r"do you have any other"],
        "__CLOSE__",
        None,
    ),
    # ── Final closing / gratitude ──
    (
        [r"stay safe", r"take care", r"have a good day",
         r"thank you for reaching", r"thank you.*(reach|contact|message)",
         r"goodbye", r"closing this", r"conclud", r"glad.*help",
         r"hope.*(help|assist)", r"dhanyavad", r"khayal.*rakh"],
        "__SESSION_CONCLUDED__",
        None,
    ),
]


def _match_pattern(text: str, patterns: list[str]) -> bool:
    """Return True if any regex *pattern* matches *text* (case-insensitive)."""
    for p in patterns:
        if re.search(p, text):
            return True
    return False


def _extract_relation(text: str) -> Optional[str]:
    """Extract a named relation from the user's message, e.g. 'my father'."""
    m = re.search(
        r"\b(?:my )?(father|mother|brother|sister|uncle|aunt|"
        r"grandmother|grandfather|grandma|grandpa|mom|dad|"
        r"mummy|papa|chacha|mama|bhai|friend|neighbor|"
        r"boss|colleague|wife|husband|son|daughter)\b",
        text, re.IGNORECASE,
    )
    return m.group(0).lower() if m else None


def _elaborate_scenario(original_message: str, notes: str) -> str:
    """Generate a detailed scenario elaboration matching the test case."""
    msg = original_message.lower()

    if "kyc" in msg or "aadhaar" in msg or "aadhar" in msg:
        return ("I received an SMS saying my KYC will expire. "
                "It asked me to click a link and update my details. "
                "The message looked very official like from my bank. "
                "Can you tell me if this is a scam and what to do?")
    if "otp" in msg:
        return ("Someone called pretending to be from my bank and said "
                "there was suspicious activity on my account. They asked "
                "for the OTP to verify and I gave it to them. Now I am "
                "worried. What should I do?")
    if "click" in msg or "link" in msg:
        return ("I clicked on a link I received in a message. It opened "
                "a page that looked real but now I am scared I may have "
                "given away my information. Please help.")
    if any(w in msg for w in ["pay", "paid", "money", "deduct", "loss", "paise"]):
        return ("I made a payment through a link someone sent me. Now "
                "I realise it might have been a scam. My money is gone. "
                "What can I do to get it back?")
    if "call" in msg:
        return "I received a phone call from someone claiming to be official. They asked for my personal details. Please guide me."
    if any(w in msg for w in ["job", "work", "earn", "registration fee"]):
        return ("I saw a job offer online with very good pay. They are "
                "asking me to pay a registration fee first. Is this a scam?")
    if any(w in msg for w in ["invest", "bitcoin", "crypto", "stock", "trading"]):
        return ("I invested in a scheme that promised very high returns. "
                "Now I cannot withdraw my money. I think I have been cheated.")
    if any(w in msg for w in ["digital arrest", "police", "video call", "arrest", "warrant"]):
        return ("Someone called me on a video call pretending to be a "
                "police officer. They said I have a case against me and "
                "demanded money. I am very scared.")
    if any(w in msg for w in ["loan", "threat"]):
        return ("I downloaded a loan app and now they are threatening me "
                "and my contacts for repayment even though I already paid. "
                "They are sending abusive messages.")
    if any(w in msg for w in ["whatsapp", "telegram", "group"]):
        return ("I was added to a WhatsApp group that offers investment "
                "tips and tasks. Now they are asking for money. Is this a scam?")
    if any(w in msg for w in ["fastag", "toll"]):
        return ("I received a message about my FASTag low balance asking "
                "me to pay through a link. The message looks urgent.")
    if any(w in msg for w in ["father", "mother", "uncle", "aunt", "friend",
                               "grand", "neighbor", "boss", "sister", "brother",
                               "mummy", "papa", "chacha", "bhai"]):
        rel = _extract_relation(msg) or "my family member"
        return (f"This is about {rel}. {original_message}. "
                f"I want to help {rel}. Please tell me what they should do.")
    if "scam" in msg:
        return f"I think this is a scam but I am not sure. {original_message}. Please confirm and guide me."

    # Default — use the original message as context
    return (f"I am worried about something. {original_message[:200]}. "
            "Please tell me if this is a scam and what I should do next.")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def is_session_closed(bot_reply: str, analysis: dict) -> bool:
    """Check if the bot has concluded the conversation."""
    if not bot_reply:
        return False
    reply_lower = bot_reply.lower()
    closing = [
        "thank you for reaching", "have a good day",
        "take care", "stay safe", "goodbye",
        "glad i could help", "glad to help",
        "hope this helps", "hope you stay safe",
        "dhanyavad", "khayal rakh",
    ]
    for phrase in closing:
        if phrase in reply_lower:
            return True
    return False


class ConversationState:
    """Tracks conversation health for stuck detection."""

    def __init__(self):
        self.last_pattern_idx: Optional[int] = None
        self.pattern_repeat_count: int = 0
        self.prev_journey: str = ""
        self.journey_stall_count: int = 0
        self.empty_reply_count: int = 0
        self.total_response_attempts: int = 0

    def update(self, analysis: dict):
        """Update state after a bot reply (call before generating next response)."""
        journey = (analysis or {}).get("journey", "") or ""
        if journey and journey == self.prev_journey:
            self.journey_stall_count += 1
        elif journey:
            self.journey_stall_count = 0
        # If journey is empty and prev was also empty, count as stalled
        elif not journey and not self.prev_journey:
            self.journey_stall_count += 1
        self.prev_journey = journey or self.prev_journey
        self.total_response_attempts += 1

    def mark_pattern(self, pattern_idx: int):
        """Track which pattern matched to detect repeated same-response loops."""
        if pattern_idx == self.last_pattern_idx:
            self.pattern_repeat_count += 1
        else:
            self.last_pattern_idx = pattern_idx
            self.pattern_repeat_count = 0

    def is_stuck(self) -> Optional[str]:
        """Return error message if stuck, else None."""
        if self.empty_reply_count >= EMPTY_REPLY_LIMIT:
            return "Bot returned empty reply repeatedly — conversation stuck"
        if self.pattern_repeat_count >= SAME_REPLY_THRESHOLD:
            return f"Bot asking same question repeatedly ({self.pattern_repeat_count}x) — conversation stuck"
        if self.journey_stall_count >= STALLED_JOURNEY_THRESHOLD:
            return (f"Journey not progressing for {self.journey_stall_count} turns "
                    f"(journey='{self.prev_journey}') — conversation stuck")
        return None

    def mark_empty_reply(self):
        self.empty_reply_count += 1


def generate_response(
    bot_reply: str,
    original_message: str,
    scenario_notes: str,
    state: ConversationState,
    turn_count: int,
) -> Optional[str]:
    """Generate an appropriate follow-up response to the bot.

    Returns:
        str              → send this response to the bot
        "__CLOSE__"      → user tells bot "no, that's all" — should lead to close
        "__SESSION_CONCLUDED__" → bot already closed the session
        "__BLOCKED__"    → bot refused to assist (anti-scam filter)
        None             → no suitable response found (fallback to generic)
    """
    if not bot_reply or not bot_reply.strip():
        # Empty reply — return None so caller sends a generic nudge.
        # NOTE: we do NOT call state.mark_empty_reply() here because the
        # test loop's response-processing code already handles that.
        return None

    reply_lower = bot_reply.lower()

    for idx, (patterns, response_self, response_other) in enumerate(_QUERIES):
        if not _match_pattern(reply_lower, patterns):
            continue

        state.mark_pattern(idx)
        response = response_self  # default

        # Handle dynamic responses
        if response is None and patterns is _QUERIES[0][0]:
            # Identity question — respond with relation or "me"
            relation = _extract_relation(original_message)
            if relation:
                response = f"Yes, it's happening to {relation}. Please help."
            else:
                response = "Yes, it's happening to me. Please help."

        # Elaboration — generate dynamic story
        if response is None and idx == 9:  # "tell me what happened"
            response = _elaborate_scenario(original_message, scenario_notes)

        # Money question — choose based on input context
        if response_other is not None and idx == 1:  # money question
            has_loss = any(
                w in original_message.lower()
                for w in ["money gone", "money lost", "paise kata", "paise gaye",
                          "deducted", "stolen", "loss", "withdraw", "paid",
                          "kata", "gaya", "cut", "took", "empty"]
            )
            response = response_self if has_loss else response_other

        # OTP question — choose based on input context
        if response_other is not None and idx == 2:  # OTP question
            mentioned_otp = "otp" in original_message.lower() or "share" in original_message.lower()
            response = response_self if mentioned_otp else response_other

        # Link clicked — choose based on input context
        if response_other is not None and idx == 3:  # link question
            clicked = "click" in original_message.lower() or "link" in original_message.lower()
            response = response_self if clicked else response_other

        # App installed — choose based on input context
        if response_other is not None and idx == 6:  # app install question
            installed = any(
                w in original_message.lower()
                for w in ["anydesk", "teamviewer", "install", "download"]
            )
            response = response_self if installed else response_other

        return response

    # ── No pattern matched ──
    if turn_count > 2:
        # We are past the first few turns — try a generic nudge
        return "Please help me, what should I do next?"
    return None
