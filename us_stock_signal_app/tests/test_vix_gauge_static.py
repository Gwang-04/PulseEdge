from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class VixGaugeStaticTests(unittest.TestCase):
    def test_gauge_shows_app_specific_equal_width_interpretation_bands(self) -> None:
        script = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
        styles = (ROOT / "static" / "styles.css").read_text(encoding="utf-8")

        self.assertIn("normalizedVixThresholds(vix.thresholds)", script)
        self.assertIn("PulseEdge 기준 · 공식 등급이 아닌 시장 해석용 구간", script)
        self.assertIn("(index + bandProgress) * 25", script)
        self.assertIn("grid-template-columns: repeat(4, minmax(0, 1fr));", styles)


if __name__ == "__main__":
    unittest.main()
