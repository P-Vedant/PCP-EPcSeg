"""Sparse invariant message passing with region-factored contact feedback."""
import torch
from torch import nn
import torch.nn.functional as F


def mlp(inp, out, hidden=384):
    return nn.Sequential(nn.Linear(inp, hidden), nn.SiLU(), nn.Linear(hidden, out))


class Layer(nn.Module):
    def __init__(self, width):
        super().__init__()
        self.message = mlp(width * 2 + 4, width)
        self.update = mlp(width * 2, width)
        self.norm = nn.LayerNorm(width)

    def forward(self, h, edges, edge_attr):
        i, j = edges
        m = self.message(torch.cat([h[i] + h[j], (h[i] - h[j]).abs(), edge_attr], -1))
        agg = torch.zeros_like(h).index_add(0, i, m).index_add(0, j, m)
        degree = torch.zeros(len(h), device=h.device).index_add(0, i, torch.ones_like(i, dtype=h.dtype)).index_add(0, j, torch.ones_like(j, dtype=h.dtype))
        return self.norm(h + self.update(torch.cat([h, agg / degree.clamp_min(1)[:, None]], -1)))


class RegionalPocket(nn.Module):
    def __init__(self, input_dim=31, width=96, layers=4, regions=12, mode="regional", use_if=False, use_energy=False, energy_mode="bounded"):
        super().__init__()
        self.config = dict(input_dim=input_dim, width=width, layers=layers, regions=regions,
                           mode=mode, use_if=use_if, use_energy=use_energy, energy_mode=energy_mode)
        self.mode, self.use_if, self.use_energy, self.energy_mode = mode, use_if, use_energy, energy_mode
        self.encode = mlp(input_dim, width)
        self.if_adapter = mlp(24, width, 96)
        self.energy_adapter = mlp(4, width, 96)
        self.energy_gate = nn.Parameter(torch.tensor(-2.0))
        self.layers = nn.ModuleList([Layer(width) for _ in range(layers)])
        self.assignment = nn.Linear(width, regions)
        self.region_pair = mlp(width * 2, 2, 128)
        self.contact = mlp(width * 2 + 4, 2, 128)
        self.pocket = mlp(width + 2, 1, 128)

    def forward(self, apo):
        # An explicit allowlist prevents accidental target access.
        h = self.encode(apo["x"])
        if self.use_if:
            h = h + self.if_adapter(torch.cat([apo["if_features"], apo["if_mask"]], -1)) * apo["if_mask"]
        if self.use_energy:
            raw = self.energy_adapter(torch.cat([apo["energy"], apo["energy_mask"]], -1))
            energy = raw if self.energy_mode == "concat" else self.energy_gate.sigmoid() * raw.tanh()
            h = h + energy * apo["energy_mask"]
        edges, attrs = apo["edges"], apo["edge_attr"]
        for layer in self.layers:
            h = layer(h, edges, attrs)
        i, j = edges
        s = self.assignment(h).softmax(-1)
        local = self.contact(torch.cat([h[i]+h[j], (h[i]-h[j]).abs(), attrs], -1))
        logits = local
        if self.mode == "regional":
            pooled = s.T @ h / s.sum(0).clamp_min(1e-6)[:, None]
            a, b = pooled[:, None, :], pooled[None, :, :]
            region_logits = self.region_pair(torch.cat([a+b, (a-b).abs()], -1))
            logits = local + torch.einsum("ek,klt,el->et", s[i], region_logits, s[j])
        feedback = torch.zeros(len(h), 2, device=h.device)
        if self.mode == "regional":
            p = logits.sigmoid()
            # Sequence neighbors have no contact-change supervision; omit from feedback.
            p = p * (attrs[:, 3:4] == 0)
            feedback = feedback.index_add(0, i, p).index_add(0, j, p)
            count = torch.zeros(len(h), device=h.device).index_add(0, i, torch.ones_like(i, dtype=h.dtype)).index_add(0, j, torch.ones_like(j, dtype=h.dtype))
            feedback = feedback / count.clamp_min(1)[:, None]
        pocket = self.pocket(torch.cat([h, feedback], -1)).squeeze(-1)
        return {"pocket_logits": pocket, "contact_logits": logits, "regions": s}


def loss_fn(pred, targets, edges, weights, mode):
    pocket = F.binary_cross_entropy_with_logits(pred["pocket_logits"].float(), targets["y"], pos_weight=weights[0])
    contact = pocket.new_tensor(0.)
    mask = targets["contact_mask"]
    if mode != "pocket" and mask.any():
        contact = F.binary_cross_entropy_with_logits(pred["contact_logits"][mask].float(), targets["contact_y"][mask], pos_weight=weights[1])
    region = pocket.new_tensor(0.)
    if mode == "regional":
        s = pred["regions"].float()
        i, j = edges
        coherence = (s[i] - s[j]).square().sum(-1).mean()
        mass = s.mean(0).clamp_min(1e-8)
        balance = (mass * (mass * s.shape[1]).log()).sum()
        entropy = -(s * s.clamp_min(1e-8).log()).sum(-1).mean()
        region = 0.01 * coherence + 0.01 * balance + 0.001 * entropy
    return pocket + 0.25 * contact + region
