import pandas as pd
import plotly.graph_objects as go
import agent


def test_missing_api_key_error_is_user_friendly(monkeypatch):
    def missing_key():
        raise ValueError("GEMINI_API_KEY is missing. Add your Gemini API key to .env.")
    monkeypatch.setattr(agent, "_client", missing_key)
    answer, plot, table = agent.ask_assistant("How many tickets?")
    assert "GEMINI_API_KEY" in answer
    assert isinstance(plot, go.Figure)
    assert isinstance(table, pd.DataFrame)


def test_rate_limit_error_is_handled_without_exposing_secrets(monkeypatch):
    class FakeCompletions:
        def create(self, **kwargs):
            error = RuntimeError("429 quota reached for key=not-a-real-secret")
            error.status_code = 429
            raise error
    class FakeChat:
        completions = FakeCompletions()
    class FakeClient:
        chat = FakeChat()
    monkeypatch.setattr(agent, "_client", lambda: FakeClient())
    answer, _plot, _table = agent.ask_assistant("How many tickets?")
    assert "quota" in answer.lower() or "rate limit" in answer.lower()
    assert "not-a-real-secret" not in answer
