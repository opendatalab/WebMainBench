from webmainbench.metrics import MetricCalculator


def test_metric_calculator_passes_config_to_default_metrics():
    config = {
        "use_llm": True,
        "llm_base_url": "http://example.test/v1",
        "llm_api_key": "test-key",
        "llm_model": "test-model",
    }

    calculator = MetricCalculator(config)

    assert calculator.metrics["formula_edit"].config == config
    assert calculator.metrics["text_edit"].config == config
