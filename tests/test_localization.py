import unittest
import numpy as np
from pcp.localization import candidates,target_centers,matched_count


class LocalizationTests(unittest.TestCase):
    def test_matching_is_one_to_one_and_not_greedy(self):
        p=[{"center":[0,0,0]},{"center":[7,0,0]}]
        t=[{"center":[3,0,0]},{"center":[-3,0,0]}]
        self.assertEqual(matched_count(p,t,1),1)
        self.assertEqual(matched_count(p,t,2),2)
        self.assertEqual(matched_count(p[:1],t,3),1)
    def test_rigid_invariant_candidates_and_target_merge(self):
        rng=np.random.default_rng(7);x=rng.normal(size=(40,3))*5;p=rng.uniform(.1,.9,40)
        ids=np.array([f"A_{i}" for i in range(40)]);valid=np.ones(40,bool);valid[0]=False
        labels=[list(ids[1:5]),list(ids[2:6]),list(ids[30:34])]
        truth=target_centers(x,ids,labels,valid);self.assertEqual(len(truth),2)
        q,_=np.linalg.qr(rng.normal(size=(3,3)));moved=x@q+100
        a,b=candidates(x,p,valid),candidates(moved,p,valid)
        self.assertEqual([i['indices'] for i in a],[i['indices'] for i in b])
        for first,second in zip(a,b):np.testing.assert_allclose(np.array(first['center'])@q+100,second['center'],atol=1e-10)
        self.assertEqual(matched_count(a,truth,3),matched_count(b,target_centers(moved,ids,labels,valid),3))


if __name__=="__main__":unittest.main()
