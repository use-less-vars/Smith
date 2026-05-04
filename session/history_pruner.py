"""
History Pruner: Pure-function-based pruning of user_history at save time.

Takes the full user_history list and returns a pruned copy, leaving the
original untouched. Designed to be called from FileSystemSessionStore.save_session
to reduce on-disk session file size while preserving enough context for
the GUI and future agent runs.

The algorithm:
1. Count summary messages (role='system' with summary=True).
2. If count < min_summaries_before_pruning → return copy unchanged.
3. Find the second-last summary index → this is cut_idx.
4. Partition: old = user_history[:cut_idx], safe = user_history[cut_idx:].
5. Walk 'old' and compact turns (user→final or user→last assistant).
6. Return compacted + safe.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────

FINAL_TOOL_NAMES: Set[str] = {'Final', 'FinalReport', 'RequestUserInteraction'}
"""Tool names that signal the end of a logical turn."""

# ──────────────────────────────────────────────────────────────────────
# Policy
# ──────────────────────────────────────────────────────────────────────


@dataclass
class PruningPolicy:
    """Configuration for how aggressively to prune history.

    Attributes:
        keep_reasoning: If True, keep assistant reasoning_content if present.
        keep_all_final_turns: If True, keep the full turn that ends with a Final tool.
        keep_non_final_assistant: If True, keep the last assistant message even
            when no Final tool was called (natural turn end).
        min_summaries_before_pruning: Minimum number of summary messages that
            must exist before any pruning is performed.
    """
    keep_reasoning: bool = False
    keep_all_final_turns: bool = True
    keep_non_final_assistant: bool = True
    min_summaries_before_pruning: int = 2


# ──────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────


def prune_user_history(
    user_history: List[Dict[str, Any]],
    policy: PruningPolicy = PruningPolicy(),
) -> List[Dict[str, Any]]:
    """Return a pruned copy of *user_history* according to *policy*.

    The original list is never mutated.  If pruning is not warranted (e.g.
    fewer summaries than *min_summaries_before_pruning*) a shallow copy of
    the input is returned.
    """
    # 1. Count summary messages
    summary_indices = _find_summary_indices(user_history)
    if len(summary_indices) < policy.min_summaries_before_pruning:
        logger.debug(
            'prune_user_history: only %d summaries (< %d), returning copy',
            len(summary_indices), policy.min_summaries_before_pruning,
        )
        return list(user_history)

    # 2. Determine cut point — second-last summary
    cut_idx = summary_indices[-2]

    # 3. Partition
    old_segment = user_history[:cut_idx]
    safe_segment = user_history[cut_idx:]

    # 4. Compact old segment
    compacted = _compact_segment(old_segment, policy)

    # 5. Return compacted + safe
    result = compacted + safe_segment
    logger.debug(
        'prune_user_history: %d messages → %d (%.1f%% reduction)',
        len(user_history), len(result),
        (1 - len(result) / max(len(user_history), 1)) * 100,
    )
    return result


# ──────────────────────────────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────────────────────────────


def _find_summary_indices(
    user_history: List[Dict[str, Any]],
) -> List[int]:
    """Return ascending list of indices of summary messages."""
    indices: List[int] = []
    for i, msg in enumerate(user_history):
        if msg.get('role') == 'system' and msg.get('summary') is True:
            indices.append(i)
    return indices


def _is_system_notification(msg: Dict[str, Any]) -> bool:
    """Check if a message is a system notification (user-role informational)."""
    if msg.get('is_system_notification') is True:
        return True
    content = msg.get('content', '')
    if isinstance(content, str) and '[SYSTEM NOTIFICATION]' in content:
        return True
    return False


def _compact_segment(
    segment: List[Dict[str, Any]],
    policy: PruningPolicy,
) -> List[Dict[str, Any]]:
    """Compact a list of messages by collapsing turns.

    System messages and system notifications pass through unchanged.
    Non-system messages are grouped into turns (starting at each user
    message) and each turn is compacted.
    """
    result: List[Dict[str, Any]] = []

    # Separate pass-through messages from turnable messages
    passthrough: List[Dict[str, Any]] = []
    turn_messages: List[Dict[str, Any]] = []

    for msg in segment:
        role = msg.get('role', '')
        if role == 'system' or _is_system_notification(msg):
            passthrough.append(msg)
        else:
            turn_messages.append(msg)

    # Group turn_messages into turns
    turns = _group_turns(turn_messages)

    # Compact each turn
    for turn in turns:
        compacted_turn = _compact_turn(turn, policy)
        result.extend(compacted_turn)

    # Merge passthrough messages back in their original positions
    result = _merge_passthrough(passthrough, turn_messages, result)

    return result


def _group_turns(messages: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    """Group a flat list of non-system messages into turns.

    Each turn starts with a user message (that is not a system notification)
    and includes all messages until the next such user message (exclusive).
    """
    turns: List[List[Dict[str, Any]]] = []
    current_turn: List[Dict[str, Any]] = []

    for msg in messages:
        role = msg.get('role', '')
        if role == 'user' and not _is_system_notification(msg):
            if current_turn:
                turns.append(current_turn)
            current_turn = [msg]
        else:
            current_turn.append(msg)

    if current_turn:
        turns.append(current_turn)

    return turns


def _compact_turn(
    turn: List[Dict[str, Any]],
    policy: PruningPolicy,
) -> List[Dict[str, Any]]:
    """Compact a single turn, returning only the messages to keep.

    A turn is a list starting with a user message.
    """
    if not turn:
        return []

    # Always keep the user message
    result: List[Dict[str, Any]] = [turn[0]]

    # Collect all assistant messages in this turn
    assistant_msgs: List[Dict[str, Any]] = [
        msg for msg in turn if msg.get('role') == 'assistant'
    ]

    if not assistant_msgs:
        return result

    # Search for a final tool call among all assistants
    final_call: Optional[Dict[str, Any]] = None
    final_assistant: Optional[Dict[str, Any]] = None
    final_call_id: Optional[str] = None

    for asst in assistant_msgs:
        tool_calls = asst.get('tool_calls', [])
        if isinstance(tool_calls, list):
            for tc in tool_calls:
                func = tc.get('function', {})
                name = func.get('name', '') if isinstance(func, dict) else ''
                if isinstance(tc.get('function'), str):
                    # Handle legacy string format if any
                    pass
                if name in FINAL_TOOL_NAMES:
                    final_call = tc
                    final_assistant = asst
                    final_call_id = tc.get('id', '')
                    break
        if final_call:
            break

    if final_call is not None and final_assistant is not None:
        # Turn ends with a final tool call
        if policy.keep_all_final_turns:
            # Keep the assistant that has the final call
            result.append(final_assistant)

            # Find and keep the tool result matching the final call's id
            found_result = False
            for msg in turn:
                if (msg.get('role') == 'tool'
                        and msg.get('tool_call_id') == final_call_id):
                    result.append(msg)
                    found_result = True
                    break

            if not found_result:
                logger.warning(
                    'Compact turn: final tool call %s has no matching tool result',
                    final_call_id,
                )
        # else: aggressive mode would drop everything after user
        return result

    # No final tool found — keep last assistant with content
    if policy.keep_non_final_assistant:
        last_content_assistant: Optional[Dict[str, Any]] = None
        for asst in reversed(assistant_msgs):
            content = asst.get('content', '')
            if content and isinstance(content, str) and content.strip():
                last_content_assistant = asst
                break

            # Also check tool_calls — an assistant without content
            # but with tool_calls is meaningful
            tool_calls = asst.get('tool_calls', [])
            if tool_calls:
                last_content_assistant = asst
                break

        if last_content_assistant is not None:
            result.append(last_content_assistant)

    return result


def _merge_passthrough(
    passthrough: List[Dict[str, Any]],
    original_turnable: List[Dict[str, Any]],
    compacted_turnable: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Merge passthrough messages (system, notifications) back into the
    compacted turnable messages at roughly their original positions.

    This preserves the relative ordering of system messages w.r.t. the
    turnable messages they were originally interleaved with.

    Since we currently don't track exact original positions during
    separation, we prepend all passthrough messages. This is a
    simplification that works because system messages are typically
    at the beginning of the history (system prompt, summaries).
    """
    # Simple approach: system messages go before user turns
    # This preserves logical ordering for typical history layout
    return passthrough + compacted_turnable
