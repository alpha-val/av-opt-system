import langextract as lx

from flask import jsonify
import os
import pprint
from .build_prompt import gen_prompt
from .config import NEO4J_CONFIG
from .neo4j_whisperer import langextract_to_neo4j_format, build_neo4j_graph, save_to_neo4j

# Initialize pretty printer for debugging
pp = pprint.PrettyPrinter(indent=2)

def build_graph(input_data, full_wipe: bool = False):
    # Implement your document processing logic here

    # Define the prompt and extraction rules
    prompt = gen_prompt()

    print("[DEBUG] Generated prompt")
    # pp.pprint(prompt)

    # A high-quality example to guide the model
    examples = [
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
                    attributes={
                        "label": "PROJECT",
                        "category": "base_case",
                    },
                ),
                lx.data.Extraction(
                    extraction_class="NODE",
                    extraction_text="jaw_crusher | crusher",
                    attributes={
                        "label": "EQUIPMENT",
                        "cost": "$1000",
                        "name": "Jaw Crusher",
                        "category": "machine",
                    },
                ),
                lx.data.Extraction(
                    extraction_class="NODE",
                    extraction_text="portable_screening_plant | screening_plant",
                    attributes={
                        "label": "EQUIPMENT",
                        "cost": "$1503",
                        "name": "Portable Screening Plant",
                        "category": "machine",
                    },
                ),
                lx.data.Extraction(
                    extraction_class="NODE",
                    extraction_text="gold_ore | ore",
                    attributes={
                        "label": "MATERIAL",
                        "cost": "$500",
                        "name": "Gold Ore",
                        "tph": "1000",
                        "moisture_content": "3%",
                        "category": "material",
                    },
                ),
                lx.data.Extraction(
                    extraction_class="NODE",
                    extraction_text="total_installed_cost",
                    attributes={
                        "label": "COST_RULE",
                        "cost": "$1,800,000",
                        "name": "Total Installed Cost",
                        "category": "machine",
                    },
                ),
                lx.data.Extraction(
                    extraction_class="NODE",
                    extraction_text="gold_ore | ore",
                    attributes={
                        "label": "PROCESS",
                        "name": "Ore Processing",
                        "category": "process",
                    },
                ),
                lx.data.Extraction(
                    extraction_class="RELATIONSHIP",
                    extraction_text="<link_id_1>",
                    attributes={
                        "label": "USES",
                        "source": "jaw_crusher",
                        "target": "rock",
                        "directionality": "one-way",
                        "count": 1,
                    },
                ),
                lx.data.Extraction(
                    extraction_class="RELATIONSHIP",
                    extraction_text="<link_id_2>",
                    attributes={
                        "label": "located",
                        "source": "project",
                        "target": "Carson City",
                        "directionality": "one-way",
                        "count": 1,
                    },
                ),
            ],
        )
    ]

    # The input text to be processed
    try:
        input_text = input_data["text"]
    except KeyError:
        return {"error": "Missing 'text' field in input data"}, 400

    print("[DEBUG] Running LangExtract extraction...")
    # Run the extraction
    result = lx.extract(
        text_or_documents=input_text,
        prompt_description=prompt,
        examples=examples,
        model_id="gemini-2.5-flash",  # Use a specific model ID
        api_key=os.getenv("GEMINI_API_KEY"),  # Ensure you set this environment variable
        extraction_passes=1,  # Multiple passes for improved recall
        batch_length=25,    # Chunks processed per batch
        # max_char_buffer=10000,  # Max characters per chunk (let the model handle this)
        max_workers=20,  # Parallel processing for speed (batch_length must be > max_workers)
        temperature=0.0,  # Lower temperature for deterministic output
    )

    # print('{"data":[')
    # for idx, ex in enumerate(result.extractions):
    #     item = {
    #         "label": ex.extraction_class,
    #         "name": ex.extraction_text,
    #         "properties": ex.attributes,
    #     }
    #     end = "," if idx < len(result.extractions) - 1 else ""
    #     print(f"{item}{end}")
    # print("]}")

    print("[DEBUG] Converting LangExtract output to Neo4j format...")
    # Convert langextract output to Neo4j format
    raw_nodes, raw_edges = langextract_to_neo4j_format(result.extractions)

    print("[DEBUG] Building Neo4j graph...")
    # Convert to Neo4j format
    graph_doc = build_neo4j_graph(raw_nodes, raw_edges, input_text)

    print("[DEBUG] Saving to Neo4j database...")
    # Save to Neo4j
    save_result = save_to_neo4j(graph_doc, full_wipe=full_wipe)

    print(f"[DEBUG] Result: {save_result}")
    return save_result 
