"""Fixed apo-residue-centroid localization proxy; target-free candidate clustering."""
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import maximum_bipartite_matching

PROTOCOL={"name":"apo-residue-centroid-v1","residue_budget_fraction":.10,
          "candidate_connection_angstrom":8.,"target_annotation_jaccard_merge":.5,
          "center_distance_angstrom":4.,"top_k":[1,3],
          "candidate_center":"score-weighted centroid of top10%-residue spatial components",
          "candidate_rank":"mean residue score, descending; original residue index tie break",
          "target_center":"unweighted centroid of merged official annotated apo residues",
          "matching":"maximum cardinality one-to-one candidate/target assignment within4A",
          "limitation":"residue-centroid proxy, NOT ligand-center DCC or exact published protocol"}


def components(n,edges):
    parent=list(range(n))
    def find(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    for i,j in edges:
        a,b=find(i),find(j)
        if a!=b:parent[max(a,b)]=min(a,b)
    groups={}
    for i in range(n):groups.setdefault(find(i),[]).append(i)
    return list(groups.values())


def candidates(coords,scores,valid):
    """No pocket labels or paired structure may enter this function."""
    coords=np.asarray(coords,dtype=np.float64);scores=np.asarray(scores,dtype=np.float64)
    ids=np.flatnonzero(valid & np.isfinite(scores))
    if not len(ids):return []
    budget=max(1,int(np.ceil(len(ids)*PROTOCOL["residue_budget_fraction"])))
    chosen=ids[np.lexsort((ids,-scores[ids]))[:budget]]
    groups=components(len(chosen),cKDTree(coords[chosen]).query_pairs(PROTOCOL["candidate_connection_angstrom"]))
    result=[]
    for group in groups:
        nodes=chosen[group]
        weights=np.maximum(scores[nodes],1e-12)
        result.append({"center":np.average(coords[nodes],axis=0,weights=weights).tolist(),
                       "score":float(scores[nodes].mean()),"indices":sorted(map(int,nodes))})
    return sorted(result,key=lambda x:(-x["score"],x["indices"][0]))


def target_centers(coords,residue_ids,annotations,valid):
    lookup={str(r):i for i,r in enumerate(residue_ids) if valid[i]}
    sets={tuple(sorted({lookup[r] for r in a if r in lookup})) for a in annotations}
    sets=[set(s) for s in sorted(sets) if s]
    links=[]
    for i,a in enumerate(sets):
        for j,b in enumerate(sets[:i]):
            if len(a&b)/len(a|b)>=PROTOCOL["target_annotation_jaccard_merge"]:links.append((i,j))
    result=[]
    for group in components(len(sets),links):
        nodes=sorted(set().union(*(sets[i] for i in group)))
        result.append({"center":np.asarray(coords,dtype=np.float64)[nodes].mean(0).tolist(),"indices":nodes})
    return result


def matched_count(predicted,targets,k):
    if not predicted or not targets:return 0
    p=np.array([x["center"] for x in predicted[:k]],float)
    t=np.array([x["center"] for x in targets],float)
    within=np.linalg.norm(p[:,None]-t[None,:],axis=-1)<=PROTOCOL["center_distance_angstrom"]
    assignment=maximum_bipartite_matching(csr_matrix(within.astype(np.int8)),perm_type="column")
    return int((assignment>=0).sum())
