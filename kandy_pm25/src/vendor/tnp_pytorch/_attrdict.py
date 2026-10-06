"""Minimal stand-in for the unmaintained `attrdict` package, which does not import on
Python 3.10+ (it relies on collections.Mapping). Upstream TNP-D uses only attribute-style
get and set on a dict, which is all this provides."""


class AttrDict(dict):
    def __getattr__(self, k):
        try:
            return self[k]
        except KeyError as e:
            raise AttributeError(k) from e

    def __setattr__(self, k, v):
        self[k] = v
