from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_community.graphs import Neo4jGraph
# from langchain_neo4j import Neo4jGraph # causes an import error
from langchain_openai import ChatOpenAI
from langchain.schema import Document
from ..config import (
    NODE_TYPES,
    EDGE_TYPES,
    NODE_PROPERTIES,
    EDGE_PROPERTIES,
    NEO4J_CONFIG,
)

import pprint

pp = pprint.PrettyPrinter(indent=1)


# Convenience slug for canonical keys
def slug(text: str) -> str:
    return slugify(text, lowercase=True, separator="-")


def ingest_doc_graph_transform(input_bytes_or_str, full_wipe=False):
    print("\n\n= = = = = = = = = = = = = = = = = = =")
    try:
        # STEP 1: Load and parse input
        try:
            raw_docs = (
                PyMuPDFLoader(input_bytes_or_str).load()
                if isinstance(input_bytes_or_str, bytes)
                else [{"text": input_bytes_or_str}]
            )
        except Exception as e:
            raise ValueError(f"[DEBUG]: Error loading or parsing input: {e}")

        # Convert raw documents to langchain Document objects
        try:
            docs = [
                Document(page_content=d["text"], metadata=d.get("metadata", {}))
                for d in raw_docs
            ]
            chunks = RecursiveCharacterTextSplitter(
                chunk_size=2500, chunk_overlap=300
            ).split_documents(docs)
        except Exception as e:
            raise ValueError(f"[DEBUG]: Error splitting text into chunks: {e}")

        # STEP 2: Transform into graph documents
        try:
            transformer = LLMGraphTransformer(
                llm=ChatOpenAI(model="gpt-4o", temperature=0),
                allowed_nodes=NODE_TYPES,
                allowed_relationships=EDGE_TYPES,
                node_properties=NODE_PROPERTIES,  # Allow extraction of any node properties
                relationship_properties=EDGE_PROPERTIES,  # Allow extraction of any relationship properties
            )

            # Convert text chunks to graph documents
            graph_docs_raw = transformer.convert_to_graph_documents(chunks)

            # Filter graph documents based on score threshold
            graph_docs = [
                gd
                for gd in graph_docs_raw
                if getattr(gd, "score", 1.0) >= 0.80  # or gd.metadata["score"]
            ]
            print("[DEBUG] Node IDs")
            for node in graph_docs.nodes:
                # Print node ID and node name
                print("Node: ", node["id"], node["properties"]["id"])

            # —————————————— Update nodes to ensure IDs are lowercase, spaces replaced with underscores, and "name" is set —————————————— #
            for gd in graph_docs:
                for node in gd.nodes:
                    # node.properties["name"] = (
                    #     node.id.lower().replace(" ", "_")
                    # )  # Set "name" property to the original ID
                    node.id = node.id.lower().replace(
                        " ", "_"
                    )  # Convert ID to lowercase and replace spaces with underscores

            # # Print nodes after normalization
            # print("\n=== Nodes After Normalization ===")
            # for gd in graph_docs:
            #     for node in gd.nodes:
            #         print(f"Node ID: {node.id}")
            #         print(f"Type: {node.type}")
            #         print(f"Properties: {node.properties}")
            #         print("-" * 40)
            # ————————————————————————————————————————————— #

            # —————————————— De-dupe the nodes —————————————— #
            from collections import defaultdict

            deduped_nodes_map = {}  # id → node
            merged_properties = defaultdict(dict)

            for gd in graph_docs:
                unique_nodes = []
                for node in gd.nodes:
                    if node.id in deduped_nodes_map:
                        # print("-- dupe found: ", node.id)
                        # Merge properties: update existing with new ones (new values overwrite)
                        merged_properties[node.id].update(node.properties)
                    else:
                        deduped_nodes_map[node.id] = node
                        merged_properties[node.id] = node.properties
                        unique_nodes.append(node)
                gd.nodes = unique_nodes  # update with deduped nodes

            # Apply merged properties back to the deduped nodes
            for node_id, props in merged_properties.items():
                deduped_nodes_map[node_id].properties = props

            # print("\n ! ! ! ! ! !")
            # # Print nodes after de-duping
            # print("\n=== Nodes After De Duping ===")
            # for gd in graph_docs:
            #     for node in gd.nodes:
            #         print(f"Node ID: {node.id}")
            #         print(f"Type: {node.type}")
            #         print(f"Properties: {node.properties}")
            #         print("-" * 40)
            # ————————————————————————————————————————————— #

            # pp.pprint(graph_docs[0].nodes)
            # pp.pprint(graph_docs[0].relationships)
        except Exception as e:
            raise RuntimeError(f"Error during graph transformation: {e}")

        # STEP 3: Write to Neo4j

        # Set up Neo4j connection
        neo_graph = Neo4jGraph(
            url=NEO4J_CONFIG["uri"],
            username=NEO4J_CONFIG["auth"][0],
            password=NEO4J_CONFIG["auth"][1],
        )

        # Test connection
        try:
            neo_graph.query("RETURN 1")
        except Exception as e:
            print(f"Neo4j connection failed: {e}")

        # Delete all existing nodes and relationships if full_wipe is True
        if full_wipe:
            print(
                "[DEBUG]: Full wipe enabled, deleting all existing nodes and relationships."
            )
            neo_graph.query("MATCH (n) DETACH DELETE n")

        neo_graph.add_graph_documents(graph_docs, include_source=True)
        print(f"[DEBUG]: Successfully wrote {len(graph_docs[0].nodes)} nodes and {len(graph_docs[0].relationships)} relationships to Neo4j AuraDB.")
        print("= = = = = = = = = = = = = = = = = = =\n\n")
        # Return the number of documents ingested
        return len(graph_docs)

    except Exception as e:
        # Log the error (you can replace this with a proper logging mechanism)
        print(f"[DEBUG]: Error in ingest_document: {e}")
        return 0  # Return
