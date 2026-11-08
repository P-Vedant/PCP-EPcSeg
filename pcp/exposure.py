"""Full-polymer/alias/CATH audit. Never reads model scores or official-test labels."""
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from collections import defaultdict
from Bio import Align
from Bio.PDB.MMCIF2Dict import MMCIF2Dict
from .io import atomic_json,download,sha256,now

POLICY={"version":"exposure-v1","identity":.30,"longer_chain_coverage":.80,
        "cath_seqres_coverage":.80,"max_sequence_length":5000,
        "max_unknown_fraction":.05,"cath_level":"topology (C.A.T), conservative shared-domain exclusion",
        "alignment":"global; match2,mismatch-1,gap_open-5,gap_extend-.5; X never a match",
        "claim":"post-hoc development screening only, NOT a fresh independent test"}


def normalized_aliases(values):
    if isinstance(values,str):values=[values]
    return {v.strip().upper().split("-")[0] for v in (values or []) if isinstance(v,str)
            and v.strip().lower() not in ("","none","null","unknown","n/a","na","?",".")}


def polymer_metadata(cif,chain):
    sequences=[]
    for chains,seq in zip(cif.get("_entity_poly.pdbx_strand_id",[]),cif.get("_entity_poly.pdbx_seq_one_letter_code_can",[])):
        if chain in [c.strip() for c in chains.split(",")]:
            sequences.append(re.sub(r"\s+","",seq).upper())
    sequences=sorted(set(sequences))
    if len(sequences)!=1:raise ValueError("author chain does not map to one canonical full polymer sequence")
    seq=sequences[0]
    if not re.fullmatch("[ACDEFGHIKLMNPQRSTVWYXBZUO]+",seq):raise ValueError("unsupported canonical sequence symbols")
    aliases={}
    for rid,db,acc in zip(cif.get("_struct_ref.id",[]),cif.get("_struct_ref.db_name",[]),cif.get("_struct_ref.pdbx_db_accession",[])):
        if db.upper() in ("UNP","UNIPROT") and acc not in (".","?"):aliases[rid]=acc
    accessions=set()
    for rid,chains in zip(cif.get("_struct_ref_seq.ref_id",[]),cif.get("_struct_ref_seq.pdbx_strand_id",[])):
        if rid in aliases and chain in [c.strip() for c in chains.split(",")]:accessions.add(aliases[rid])
    unknown=sum(a not in "ACDEFGHIKLMNPQRSTVWY" for a in seq)/len(seq)
    return {"sequence":seq,"sequence_sha256":hashlib.sha256(seq.encode()).hexdigest(),
            "uniprot":sorted(accessions),"unknown_fraction":unknown,
            "sequence_audit_valid":len(seq)<=POLICY["max_sequence_length"] and unknown<=POLICY["max_unknown_fraction"]}


def cath_domains(list_path,bounds_path,wanted):
    domains={}; by_chain=defaultdict(list)
    with open(list_path) as f:
        for line in f:
            if line.startswith("#"):continue
            row=line.split()
            if not row:continue
            key=row[0][:4].lower()+":"+row[0][4]
            if key in wanted:
                item={"id":row[0],"topology":".".join(row[1:4]),"superfamily":".".join(row[1:5]),"ranges":[]}
                domains[row[0]]=item; by_chain[key].append(item)
    with open(bounds_path) as f:
        for line in f:
            row=line.split()
            if len(row)>1 and row[0] in domains:
                ranges=[]
                for segment in row[1].split(","):
                    match=re.fullmatch(r"(\d+)-(\d+)",segment)
                    if not match:raise ValueError(f"unexpected CATH seqres boundary: {segment}")
                    ranges.append([int(match[1]),int(match[2])])
                domains[row[0]]["ranges"]=ranges
    return by_chain


class PairCache:
    def __init__(self,path):
        self.db=sqlite3.connect(path)
        self.db.execute("CREATE TABLE IF NOT EXISTS pairs (key TEXT PRIMARY KEY, identity REAL, coverage REAL)")
        self.a=Align.PairwiseAligner(mode="global",match_score=2,mismatch_score=-1,open_gap_score=-5,extend_gap_score=-.5)
        self.pending=0
    def compare(self,x,y):
        s,t=x["sequence"],y["sequence"]
        if min(len(s),len(t))/max(len(s),len(t))<POLICY["longer_chain_coverage"]:return None
        key=hashlib.sha256(POLICY["alignment"].encode()).hexdigest()+":"+":".join(sorted((x["sequence_sha256"],y["sequence_sha256"])))
        hit=self.db.execute("SELECT identity,coverage FROM pairs WHERE key=?",(key,)).fetchone()
        if hit is None:
            # Canonical ordering avoids tie-dependent asymmetry in first optimal alignment.
            s,t=sorted((s,t))
            alignment=self.a.align(s,t)[0]; matches=aligned=0
            for (i,j),(k,l) in zip(*alignment.aligned):
                aligned+=j-i
                matches+=sum(a==b and a in "ACDEFGHIKLMNPQRSTVWY" for a,b in zip(s[i:j],t[k:l]))
            hit=(matches/max(aligned,1),aligned/max(len(s),len(t)))
            self.db.execute("INSERT INTO pairs VALUES (?,?,?)",(key,*hit)); self.pending+=1
            if self.pending>=100:self.db.commit();self.pending=0
        return {"identity":hit[0],"coverage":hit[1]} if hit[0]>=POLICY["identity"] and hit[1]>=POLICY["longer_chain_coverage"] else None
    def close(self):self.db.commit();self.db.close()


def run(index_path="data/prepared-666/index.json",outdir="data/exposure-audit-v1"):
    out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
    index=json.loads(Path(index_path).read_text()); prior=json.loads(Path("configs/prior_exposure.json").read_text(encoding="utf-8-sig"))
    exposed={p[:4].lower()+p[4:] for p in prior["apo_chains"]+prior["paired_chains"]}
    endpoints={}
    for r in index["records"]:
        p=r["source"]["pair"]
        endpoints[r["id"]]=[r["apo_id"].lower()+":"+p["apo_chain"],p["holo_pdb_id"].lower()+":"+p["holo_chain"]]
    wanted=exposed|set(sum(endpoints.values(),[]))
    ref=Path("data/reference");ref.mkdir(parents=True,exist_ok=True)
    list_path=download("https://download.cathdb.info/cath/releases/latest-release/cath-classification-data/cath-domain-list.txt",ref/"cath-domain-list.txt")
    bounds_path=download("https://download.cathdb.info/cath/releases/latest-release/cath-classification-data/cath-domain-boundaries-seqreschopping.txt",ref/"cath-seqres-boundaries.txt")
    cath=cath_domains(list_path,bounds_path,wanted)
    cache_path=out/"chain-metadata.json"
    cache=json.loads(cache_path.read_text()) if cache_path.exists() else {}
    failures={}; metadata={}
    groups=defaultdict(list)
    for key in wanted:groups[key[:4]].append(key)
    for n,(pdb,keys) in enumerate(sorted(groups.items()),1):
        try:
            path=download(f"https://files.rcsb.org/download/{pdb}.cif",Path("data/raw")/f"{pdb}.cif")
            digest=sha256(path); cif=None
            for key in keys:
                try:
                    if key not in cache or cache[key].get("structure_sha256")!=digest:
                        if cif is None:cif=MMCIF2Dict(str(path))
                        cache[key]=polymer_metadata(cif,key.split(":",1)[1])|{"structure_sha256":digest}
                    m=dict(cache[key]); m["domains"]=cath.get(key,[])
                    covered=set(); bad=False
                    for d in m["domains"]:
                        for lo,hi in d["ranges"]:
                            if lo<1 or hi>len(m["sequence"]) or hi<lo:bad=True
                            else:covered.update(range(lo,hi+1))
                    m["cath_coverage"]=len(covered)/len(m["sequence"])
                    m["cath_bounds_invalid"]=bad
                    m["cath_complete_enough"]=bool(m["domains"]) and not bad and m["cath_coverage"]>=POLICY["cath_seqres_coverage"]
                    metadata[key]=m
                except Exception as exc:failures[key]=str(exc)
        except Exception as exc:
            for key in keys:failures[key]=str(exc)
        if n%25==0:
            atomic_json(cache_path,cache); print(f"chain metadata {n}/{len(groups)} structures",flush=True)
    atomic_json(cache_path,cache)
    def aliases(keys):return set().union(*(normalized_aliases(metadata[k]["uniprot"]) for k in keys if k in metadata))
    def topologies(keys):return set().union(*({d["topology"] for d in metadata[k]["domains"]} for k in keys if k in metadata))
    train=[r for r in index["records"] if r["split"]=="train"]
    train_keys=set(sum([endpoints[r["id"]] for r in train],[]))
    train_pdbs={k[:4] for k in train_keys}; prior_pdbs={k[:4] for k in exposed}
    train_aliases=aliases(train_keys)|set().union(*(normalized_aliases(r["uniprot"]) for r in train))
    prior_aliases=aliases(exposed)
    train_cath=topologies(train_keys); prior_cath=topologies(exposed)|{prior["known_cath_overlap"]["topology"]}
    pairs=PairCache(out/"pair-cache.sqlite")
    def sequence_hits(keys,references):
        hits=[];seen=set()
        for k in keys:
            if k not in metadata or not metadata[k]["sequence_audit_valid"]:continue
            for refkey in sorted(references):
                if refkey not in metadata or not metadata[refkey]["sequence_audit_valid"]:continue
                dedup=(metadata[k]["sequence_sha256"],metadata[refkey]["sequence_sha256"])
                if dedup in seen:continue
                seen.add(dedup)
                hit=pairs.compare(metadata[k],metadata[refkey])
                if hit:hits.append({"chain":k,"reference":refkey,**hit})
        return hits
    rows=[]; retained=[]
    try:
        for n,r in enumerate(index["records"],1):
            keys=endpoints[r["id"]]; reasons=[]
            prior_hits=sequence_hits(keys,exposed)
            own_aliases=aliases(keys)|normalized_aliases(r["uniprot"]); own_cath=topologies(keys)
            if {k[:4] for k in keys}&prior_pdbs:reasons.append("prior_structure")
            if own_aliases&prior_aliases:reasons.append("prior_uniprot_alias")
            if prior_hits:reasons.append("prior_full_sequence_similarity")
            if own_cath&prior_cath:reasons.append("prior_CATH_topology")
            row={"id":r["id"],"split":r["split"],"endpoints":keys,"prior_reasons":list(reasons),"prior_sequence_hits":prior_hits,
                 "prior_cath_overlap":sorted(own_cath&prior_cath),"prior_alias_overlap":sorted(own_aliases&prior_aliases)}
            if r["split"]=="val":
                hits=sequence_hits(keys,train_keys)
                if {k[:4] for k in keys}&train_pdbs:reasons.append("training_structure")
                if own_aliases&train_aliases:reasons.append("training_uniprot_alias")
                if hits:reasons.append("training_full_sequence_similarity")
                if own_cath&train_cath:reasons.append("training_CATH_topology")
                if any(k not in metadata or not metadata[k]["sequence_audit_valid"] for k in keys):reasons.append("unresolved_full_sequence")
                if any(k not in metadata or not metadata[k]["cath_complete_enough"] for k in keys):reasons.append("insufficient_CATH_coverage")
                row.update(exclusion_reasons=reasons,training_sequence_hits=hits,training_cath_overlap=sorted(own_cath&train_cath))
                if not reasons:retained.append(r["id"])
            rows.append(row)
            if n%25==0:
                atomic_json(out/"progress.json",{"processed":n,"total":len(index["records"]),"retained_val":retained})
                print(f"exposure comparisons {n}/{len(index['records'])}",flush=True)
    finally:pairs.close()
    unknown_prior=[k for k in sorted(exposed) if k not in metadata or not metadata[k]["sequence_audit_valid"] or not metadata[k]["cath_complete_enough"]]
    report={"time":now(),"policy":POLICY,"source_index_sha256":sha256(index_path),"prior_config_sha256":sha256("configs/prior_exposure.json"),
            "CATH":{"version":"4.4.0; file date2024-12-16","list_sha256":sha256(list_path),"boundaries_sha256":sha256(bounds_path),
                    "source":"https://www.cathdb.info/download","license":"CC BY4.0; see docs/EXPOSURE_AUDIT.md for attribution"},
            "chains_requested":len(wanted),"chains_parsed":len(metadata),"failures":failures,"prior_annotation_gaps":unknown_prior,
            "cath_covered_chains":sum(m["cath_complete_enough"] for m in metadata.values()),
            "rows":rows,"retained_validation_ids":retained,"strict_val_count":len(retained),"locked_test_enabled":False,
            "known_topology_crosscheck":{k:sorted(topologies([k])) for k in ("3ppn:A","4p0i:B")},
            "limitations":["full-chain30%/80% alignment can miss remote/domain homologs","CATH is incomplete and not all structural-family systems agree",
                           "CATH coverage is at least80%, not proof of complete annotation","SCOP and pretrained-model overlap remain unaudited",
                           "the screened slice is post-hoc development analysis, not an independent test"]}
    atomic_json(out/"report.json",report)
    strict=dict(index); strict.update(protocol=POLICY["claim"],records=[r for r in index["records"] if r["split"]=="train" or r["id"] in retained],
                                     exposure_audit_sha256=sha256(out/"report.json"),locked_test_enabled=False)
    atomic_json(out/"screened-index.json",strict)
    return report
