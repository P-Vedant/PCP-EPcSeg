import tempfile
import unittest
from dataclasses import fields
from pathlib import Path
import numpy as np
import torch
from pcp.data import ApoInput, apo_features, contact_targets
from pcp.model import RegionalPocket, loss_fn
from pcp.train import tensors, save_checkpoint, seed_all
from pcp.transfer import import_bundle
import zipfile
import json


def example():
    rng = np.random.default_rng(5)
    coords = np.cumsum(rng.normal(size=(24,3)), axis=0).astype(np.float32)*3
    return [{"id":f"A_{i+1}","aa":"A","atoms":{"CA":c,"CB":c+np.array([0,1,0],np.float32)}} for i,c in enumerate(coords)]


class CoreTests(unittest.TestCase):
    def setUp(self):
        torch.set_num_threads(2); seed_all(7)

    def test_apo_isolation_and_rigid_invariance(self):
        self.assertEqual({f.name for f in fields(ApoInput)}, {"x","coords","edges","edge_attr","residue_ids","sequence"})
        residues = example(); apo = apo_features(residues)
        q,_ = np.linalg.qr(np.random.default_rng(4).normal(size=(3,3)))
        q[:,0] *= np.linalg.det(q)
        moved = [{**r,"atoms":{k:(v@q+20).astype(np.float32) for k,v in r["atoms"].items()}} for r in residues]
        b = apo_features(moved)
        np.testing.assert_array_equal(apo.edges,b.edges)
        np.testing.assert_allclose(apo.x,b.x,atol=1e-5)
        model = RegionalPocket().eval()
        def pred(a):
            z={"x":a.x,"edges":a.edges,"edge_attr":a.edge_attr}
            return model(tensors(z,"cpu",0,1)[0])
        with torch.no_grad():
            x,y = pred(apo),pred(b)
        for key in x: torch.testing.assert_close(x[key],y[key],atol=2e-5,rtol=2e-5)

    def test_finite_overfit_and_checkpoint(self):
        a=apo_features(example()); n=len(a.x)
        z={"x":a.x,"edges":a.edges,"edge_attr":a.edge_attr,"y":(np.arange(n)%3==0).astype(np.float32),
           "contact_y":np.zeros((a.edges.shape[1],2),np.float32),"contact_mask":np.ones(a.edges.shape[1],bool)}
        inputs,target=tensors(z,"cpu",0,1)
        model=RegionalPocket(); opt=torch.optim.AdamW(model.parameters(),lr=.001)
        weights=(torch.tensor(1.),torch.ones(2))
        losses=[]
        for _ in range(30):
            opt.zero_grad(); loss=loss_fn(model(inputs),target,inputs["edges"],weights,model.mode)
            loss.backward()
            self.assertTrue(all(torch.isfinite(p.grad).all() for p in model.parameters() if p.grad is not None))
            opt.step(); losses.append(float(loss.detach()))
        self.assertLess(losses[-1],losses[0]*.65)
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"state.pt"; save_checkpoint(path,{"model":model.state_dict(),"optimizer":opt.state_dict()})
            restored=RegionalPocket(); state=torch.load(path,weights_only=True); restored.load_state_dict(state["model"])
            torch.testing.assert_close(model(inputs)["pocket_logits"],restored(inputs)["pocket_logits"])

    def test_contact_labels_and_missing_energy(self):
        r=example(); a=apo_features(r); labels,mask,audit=contact_targets(r,r,a)
        self.assertEqual(labels.sum(),0)
        self.assertGreater(mask.sum(),0)
        inputs,_=tensors({"x":a.x,"edges":a.edges,"edge_attr":a.edge_attr},"cpu",0,1)
        model=RegionalPocket(use_energy=True)
        first=model(inputs)["pocket_logits"]
        inputs["energy"]=torch.randn_like(inputs["energy"])*100
        torch.testing.assert_close(first,model(inputs)["pocket_logits"])

    def test_transfer_rejects_path_escape_before_writing(self):
        with tempfile.TemporaryDirectory() as d:
            archive=Path(d)/"bad.zip"
            with zipfile.ZipFile(archive,"w") as z:
                z.writestr("../escape",b"x"); z.writestr("SHA256.json",json.dumps({"../escape":"wrong"}))
            with self.assertRaises(ValueError): import_bundle(archive,Path(d)/"dest")
            self.assertFalse((Path(d)/"dest").exists())


if __name__=="__main__": unittest.main()
