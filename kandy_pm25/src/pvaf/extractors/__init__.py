"""PVAF per-block extractors.

Each module exposes one function `extract(city_entry, cf, **opts) -> None`
that mutates `cf` in place to fill its block's fields. Errors append to
`cf.notes` and leave the corresponding fields as None — extraction failures
in one block do not kill the others.
"""
