import types

import pytest


class DummyTokenizer:
    def __call__(
        self,
        text,
        add_special_tokens=True,
        truncation=False,
        max_length=None,
    ):
        # Simple, deterministic tokenization: whitespace split.
        tokens = str(text).split()
        if truncation and max_length is not None:
            tokens = tokens[: int(max_length)]
        # Use incremental ints as token IDs.
        return {"input_ids": list(range(len(tokens)))}

    def decode(self, input_ids, skip_special_tokens=True):
        # Return a stable string without raising type errors.
        return "x " * len(list(input_ids))


class PipelineRecorder:
    def __init__(self):
        self.last_kwargs = None

    def __call__(self, task, **kwargs):
        self.last_kwargs = kwargs

        def _runner(texts, **_run_kwargs):
            # Return deterministic outputs to avoid network/model downloads.
            if isinstance(texts, str):
                texts = [texts]
            return [{"label": "NEGATIVE", "score": 0.9} for _ in texts]

        return _runner


@pytest.fixture()
def engine_with_mocked_transformers(monkeypatch):
    import src.nlp.nlp_risk_engine as nlp_mod

    recorder = PipelineRecorder()

    dummy_auto_tokenizer = types.SimpleNamespace(
        from_pretrained=lambda _name: DummyTokenizer()
    )

    monkeypatch.setattr(nlp_mod, "AutoTokenizer", dummy_auto_tokenizer)
    monkeypatch.setattr(nlp_mod, "pipeline", recorder)

    # Avoid requiring spaCy model downloads for this unit test.
    monkeypatch.setattr(nlp_mod, "spacy", None)

    engine = nlp_mod.RiskNLPEngine()
    return engine, recorder


def test_tokenizer_object_is_used_in_pipeline(engine_with_mocked_transformers):
    engine, recorder = engine_with_mocked_transformers

    assert engine.tokenizer is not None
    assert recorder.last_kwargs is not None
    assert recorder.last_kwargs.get("tokenizer") is engine.tokenizer
    assert not isinstance(recorder.last_kwargs.get("tokenizer"), str)


def test_prepare_text_handles_empty_text(engine_with_mocked_transformers):
    engine, _ = engine_with_mocked_transformers

    assert engine._prepare_text_for_model("") == ""
    assert engine._prepare_text_for_model("   ") == ""


def test_prepare_text_truncates_long_text_without_type_errors(engine_with_mocked_transformers):
    engine, _ = engine_with_mocked_transformers

    long_text = "word " * 600
    prepared = engine._prepare_text_for_model(long_text)
    assert isinstance(prepared, str)

    token_ids = engine.tokenizer(prepared, truncation=False)["input_ids"]
    assert len(token_ids) <= 512


def test_prepare_text_handles_special_characters(engine_with_mocked_transformers):
    engine, _ = engine_with_mocked_transformers

    weird = "Blocked on API integration! @$%^&*()[]{};:'\"\\|,./<>?\nNew line"
    prepared = engine._prepare_text_for_model(weird)
    assert isinstance(prepared, str)
