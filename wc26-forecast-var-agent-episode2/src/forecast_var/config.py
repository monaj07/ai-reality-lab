"""Project-wide configuration for Forecast VAR.

The live OpenAI path is optional. Offline demos and tests use deterministic mock
agents, but when a live model is requested we keep the default in one place so
README examples, scripts, and agent code do not drift.
"""

DEFAULT_OPENAI_MODEL = "gpt-5.4-nano"
