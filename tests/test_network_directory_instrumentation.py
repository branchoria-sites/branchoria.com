"""Falsifier + bounded census arm for hub satellite event wiring.

The hub (branchoria.com) is the estate's entire discovery funnel into member
satellites: every satellite visit from the hub passes through a
``data-network-site-card`` anchor in the home page directory. This census
verifies that the hub's own ``network-directory.js`` asset wires typed GA4
``satellite_click`` events onto exactly that anchor population, and it
proves the check has teeth by mutating the wiring and demanding a red.
"""

import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parent.parent
HUB_HTML = REPO_ROOT / "index.html"
HUB_JS = REPO_ROOT / "assets" / "network-directory.js"

ESTATE_HOST_SUFFIX = ".branchoria.com"

PAYLOAD_KEYS = (
    "satellite_id",
    "satellite_host",
    "network",
    "card_position",
    "card_total",
    "link_kind",
    "link_text",
    "page_path",
)


class _CardAnchorParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.card_depth = 0
        self.anchor_depth = 0
        self.anchor_href = None
        self.anchor_text = []
        self.cards = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "article" and "data-network-site-card" in attrs:
            self.card_depth = 1
            self.cards.append([])
            return
        if not self.card_depth:
            return
        if tag == "article":
            self.card_depth += 1
        elif tag == "a":
            self.anchor_depth += 1
            self.anchor_href = attrs.get("href")
            self.anchor_text = []

    def handle_endtag(self, tag):
        if tag == "a" and self.anchor_depth:
            self.anchor_depth -= 1
            text = " ".join("".join(self.anchor_text).split())
            if self.cards:
                self.cards[-1].append({"href": self.anchor_href or "", "text": text})
            self.anchor_href = None
            self.anchor_text = []
        elif tag == "article" and self.card_depth:
            self.card_depth -= 1

    def handle_data(self, data):
        if self.anchor_depth:
            self.anchor_text.append(data)


def parse_hub_directory(html_text):
    parser = _CardAnchorParser()
    parser.feed(html_text)
    cards = []
    for anchors in parser.cards:
        satellite_anchors = [
            a for a in anchors
            if a["href"].startswith("http") and urlparse(a["href"]).hostname
        ]
        cards.append(satellite_anchors)
    hosts = sorted({urlparse(a["href"]).hostname for card in cards for a in card})
    return {
        "card_count": len(cards),
        "satellite_link_count": sum(len(card) for card in cards),
        "satellite_hosts": hosts,
        "cards": cards,
    }


def parse_wiring(js_text):
    return {
        "binds_card_anchors": 'card.querySelectorAll("a[href]")' in js_text,
        "click_listener": 'addEventListener("click"' in js_text,
        "gtag_satellite_click": 'gtag("event", "satellite_click"' in js_text,
        "gtag_guard": 'typeof window.gtag !== "function"' in js_text,
        "idempotent_binding": "satelliteClickBound" in js_text,
        "payload_keys": tuple(k for k in PAYLOAD_KEYS if k in js_text),
        "transport_beacon": "transport_type: \"beacon\"" in js_text,
    }


def census_hub_satellite_wiring(html_text, js_text):
    directory = parse_hub_directory(html_text)
    wiring = parse_wiring(js_text)
    missing_keys = [k for k in PAYLOAD_KEYS if k not in wiring["payload_keys"]]
    reasons = []
    if directory["card_count"] == 0:
        reasons.append("directory_has_no_satellite_cards")
    if directory["satellite_link_count"] == 0:
        reasons.append("directory_has_no_satellite_links")
    non_estate = [h for h in directory["satellite_hosts"]
                  if not h.endswith(ESTATE_HOST_SUFFIX)]
    if non_estate:
        reasons.append("non_estate_satellite_hosts:" + ",".join(non_estate))
    for field, present in wiring.items():
        if field == "payload_keys":
            continue
        if not present:
            reasons.append("wiring_missing:" + field)
    if missing_keys:
        reasons.append("wiring_missing_payload_keys:" + ",".join(missing_keys))
    verdict = "instrumented" if not reasons else "blindspot"
    return {
        "verdict": verdict,
        "reasons": reasons,
        "directory": {
            "card_count": directory["card_count"],
            "satellite_link_count": directory["satellite_link_count"],
            "satellite_hosts": directory["satellite_hosts"],
        },
        "wiring": {k: (list(v) if isinstance(v, tuple) else v) for k, v in wiring.items()},
    }


class HubSatelliteWiringCensusTests(unittest.TestCase):
    def setUp(self):
        self.html_text = HUB_HTML.read_text(encoding="utf-8")
        self.js_text = HUB_JS.read_text(encoding="utf-8")
        self.report = census_hub_satellite_wiring(self.html_text, self.js_text)

    def test_hub_directory_is_instrumented(self):
        self.assertEqual(
            self.report["verdict"], "instrumented",
            "hub satellite wiring census: " + "; ".join(self.report["reasons"]),
        )

    def test_census_is_bounded_to_a_nonempty_estate_funnel(self):
        directory = self.report["directory"]
        self.assertGreaterEqual(directory["card_count"], 1)
        self.assertGreaterEqual(directory["satellite_link_count"], directory["card_count"])
        self.assertGreaterEqual(len(directory["satellite_hosts"]), 1)

    def test_every_card_anchor_is_an_estate_satellite(self):
        cards = parse_hub_directory(self.html_text)["cards"]
        for index, card in enumerate(cards, start=1):
            self.assertGreaterEqual(
                len(card), 1,
                "hub directory card %d has no satellite anchor" % index)
            for anchor in card:
                self.assertTrue(
                    urlparse(anchor["href"]).hostname.endswith(ESTATE_HOST_SUFFIX),
                    "card %d anchor %s leaves the estate" % (index, anchor["href"]),
                )

    def test_wiring_covers_the_full_payload_contract(self):
        wiring = self.report["wiring"]
        self.assertEqual(sorted(wiring["payload_keys"]), sorted(PAYLOAD_KEYS))
        self.assertTrue(wiring["transport_beacon"])

    def test_falsifier_removing_the_gtag_emission_redds_the_census(self):
        mutated = self.js_text.replace(
            'window.gtag("event", "satellite_click"', "window.__removed(")
        self.assertNotEqual(mutated, self.js_text, "falsifier mutation did not apply")
        report = census_hub_satellite_wiring(self.html_text, mutated)
        self.assertEqual(report["verdict"], "blindspot")
        self.assertIn("wiring_missing:gtag_satellite_click", report["reasons"])

    def test_falsifier_removing_the_click_binding_redds_the_census(self):
        mutated = self.js_text.replace(
            'addEventListener("click"', 'addEventListener("__none"')
        self.assertNotEqual(mutated, self.js_text, "falsifier mutation did not apply")
        report = census_hub_satellite_wiring(self.html_text, mutated)
        self.assertEqual(report["verdict"], "blindspot")
        self.assertIn("wiring_missing:click_listener", report["reasons"])

    def test_falsifier_empty_directory_redds_the_census(self):
        report = census_hub_satellite_wiring(
            "<!doctype html><html><body><p>no directory</p></body></html>",
            self.js_text)
        self.assertEqual(report["verdict"], "blindspot")
        self.assertIn("directory_has_no_satellite_cards", report["reasons"])

    def test_relabeling_anchor_classes_does_not_red_the_census(self):
        # The wiring binds anchors by href presence inside cards, not by
        # class, so relabeling the explore-link class cannot silently
        # unwire the funnel; the census must stay green.
        mutated = self.html_text.replace(
            '<a class="network-site-link"',
            '<a data-census-relabel="1" class="explore-link"')
        self.assertNotEqual(mutated, self.html_text, "relabel mutation did not apply")
        report = census_hub_satellite_wiring(mutated, self.js_text)
        self.assertEqual(report["verdict"], "instrumented")


if __name__ == "__main__":
    unittest.main()
