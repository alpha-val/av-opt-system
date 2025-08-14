from __future__ import annotations
import json, re, uuid
from typing import Dict, Any, List
from .models import GraphDoc, Node, Relationship, Chunk
from .utils import extract_numbers_with_units
import langextract as lx

from flask import jsonify
import os
import pprint
from .build_prompt import gen_prompt
from .neo4j_utils import langextract_to_neo4j_format, build_neo4j_graph, save_to_neo4j

# Initialize pretty printer for debugging
pp = pprint.PrettyPrinter(indent=2)


class KGExtractor:
    """
    Wrapper around a hypothetical LangExtract client.
    - If GOOGLE_API_KEY present and LangExtract installed, call it.
    - Otherwise, use a simple regex-based fallback that extracts:
      * throughput (t/d, tph), power (kW, MW), $CAPEX/$OPEX
      * mentions of crusher/mill/tank/pump etc. as Equipment nodes
    """

    def __init__(self, ontology: Dict[str, Any], settings):
        self.ontology = ontology
        self.settings = settings
        self._client = None
        # Reuse existing prompt/example logic from build_graph (inline to avoid refactor)
        self.prompt = gen_prompt(ontology=self.ontology)
        # pp.pprint(f"[DEBUG] prompt: {self.prompt}")
        # A high-quality example to guide the model
        self.lx_examples = [
            lx.data.ExampleData(
                text="""Project Overview\nProject Type: Jaw Crusher Installation\n\nLocation: Carson City, Nevada (Carson River floodplain)\n\n
            Elevation: ~1,150 m\n\nOre Type: Gold ore\n\nSystem Capacity: 1,000 tph\n\n
            Moisture Content: 3%\n\nAvailability Target: 90%\n\nTop Feed Size: 10″\n\n
            Product Size Target: ~1″–6″\n\nSite Conditions\nClimate: Arid\n\n
            Annual Rainfall: ~127 mm\n\nSoil Type: Carson Series (floodplain smectitic clay)\n\n
            Soil Bearing Capacity: ~200 kPa\n\nWater Table Depth: ~0.5–1.5 m\n\n
            Crusher Details\nType: Jaw Crusher\n\nModel: PE1200×1500\n\nCapacity Range: 400–1,000 tph.\n\n
            Total Installed Cost (TIC): $1,800,000\nCrusher: $1,200,000\nFoundation: $5,160\nElectrical: $130,000\n
            Utilities: $50,000\nCivil Works: $130,000\nContingency: $280,000\n\nAssumptions & Risks\n
            U.S. labor & standards\nImport duties included\nAt-grade construction, minimal dewatering\n
            Stable exchange rate; 3% inflation\nTIC sensitive to: soil variability, permitting, equipment delays.
            The gold ore is crushed using a jaw crusher and a portable screening plant.""",
                extractions=[
                    lx.data.Extraction(
                        extraction_class="NODE",
                        extraction_text="jaw_crusher_installation",
                        # attributes={
                        #     "label": "PROJECT",
                        #     "cost": "$1,800,000",
                        #     "name": "Jaw Crusher Installation",
                        #     "category": "base_case",
                        # },
                        attributes={
                            "label": "PROJECT",
                            **self.ontology["NODE_PROP_EXAMPLES"],
                        },
                    ),
                    # lx.data.Extraction(
                    #     extraction_class="NODE",
                    #     extraction_text="jaw_crusher | crusher",
                    #     attributes={
                    #         "label": "EQUIPMENT",
                    #         "cost": "$1000",
                    #         "name": "Jaw Crusher",
                    #         "category": "machine",
                    #     },
                    # ),
                    # lx.data.Extraction(
                    #     extraction_class="NODE",
                    #     extraction_text="portable_screening_plant | screening_plant",
                    #     attributes={
                    #         "label": "EQUIPMENT",
                    #         "cost": "$1503",
                    #         "name": "Portable Screening Plant",
                    #         "category": "machine",
                    #     },
                    # ),
                    # lx.data.Extraction(
                    #     extraction_class="NODE",
                    #     extraction_text="gold_ore | ore",
                    #     attributes={
                    #         "label": "MATERIAL",
                    #         "cost": "$500",
                    #         "name": "Gold Ore",
                    #         "category": "material",
                    #     },
                    # ),
                    # lx.data.Extraction(
                    #     extraction_class="NODE",
                    #     extraction_text="total_installed_cost",
                    #     attributes={
                    #         "label": "COST_RULE",
                    #         "cost": "$1,800,000",
                    #         "name": "Total Installed Cost",
                    #         "category": "machine",
                    #     },
                    # ),
                    # lx.data.Extraction(
                    #     extraction_class="NODE",
                    #     extraction_text="gold_ore | ore",
                    #     attributes={
                    #         "label": "PROCESS",
                    #         "cost": "$500",
                    #         "name": "Ore Processing",
                    #         "category": "process",
                    #     },
                    # ),
                    lx.data.Extraction(
                        extraction_class="RELATIONSHIP",
                        extraction_text="<link_id_1>",
                        attributes={
                            "label": "USES",
                            "source": "jaw_crusher",
                            "target": "rock",
                            "directionality": "one-way",
                        },
                    ),
                    # lx.data.Extraction(
                    #     extraction_class="RELATIONSHIP",
                    #     extraction_text="<link_id_2>",
                    #     attributes={
                    #         "label": "located",
                    #         "source": "project",
                    #         "target": "Carson City",
                    #         "directionality": "one-way",
                    #     },
                    # ),
                ],
            )
        ]

    def _from_json(self, data: Dict[str, Any]) -> GraphDoc:
        nodes = [
            Node(id=n["id"], type=n["type"], properties=n.get("properties", {}))
            for n in data.get("nodes", [])
        ]
        rels = [
            Relationship(
                source_id=r["source_id"],
                target_id=r["target_id"],
                type=r["type"],
                properties=r.get("properties", {}),
            )
            for r in data.get("relationships", [])
        ]
        return GraphDoc(nodes=nodes, relationships=rels)

    # NEW: chunk-level batch extraction
    def build_graph_from_chunks(
        self,
        chunks: List[Chunk],
        join_delimiter: str = "\n\n",
    ) -> List[GraphDoc]:
        """
        Aggregate all chunk texts and run the same LangExtract logic once.
        Returns a list with a single GraphDoc (kept list for backward compatibility
        with previous 'graph_docs = [...]' usage).
        """
        if not chunks:
            return []
        print(f"[DEBUG] Building graph from {len(chunks)} chunks")
        # Combine chunk texts with lightweight provenance headers (helps model)
        combined_text_parts = []
        for i, ch in enumerate(chunks, start=1):
            combined_text_parts.append(
                f"[CHUNK {i} id={ch.chunk_id} pages={ch.page_start}-{ch.page_end}]\n{ch.text}"
            )
        combined_text = join_delimiter.join(combined_text_parts)
        print(f"[DEBUG] Combined text length: {len(combined_text)} : {combined_text[:250]}")
        result = lx.extract(
            text_or_documents=combined_text,
            prompt_description=self.prompt,
            examples=self.lx_examples,
            model_id="gemini-2.5-pro",
            api_key=os.getenv("GEMINI_API_KEY"),
            extraction_passes=1,
            batch_length=50,
            max_workers=30,
            temperature=0.0,
        )

        try:
            raw_nodes, raw_edges = langextract_to_neo4j_format(result.extractions)
        except Exception as e:
            print(f"\t[ERROR] Failed to convert LangExtract result to Neo4j format: {e}")
            return []
        try:
            graph_doc = build_neo4j_graph(raw_nodes, raw_edges, combined_text)
        except Exception as e:
            print(f"\t[ERROR] Failed to build Neo4j graph: {e}")
            return []
        print(graph_doc)
        return [graph_doc]
