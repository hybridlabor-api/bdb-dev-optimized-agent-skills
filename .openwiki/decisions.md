# Design Decisions

- **Strict Privacy**: Implemented a mandatory ban on hardcoded local usernames to ensure the skills pack can be distributed and used universally without leaking PII.
- **OpenWiki Direct API**: Decided to replace the `agy --prompt` invocation in the OpenWiki daemon with direct Gemma 4 API calls via `google-genai`. This was chosen because spawning new instances of the agent recursively caused infinite loops and rapid quota drain.
- **memB as Core**: Enforced memB as a core (non-toggleable) module in the installer to ensure all agents share a unified offline semantic memory.
