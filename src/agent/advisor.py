"""LangChain Attribution Advisor agent.

Reads the composite attribution table and the optimiser's recommended
allocation, then autonomously:

1. Identifies the top-N (promote) and bottom-N (trim) channels by attribution.
2. Generates a plain-English reallocation rationale. If a Groq/LangChain LLM is
   configured it uses the model; otherwise it falls back to a deterministic,
   rule-based narrative so the loop always closes.
3. Translates the optimiser's spend deltas into per-channel bid adjustments and
   calls the Google Ads + Meta clients to apply (or simulate) them.

This is the component that "closes the optimisation loop without human
intervention": attribution insight in, ad-platform bid changes out.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

import pandas as pd

from .google_ads_client import GoogleAdsClient
from .meta_ads_client import MetaAdsClient


@dataclass
class ReallocationPlan:
    """The agent's decision: rationale + concrete bid changes."""

    promote: list[str]
    trim: list[str]
    rationale: str
    bid_changes: list[dict] = field(default_factory=list)
    llm_used: bool = False


# Channels routed to each ad platform for bid actuation.
_GOOGLE_CHANNELS = {"Paid Search", "Display", "Video", "Organic Search", "Direct"}
_META_CHANNELS = {"Paid Social"}


class AttributionAdvisor:
    """Autonomous budget-reallocation advisor."""

    def __init__(
        self,
        top_n: int = 3,
        bottom_n: int = 3,
        max_bid_shift_pct: float = 0.25,
        apply_changes: bool = False,
    ):
        self.top_n = top_n
        self.bottom_n = bottom_n
        self.max_bid_shift_pct = max_bid_shift_pct
        self.google = GoogleAdsClient(apply_changes=apply_changes)
        self.meta = MetaAdsClient(apply_changes=apply_changes)

    # ------------------------------------------------------------------
    def recommend(
        self, attribution: pd.DataFrame, allocation: pd.DataFrame
    ) -> ReallocationPlan:
        """Produce and execute a reallocation plan."""
        ranked = attribution.sort_values("composite_share", ascending=False)
        promote = list(ranked.index[: self.top_n])
        trim = list(ranked.index[-self.bottom_n :])

        rationale, llm_used = self._make_rationale(ranked, promote, trim)

        bid_changes = self._actuate(allocation)

        return ReallocationPlan(
            promote=promote,
            trim=trim,
            rationale=rationale,
            bid_changes=bid_changes,
            llm_used=llm_used,
        )

    # ------------------------------------------------------------------
    def _actuate(self, allocation: pd.DataFrame) -> list[dict]:
        """Map spend deltas to capped bid changes and push to ad platforms."""
        changes: list[dict] = []
        for channel, row in allocation.iterrows():
            delta_pct = float(row["delta_pct"])
            # Cap the bid move so the agent never makes a reckless adjustment.
            shift = max(-self.max_bid_shift_pct, min(self.max_bid_shift_pct, delta_pct))
            if abs(shift) < 0.01:
                continue
            current_bid = 1.0  # normalised baseline bid modifier
            new_bid = round(current_bid * (1 + shift), 4)
            client = self.google if channel in _GOOGLE_CHANNELS else self.meta
            if channel not in _GOOGLE_CHANNELS and channel not in _META_CHANNELS:
                client = self.google  # default routing
            rec = client.adjust_bid(
                channel=str(channel),
                current_bid=current_bid,
                new_bid=new_bid,
                reason=f"composite-attribution reallocation ({shift:+.0%})",
            )
            changes.append(rec)
        return changes

    # ------------------------------------------------------------------
    def _make_rationale(
        self,
        ranked: pd.DataFrame,
        promote: list[str],
        trim: list[str],
    ) -> tuple[str, bool]:
        llm = self._try_llm(ranked, promote, trim)
        if llm is not None:
            return llm, True
        return self._rule_based_rationale(ranked, promote, trim), False

    def _rule_based_rationale(
        self, ranked: pd.DataFrame, promote: list[str], trim: list[str]
    ) -> str:
        top_lines = [
            f"  - Increase investment in {c} "
            f"(composite credit {ranked.loc[c, 'composite_share']:.1%})"
            for c in promote
        ]
        bottom_lines = [
            f"  - Reduce investment in {c} "
            f"(composite credit {ranked.loc[c, 'composite_share']:.1%})"
            for c in trim
        ]
        return (
            "Attribution Advisor recommendation:\n"
            "High-attribution channels - redirect budget toward:\n"
            + "\n".join(top_lines)
            + "\nLow-attribution channels - trim spend on:\n"
            + "\n".join(bottom_lines)
            + "\nRationale: budget is being moved from channels with low marginal "
            "Shapley/Markov contribution to those carrying genuine incremental "
            "conversions, maximising expected blended ROAS within budget limits."
        )

    def _try_llm(
        self,
        ranked: pd.DataFrame,
        promote: list[str],
        trim: list[str],
    ) -> str | None:
        if not os.environ.get("GROQ_API_KEY"):
            return None
        try:  # pragma: no cover - requires GROQ_API_KEY
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_groq import ChatGroq

            model = ChatGroq(
                model=os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile"),
                temperature=0.2,
            )
            table = ranked[["composite_share"]].to_markdown()
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "You are a marketing budget optimisation advisor. Given "
                        "multi-touch attribution credit per channel, write a concise "
                        "reallocation rationale (max 120 words).",
                    ),
                    (
                        "human",
                        "Attribution credit per channel:\n{table}\n\n"
                        "Promote: {promote}\nTrim: {trim}\n"
                        "Explain the reallocation decision.",
                    ),
                ]
            )
            chain = prompt | model
            resp = chain.invoke(
                {"table": table, "promote": ", ".join(promote), "trim": ", ".join(trim)}
            )
            return str(resp.content)
        except Exception:
            return None
