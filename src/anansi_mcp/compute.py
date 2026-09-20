"""Deterministic series math, done in the tool rather than the model."""

from __future__ import annotations

from typing import Any

Observation = dict[str, Any]  # {"date": "YYYY-MM-DD", "value": float, "is_forecast": bool}


def _year(observation: Observation) -> int:
    return int(str(observation["date"])[:4])


def _points(observations: list[Observation]) -> list[tuple[str, float]]:
    return [(o["date"], o["value"]) for o in observations if o.get("value") is not None]


def growth(observations: list[Observation], lag: int = 1) -> list[dict[str, Any]]:
    points = _points(observations)
    out = []
    for i in range(lag, len(points)):
        prev, cur = points[i - lag][1], points[i][1]
        if prev == 0:
            continue
        out.append({"date": points[i][0], "value": round((cur / prev - 1) * 100, 4)})
    return out


def cagr(observations: list[Observation]) -> dict[str, Any] | None:
    points = _points(observations)
    if len(points) < 2:
        return None
    (d0, v0), (d1, v1) = points[0], points[-1]
    years = _year({"date": d1}) - _year({"date": d0})
    if years <= 0 or v0 <= 0 or v1 < 0:
        return None
    return {
        "from": d0,
        "to": d1,
        "years": years,
        "cagr_pct": round(((v1 / v0) ** (1 / years) - 1) * 100, 4),
    }


def align(
    series: dict[str, list[Observation]],
) -> tuple[list[str], dict[str, dict[str, float]]]:
    """Align several series on their common dates."""
    by_date: dict[str, dict[str, float]] = {}
    for code, observations in series.items():
        for observation in observations:
            if observation.get("value") is None:
                continue
            by_date.setdefault(observation["date"], {})[code] = observation["value"]
    codes = list(series.keys())
    common = {d: v for d, v in by_date.items() if all(c in v for c in codes)}
    return sorted(common), common


def rebase(observations: list[Observation], base: float = 100.0) -> list[dict[str, Any]]:
    points = _points(observations)
    if not points or points[0][1] == 0:
        return []
    anchor = points[0][1]
    return [{"date": d, "value": round(v / anchor * base, 4)} for d, v in points]


def spread(a: list[Observation], b: list[Observation]) -> list[dict[str, Any]]:
    dates, common = align({"a": a, "b": b})
    return [{"date": d, "value": round(common[d]["a"] - common[d]["b"], 4)} for d in dates]


def correlation(a: list[Observation], b: list[Observation]) -> dict[str, Any] | None:
    dates, common = align({"a": a, "b": b})
    if len(dates) < 3:
        return None
    xs = [common[d]["a"] for d in dates]
    ys = [common[d]["b"] for d in dates]
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx == 0 or vy == 0:
        return None
    return {
        "observations": n,
        "from": dates[0],
        "to": dates[-1],
        "correlation": round(cov / (vx**0.5 * vy**0.5), 4),
    }


def moving_average(
    observations: list[Observation], window: int
) -> list[dict[str, Any]]:
    points = _points(observations)
    out = []
    for i in range(window - 1, len(points)):
        chunk = [v for _, v in points[i - window + 1 : i + 1]]
        out.append({"date": points[i][0], "value": round(sum(chunk) / window, 4)})
    return out


def zscore(observations: list[Observation]) -> list[dict[str, Any]]:
    points = _points(observations)
    if len(points) < 2:
        return []
    values = [v for _, v in points]
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    std = variance**0.5
    if std == 0:
        return []
    return [
        {"date": d, "value": round((v - mean) / std, 4)} for (d, v) in points
    ]
