from pathlib import Path
import json
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ChartConsistencyStaticTests(unittest.TestCase):
    def test_public_runtime_does_not_activate_personal_market_data(self) -> None:
        config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
        self.assertEqual(config["provider"], "demo")

        html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
        self.assertNotIn('value="alpaca"', html)
        self.assertNotIn('id="testAlpacaButton"', html)

    def test_detail_chart_defaults_to_rsi_and_labels_returns_clearly(self) -> None:
        script = (ROOT / "static" / "app.js").read_text(encoding="utf-8")

        self.assertIn('studies: ["RSI@tv-basicstudies"]', script)
        self.assertIn('detailMetric("5일 등락"', script)
        self.assertIn('detailMetric("20일선 이격"', script)
        self.assertIn("function chartSupportResistanceStrip(levels)", script)
        self.assertIn('data-detail-chart-mode="pulseedge"', script)
        self.assertIn('renderPulseEdgeFallbackChart(host, result, "analysis")', script)
        self.assertNotIn('studies: ["MASimple@tv-basicstudies"]', script)


if __name__ == "__main__":
    unittest.main()
