# Adaptations to the vendored TNP-D source

Source: https://github.com/tung-nd/TNP-pytorch (MIT, Copyright 2022 Tung Nguyen; see LICENSE.md).
Fetched 2026-09-11: regression/models/{tnp,tnpd,modules,attention}.py.
Used as estimator E11 of OSF amendment 26hp8, registered as adapted from this implementation.

Only three changes, none of which alters the model:

1. `attrdict` replaced by `_attrdict.AttrDict`, a ten-line dict with attribute access. The
   upstream package does not import on Python 3.10+ and TNP-D uses only attribute get and set.
2. Hard-coded `device='cuda'` in `TNP.create_mask` and `TNPD.predict` replaced by the device of
   the input tensors. Upstream cannot run on CPU as written; on a GPU the behaviour is identical.
3. Package imports `from models.X` rewritten as relative imports within this folder.

Architecture, masking, likelihood and loss are exactly as upstream.

## Hyperparameters used for E11

The authors' own TNP-D defaults, from `regression/configs/gp/tnpd.yaml` in the same repository,
fetched 2026-09-11:

    d_model: 64
    emb_depth: 4
    dim_feedforward: 128
    nhead: 4
    dropout: 0.0
    num_layers: 6

Unchanged for E11 except the input dimension, which is set by the problem: `dim_x = 9` (x and y
in km plus the seven registered covariates) against the upstream 1-D Gaussian-process task, and
`dim_y = 1`. `bound_std=True` (std = 0.05 + 0.95 * softplus), the upstream option for numerically
stable training.
