"""Shared helpers used by all deterministic generators.

The generators intentionally use small parameter spaces and enumerate
combinations rather than calling into a stochastic generator — this makes
the matrix reproducible across runs and trivially parallelizable by
shard index.

Key primitives:

    param_grid(**axes)
        Cartesian-product of axes; yields dicts.

    GridBuilder
        Fluent builder that emits :class:`TestCase` objects from a source
        template function + tag template.

    interp_variants
        Pre-baked snippets that exercise interpreter/JIT tier transitions
        (loop with side effects, nested call loops, etc.).
"""

from __future__ import annotations

import itertools
from typing import Any, Callable, Iterable, Iterator

from ..harness import TagSet


def param_grid(**axes: Iterable[Any]) -> Iterator[dict[str, Any]]:
    """Yield every combination of ``axes`` as a dict."""
    keys = list(axes.keys())
    value_lists = [list(v) for v in axes.values()]
    for combo in itertools.product(*value_lists):
        yield dict(zip(keys, combo))


class GridBuilder:
    """Fluent: take a template fn, iterate params, yield TestCases.

    Usage::

        gb = GridBuilder(category="numeric", tags_factory=lambda p: TagSet.make("numeric"))
        for case in gb.expand(grid, lambda p: (source_for(p), inputs_for(p))):
            yield case
    """

    def __init__(
        self,
        *,
        category: str,
        tags_factory: Callable[[dict[str, Any]], TagSet] | None = None,
        id_prefix: str = "",
    ) -> None:
        self.category = category
        self.tags_factory = tags_factory or (lambda _p: TagSet.make(category))
        self.id_prefix = id_prefix or category

    def expand(
        self,
        grid: Iterable[dict[str, Any]],
        source_fn: Callable[[dict[str, Any]], tuple[str, tuple[tuple[str, Any], ...], TagSet]],
    ) -> Iterator:
        # Lazy import to avoid a circular dependency
        from ..harness import TestCase

        for i, params in enumerate(grid):
            source, inputs, tags = source_fn(params)
            yield TestCase(
                source=source,
                inputs=inputs,
                tags=tags if tags is not None else self.tags_factory(params),
                id=f"{self.id_prefix}-{i:07d}",
                category=self.category,
            )

    def expand_simple(
        self,
        grid: Iterable[dict[str, Any]],
        source_fn: Callable[[dict[str, Any]], str],
        *,
        inputs_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
        tags_fn: Callable[[dict[str, Any]], TagSet] | None = None,
    ) -> Iterator:
        from ..harness import TestCase

        for i, params in enumerate(grid):
            source = source_fn(params)
            inputs = dict(inputs_fn(params)) if inputs_fn else {}
            tags = tags_fn(params) if tags_fn else self.tags_factory(params)
            yield TestCase(
                source=source,
                inputs=tuple(sorted(inputs.items())),
                tags=tags,
                id=f"{self.id_prefix}-{i:07d}",
                category=self.category,
            )


def shard(stream: Iterable, *, shard: int, n_shards: int) -> Iterator:
    """Yield every ``n_shards``-th item starting at ``shard`` (0-indexed)."""
    for i, item in enumerate(stream):
        if i % n_shards == shard:
            yield item


def take(stream: Iterable, n: int) -> list:
    out = []
    for i, item in enumerate(stream):
        if i >= n:
            break
        out.append(item)
    return out


def cap(generator: Iterator, n: int) -> Iterator:
    """Stop a generator after ``n`` items (so we can hit exact category counts)."""
    for i, item in enumerate(generator):
        if i >= n:
            return
        yield item
