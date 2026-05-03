System Notifications in ThoughtMachine

Overview

System notifications are messages generated internally to inform the agent about token usage, turn limits, and context clearing. They appear in user_history and LLM context with role='user' and a [SYSTEM NOTIFICATION] prefix. A metadata flag is_system_notification distinguishes them for internal processing (turn counting, summary insertion).

Why role = "user"

LLM providers (OpenAI, Anthropic, etc.) typically ignore messages with role = "system" when it comes to the agent reacting to warnings. Using role = "user" ensures the agent "hears" the notification and can take action (e.g., calling SummarizeTool to prune the conversation). This is a deliberate design choice to make the LLM respond to token and turn warnings.

Content formats (legacy)

All new notifications use [SYSTEM NOTIFICATION]. Legacy prefixes [**SYSTEM NOTIFICATION**] and [****SYSTEM NOTIFICATION****] exist only in old sessions and are not generated anymore. Fallback content‑based skipping recognises all three.

Metadata flag: is_system_notification

All system notifications now include a boolean metadata field in their message dictionary:

"is_system_notification": true

Where the flag is added

The flag is added at creation time in agent/core/agent.py at the following locations:
- ~Line 523: turn warning events (pre-LLM, _handle_state_event)
- ~Line 536: token warning events (pre-LLM, _handle_state_event)
- ~Lines 595, 607: secondary token/turn warning paths
- ~Lines 318-325: post-tool token warnings (_update_tokens_after_tool)
- ~Line 872: context cleared (unwarning) after summarisation

Note that countdown expiry notifications no longer exist.

Where the flag is used

The flag is read only in two internal methods of the agent, both related to turn counting and summary placement:
- _find_summary_insertion_index – skips flagged messages when calculating where to insert a summary system message during pruning. This prevents notifications from shifting the insertion point.
- _group_messages_into_turns – skips flagged messages when grouping conversation history into logical turns. This prevents notifications from creating empty or spurious turns.

Where the flag is NOT used

The flag is not used in the context builder (SummaryBuilder.build). That builder copies all messages from user_history that appear after the latest summary insertion point, regardless of the flag. Therefore, system notifications that occur after the summary are always included in the LLM context. The flag does not cause notifications to be filtered out.

Lifecycle of a system notification

1. Trigger: AgentState.update_token_state() or update_turn_state() detects soft or critical threshold. No countdown.

2. Creation: The agent’s event handler (e.g., _handle_state_event in agent.py) creates a message dictionary with role = "user", a content string containing one of the [SYSTEM NOTIFICATION] prefixes, and the metadata flag is_system_notification = True.

3. Injection: The dictionary is appended to user_history immediately via _add_to_conversation or directly appended. No deletion or reordering occurs at this stage.

4. Summarisation (pruning): Notifications are skipped during turn counting, so summary insertion index is unaffected. The unwarning is appended after the summary tool result.

5. LLM context building: SummaryBuilder.build scans user_history starting from the summary insertion point (or the beginning if no summary). It copies all messages from that point forward, including any system notifications that appear after that point. Because the flag did not affect the insertion point, notifications appear in the correct chronological order relative to user and assistant messages.

6. GUI display: The Qt GUI reads user_history directly. The MessageRenderer recognises the is_system_notification flag and renders notifications with special styling (e.g., gray background, italic text) to distinguish them from normal user messages.

Backward compatibility

Old session files (saved before the metadata flag was introduced) do not have is_system_notification in their messages. To support them, the turn‑counting methods contain fallback content‑based checks. They look for the substrings "[SYSTEM NOTIFICATION]" and "[**SYSTEM NOTIFICATION**]" in the message content. The four‑asterisk pattern "[****SYSTEM NOTIFICATION****]" was originally missing and has been added to the fallback as well. This ensures that old sessions continue to behave correctly (notifications are still skipped during turn counting), while new sessions use the more robust metadata flag.

Testing verification

To verify: Run a conversation that triggers soft warning, then critical warning. The agent should see a [SYSTEM NOTIFICATION] message. After a tool result increases tokens further, another warning should appear immediately (via _update_tokens_after_tool). No 'countdown expired' messages appear.

Common pitfalls

- Do not change the role of system notifications to "system". The LLM will ignore them.
- Do not rely on content string matching alone; use the metadata flag for new code.
- Do not add the flag to normal user messages.
- The flag is intended only for internal turn counting; it does not need to be stripped before sending to the LLM, but stripping it is harmless if desired for API cleanliness.
- Do not rely on countdown logic – it has been removed.

Related components

- agent/core/agent.py: creation of notifications, _find_summary_insertion_index, _group_messages_into_turns
- agent/core/state.py: token and turn monitoring (AgentState.update_token_state)
- session/context_builder.py: SummaryBuilder.build (includes notifications in LLM context)
- qt_gui/panels/message_renderer.py: special rendering for notifications
- docs/pruning_system.md: broader context on pruning and summarisation