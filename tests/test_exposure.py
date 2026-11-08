import hashlib
import tempfile
import unittest
from pathlib import Path
from pcp.exposure import PairCache,polymer_metadata,normalized_aliases


class ExposureTests(unittest.TestCase):
    def test_full_entity_sequence_and_author_chain_alias(self):
        cif={"_entity_poly.pdbx_strand_id":["A,B","AA"],"_entity_poly.pdbx_seq_one_letter_code_can":["ACD\nEFG","WYV"],
             "_struct_ref.id":["1"],"_struct_ref.db_name":["UNP"],"_struct_ref.pdbx_db_accession":["P12345-2"],
             "_struct_ref_seq.ref_id":["1"],"_struct_ref_seq.pdbx_strand_id":["B"]}
        self.assertEqual(polymer_metadata(cif,"B")["sequence"],"ACDEFG")
        self.assertEqual(polymer_metadata(cif,"AA")["sequence"],"WYV")
        self.assertEqual(normalized_aliases(polymer_metadata(cif,"B")["uniprot"]),{"P12345"})
        self.assertEqual(normalized_aliases([None,"unknown",".","N/A"]),set())
        with self.assertRaises(ValueError):polymer_metadata(cif,"C")
    def test_unknown_matches_do_not_establish_homology(self):
        def seq(s):return {"sequence":s,"sequence_sha256":hashlib.sha256(s.encode()).hexdigest()}
        with tempfile.TemporaryDirectory() as tmp:
            cache=PairCache(Path(tmp)/"pairs.sqlite")
            self.assertIsNone(cache.compare(seq("X"*80+"A"*20),seq("X"*80+"A"*20)))
            good=cache.compare(seq("ACDEFGHIKLMNPQRSTVWY"),seq("ACDEFGHIKLMNPQRSTVWY"))
            self.assertEqual(good,{"identity":1.,"coverage":1.})
            self.assertIsNone(cache.compare(seq("A"*10),seq("A"*100)))
            cache.close()


if __name__=="__main__":unittest.main()
