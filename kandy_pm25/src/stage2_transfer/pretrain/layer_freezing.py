"""
layer_freezing.py — Utility to freeze/unfreeze PINN layers for transfer learning.

Two-stage transfer strategy (§2.8 of RESEARCH_PROJECT_DESIGN.md):
  A. FROZEN  : After pre-training on Medellín, freeze early (physics) layers.
               Fine-tune only the Kandy-specific head (last 1–2 layers).
               Prevents catastrophic forgetting of learned PDE structure.

  B. THAWED  : If fine-tuned model plateaus, progressively unfreeze layers
               from the output side in — progressive unfreezing (Howard & Ruder 2018)

Decision rule (from RESEARCH_PROJECT_DESIGN.md §2.8):
  - If K magnitude differs > 5× from Medellín: unfreeze all layers, train from transfer-init
  - Otherwise: freeze backbone, fine-tune head only

Usage:
    from layer_freezing import freeze_backbone, unfreeze_all, progressive_unfreeze
    model = freeze_backbone(model, n_frozen_layers=4)
"""

import logging
from typing import List, Optional

log = logging.getLogger("layer_freezing")


def freeze_backbone(model, n_frozen_layers: int = 4):
    """
    Freeze the first n_frozen_layers of the PINN for transfer fine-tuning.

    The backbone layers encode the advection-diffusion PDE structure learned
    from Medellín. Freezing them preserves this physics knowledge.

    Args:
        model          : FourierPINN model
        n_frozen_layers: Number of layers from the input side to freeze

    Returns:
        model with frozen backbone parameters
    """
    try:
        import torch.nn as nn
    except ImportError:
        raise ImportError("PyTorch required")

    trainable_before = sum(p.numel() for p in model.parameters() if p.requires_grad)

    if hasattr(model, "net") and hasattr(model.net, "layers"):
        layers = model.net.layers
    else:
        # Fallback: get all named children in order
        layers = list(model.children())

    for i, layer in enumerate(layers[:n_frozen_layers]):
        for param in layer.parameters():
            param.requires_grad = False
        log.info(f"  Frozen layer {i}: {layer.__class__.__name__}")

    trainable_after = sum(p.numel() for p in model.parameters() if p.requires_grad)
    pct_frozen = 100 * (1 - trainable_after / trainable_before) if trainable_before > 0 else 0
    log.info(f"Backbone frozen: {trainable_before} → {trainable_after} trainable params ({pct_frozen:.0f}% frozen)")
    return model


def unfreeze_all(model):
    """Unfreeze all model parameters (for full fine-tuning phase)."""
    for param in model.parameters():
        param.requires_grad = True
    n_trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    log.info(f"All parameters unfrozen: {n_trainable} trainable params")
    return model


def progressive_unfreeze(model, n_unfrozen_layers: int):
    """
    Progressively unfreeze layers from the output side inward.

    Howard & Ruder (2018) progressive unfreezing: unfreeze one layer group
    at a time, starting from the last layer and working toward the first.

    Usage:
        for n in [1, 2, 4]:  # gradually unfreeze more layers
            model = progressive_unfreeze(model, n_unfrozen_layers=n)
            optimizer = Adam(model.parameters(), lr=lr * 0.5**n)
            train_one_epoch(model, ...)

    Args:
        model              : FourierPINN model
        n_unfrozen_layers  : How many layers from the output side to unfreeze

    Returns:
        model with progressively unfrozen layers
    """
    if hasattr(model, "net") and hasattr(model.net, "layers"):
        layers = list(model.net.layers)
    else:
        layers = list(model.children())

    # First freeze all
    for layer in layers:
        for param in layer.parameters():
            param.requires_grad = False

    # Then unfreeze the last n_unfrozen_layers
    for layer in layers[-n_unfrozen_layers:]:
        for param in layer.parameters():
            param.requires_grad = True
        log.info(f"  Unfrozen layer: {layer.__class__.__name__}")

    n_trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    log.info(f"Progressive unfreeze (n={n_unfrozen_layers}): {n_trainable} trainable params")
    return model


def get_layer_lr_groups(model, base_lr: float, decay_factor: float = 0.5) -> List[dict]:
    """
    Build per-layer learning rate groups for differential LR fine-tuning.

    Earlier (physics) layers get lower LR, later (domain) layers get higher LR.
    This preserves the learned physics while allowing the head to adapt fast.

    Args:
        model        : FourierPINN model
        base_lr      : Learning rate for the last layer group
        decay_factor : LR multiplier per layer from output → input (< 1)

    Returns:
        List of dicts suitable for torch.optim.Adam(param_groups=...)
    """
    if hasattr(model, "net") and hasattr(model.net, "layers"):
        layers = list(model.net.layers)
    else:
        layers = list(model.children())

    n_layers = len(layers)
    param_groups = []
    for i, layer in enumerate(reversed(layers)):
        lr_i = base_lr * (decay_factor ** i)
        param_groups.append({
            "params": layer.parameters(),
            "lr":     lr_i,
            "name":   f"layer_{n_layers - 1 - i}",
        })
        log.debug(f"  layer_{n_layers - 1 - i}: lr={lr_i:.2e}")

    log.info(f"Differential LR groups: {n_layers} groups, {base_lr:.2e} → {base_lr * decay_factor**(n_layers-1):.2e}")
    return param_groups
