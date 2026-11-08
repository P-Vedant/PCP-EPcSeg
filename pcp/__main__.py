import argparse
import json
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="PCP-EPcSeg research CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("hardware"); p.add_argument("--out", default="outputs/hardware.json")
    p = sub.add_parser("prepare"); p.add_argument("--root", default="data"); p.add_argument("--limit", type=int, default=24)
    p = sub.add_parser("audit"); p.add_argument("--index", required=True)
    p = sub.add_parser("baseline"); p.add_argument("--index", required=True); p.add_argument("--run", required=True)
    p = sub.add_parser("train"); p.add_argument("--index", required=True); p.add_argument("--run", required=True); p.add_argument("--config", required=True); p.add_argument("--resume")
    p = sub.add_parser("profile"); p.add_argument("--index", required=True); p.add_argument("--out", default="outputs/profile.json")
    p = sub.add_parser("infer"); p.add_argument("--structure", required=True); p.add_argument("--chain", required=True); p.add_argument("--sequence", required=True); p.add_argument("--checkpoint", required=True); p.add_argument("--out", required=True); p.add_argument("--device", default="cpu")
    p = sub.add_parser("evaluate"); p.add_argument("--index", required=True); p.add_argument("--checkpoint", required=True); p.add_argument("--out", required=True); p.add_argument("--split", choices=["val", "test"], default="val")
    p = sub.add_parser("export"); p.add_argument("--out", required=True); p.add_argument("files", nargs="+")
    p = sub.add_parser("import"); p.add_argument("--archive", required=True); p.add_argument("--destination", required=True)
    args = parser.parse_args()
    from .io import atomic_json, hardware
    if args.command == "hardware":
        import torch
        hw = hardware()
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA unavailable")
        model = torch.nn.Sequential(torch.nn.Linear(64, 128), torch.nn.SiLU(), torch.nn.Linear(128, 1)).cuda()
        opt = torch.optim.AdamW(model.parameters())
        x = torch.randn(32, 64, device="cuda")
        for _ in range(3):
            opt.zero_grad(); loss = model(x).square().mean(); loss.backward()
            assert torch.isfinite(loss) and all(torch.isfinite(p.grad).all() for p in model.parameters())
            opt.step()
        torch.cuda.synchronize()
        hw["cuda_forward_backward_optimizer_passed"] = True
        atomic_json(args.out, hw); print(json.dumps(hw, indent=2))
    elif args.command == "prepare":
        from .data import prepare
        print(prepare(args.root, args.limit))
    elif args.command == "audit":
        from .audit import audit
        print(json.dumps(audit(args.index), indent=2))
    elif args.command == "baseline":
        from .train import baseline
        result = baseline(args.index, args.run)
        print(json.dumps({k:v["macro_ap"] for k,v in result.items()}))
    elif args.command == "train":
        from .train import train
        result = train(args.index, args.run, json.loads(Path(args.config).read_text()), args.resume)
        print(json.dumps({k:v for k,v in result.items() if k != "per_protein"}))
    elif args.command == "profile":
        from .ops import profile
        print(json.dumps(profile(args.index, args.out), indent=2))
    elif args.command == "infer":
        from .ops import infer
        infer(args.structure, args.chain, args.sequence, args.checkpoint, args.out, args.device)
    elif args.command == "evaluate":
        from .ops import evaluate_checkpoint
        evaluate_checkpoint(args.index, args.checkpoint, args.out, args.split)
    elif args.command in ("export", "import"):
        from .transfer import export_bundle, import_bundle
        print(export_bundle(args.files, args.out) if args.command=="export" else import_bundle(args.archive, args.destination))


if __name__ == "__main__":
    main()
