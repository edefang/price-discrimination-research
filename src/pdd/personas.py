"""Personas: constructed consumer profiles (study design, section 2).

A persona is a point on the factor grid. Every factor has a control level, and the
control persona sits at all of them. The v0 prototype's three personas each varied
four attributes at once, so no observed difference was attributable to any one of
them; here a persona carries its factor levels explicitly, and the design helpers
build sets in which each factor moves on its own.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product as _cartesian

FACTORS = ("geo", "dev", "loc", "tz", "hist")

CONTROL_LEVELS: dict[str, str] = {
    "geo": "us-east",
    "dev": "desktop",
    "loc": "en-US",
    "tz": "America/New_York",
    "hist": "cold",
}

# Provisional levels from the design document. The pilot or the simulator may revise
# these; the instrument does not care what the levels are, only that each is declared.
DEFAULT_LEVELS: dict[str, list[str]] = {
    "geo": ["us-east", "us-west", "eu-west"],
    "dev": ["desktop", "mobile"],
    "loc": ["en-US", "de-DE"],
    "tz": ["America/New_York", "Europe/Berlin"],
    "hist": ["cold", "primed"],
}

_DEVICE_PROFILES: dict[str, dict] = {
    "desktop": {
        "user_agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        ),
        "viewport": {"width": 1280, "height": 800},
        "is_mobile": False,
        "has_touch": False,
    },
    "mobile": {
        "user_agent": (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 "
            "(KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1"
        ),
        "viewport": {"width": 390, "height": 844},
        "is_mobile": True,
        "has_touch": True,
    },
}

# Coordinates handed to the browser's geolocation API. They are not what a live
# retailer keys on — that is the request's IP — but they keep the browser-visible
# signals consistent with the persona's claimed region.
_GEO_COORDS: dict[str, dict[str, float]] = {
    "us-east": {"latitude": 40.7128, "longitude": -74.0060},
    "us-west": {"latitude": 34.0522, "longitude": -118.2437},
    "eu-west": {"latitude": 52.5200, "longitude": 13.4050},
}


@dataclass(frozen=True)
class Persona:
    persona_id: str
    geo: str
    dev: str
    loc: str
    tz: str
    hist: str
    is_control: bool = False

    def factors(self) -> dict[str, str]:
        return {f: getattr(self, f) for f in FACTORS}

    def context_options(self) -> dict:
        """Keyword arguments for `playwright.Browser.new_context`."""
        profile = _DEVICE_PROFILES[self.dev]
        return {
            "locale": self.loc,
            "timezone_id": self.tz,
            "geolocation": _GEO_COORDS[self.geo],
            "permissions": ["geolocation"],
            "user_agent": profile["user_agent"],
            "viewport": profile["viewport"],
            "is_mobile": profile["is_mobile"],
            "has_touch": profile["has_touch"],
            "extra_http_headers": self.http_headers(include_ua=False),
        }

    def http_headers(self, *, include_ua: bool = True) -> dict[str, str]:
        """Headers for a plain HTTP fetch.

        `X-Persona-Geo` exists for the mock storefront, which cannot see an IP address.
        A live target ignores it and keys on the proxy exit instead; sending it there
        is harmless and keeps one code path.
        """
        headers = {
            "Accept-Language": f"{self.loc},{self.loc.split('-')[0]};q=0.9",
            "X-Persona-Geo": self.geo,
        }
        if include_ua:
            headers["User-Agent"] = _DEVICE_PROFILES[self.dev]["user_agent"]
        return headers


def control_persona() -> Persona:
    return Persona(persona_id="control", is_control=True, **CONTROL_LEVELS)


def _persona_id(levels: dict[str, str]) -> str:
    moved = [f"{f}={v}" for f, v in levels.items() if v != CONTROL_LEVELS[f]]
    return "+".join(moved) if moved else "control"


def one_factor_at_a_time(levels: dict[str, list[str]] | None = None) -> list[Persona]:
    """Control plus one persona per non-control level of each factor.

    Identifies every main effect with the fewest personas. It cannot see interactions;
    that is by design and the mock storefront's `interaction` scenario exists to
    confirm the instrument reports *nothing* there rather than something spurious.
    """
    levels = levels or DEFAULT_LEVELS
    personas = [control_persona()]
    for factor in FACTORS:
        for level in levels.get(factor, [CONTROL_LEVELS[factor]]):
            if level == CONTROL_LEVELS[factor]:
                continue
            spec = dict(CONTROL_LEVELS, **{factor: level})
            personas.append(Persona(persona_id=_persona_id(spec), **spec))
    return personas


def full_factorial(levels: dict[str, list[str]] | None = None) -> list[Persona]:
    """Every combination. Grows fast; the design document explains why the main study
    uses a fraction of this rather than all of it."""
    levels = levels or DEFAULT_LEVELS
    personas = []
    for combo in _cartesian(*(levels[f] for f in FACTORS)):
        spec = dict(zip(FACTORS, combo))
        is_control = spec == CONTROL_LEVELS
        personas.append(
            Persona(
                persona_id="control" if is_control else _persona_id(spec),
                is_control=is_control,
                **spec,
            )
        )
    return personas
