from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_community.graphs import Neo4jGraph
from langchain_openai import ChatOpenAI
from langchain.schema import Document
from langchain_community.graphs.graph_document import Node, Relationship, GraphDocument
from ..config import (
    NODE_TYPES,
    EDGE_TYPES,
    NODE_PROPERTIES,
    EDGE_PROPERTIES,
    NEO4J_CONFIG,
)
import uuid
import pprint
from typing import Dict, List, Any
from collections import defaultdict
from copy import deepcopy


# Initialize a pretty printer for debugging
pp = pprint.PrettyPrinter(indent=1)


# # Utility function to safely get a node by ID, ensuring it exists
# def _dedupe_case_insensitive(
#     seq: List[Dict[str, Any]], key: str = "id"
# ) -> List[Dict[str, Any]]:
#     """Order-preserving deduplication by `key`, case-insensitive."""
#     od = OrderedDict()
#     for item in seq:
#         normalized_key = getattr(
#             item, key
#         ).lower()  # Normalize the key to lowercase for case-insensitivity
#         od[normalized_key] = item  # Use the normalized key for deduplication
#     return list(od.values())


def canonicalize_name(name: str) -> str:
    return "".join(c for c in name.lower() if c.isalnum())


def dedupe_nodes_with_property_merge(nodes: list[Node]) -> list[Node]:
    """
    Deduplicate nodes by canonicalized ID.
    When duplicates exist, merge their properties into a single node
    (favoring union of all values where possible).
    """
    grouped = defaultdict(list)
    for n in nodes:
        cid = canonicalize_name(n.id)
        grouped[cid].append(n)

    merged_nodes = []
    for cid, node_group in grouped.items():
        base = deepcopy(node_group[0])
        for other in node_group[1:]:
            for k, v in other.properties.items():
                if k not in base.properties:
                    base.properties[k] = v
                elif base.properties[k] != v:
                    # Union if values differ
                    if isinstance(base.properties[k], list):
                        if isinstance(v, list):
                            base.properties[k] = list(set(base.properties[k] + v))
                        else:
                            if v not in base.properties[k]:
                                base.properties[k].append(v)
                    elif base.properties[k] != v:
                        base.properties[k] = (
                            [base.properties[k], v]
                            if v != base.properties[k]
                            else base.properties[k]
                        )
        merged_nodes.append(base)
    return merged_nodes


def ingest_doc_graph_transform(
    input_bytes_or_str, doc_name="<document ref>", full_wipe=False
):
    print("\n\n> > > > > > Starting ingestion with graph transformation...")
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
                chunk_size=2750, chunk_overlap=800
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

            doc_id = str(uuid.uuid4())  # Generate a UUID and convert it to a string
            doc_node = Node(
                id=doc_id,
                type="Document",
                properties={
                    "name": f"doc_{doc_id}",
                    "_source_doc": doc_name,
                    "_confidence": 1.0,
                },
            )
            # Convert text chunks to graph documents
            graph_docs_raw = transformer.convert_to_graph_documents(chunks)
            print("> [DEBUG] Length of graph_docs_raw:", len(graph_docs_raw))

            # Filter graph documents based on score threshold
            graph_docs = [
                gd
                for gd in graph_docs_raw
                if getattr(gd, "score", 1.0) >= 0.80  # or gd.metadata["score"]
            ]

            # print("> [DEBUG] Node IDs")
            # # Print the IDs and properties of nodes in the graph documents            # Print the IDs and properties of nodes, if no name then print "<no name>"
            # for gd in graph_docs:
            #     print(f"gd num nodes: {len(gd.nodes)}")
            #     print([f"{node.id} ({node.properties})\n" for node in gd.nodes])

            # # Deduplicate nodes across all graph documents
            # all_nodes = []
            # for gd in graph_docs:
            #     all_nodes.extend(gd.nodes)  # Collect all nodes from all graph documents

            # # Update nodes to ensure IDs are lowercase, spaces replaced with underscores, and "name" is set
            # for node in all_nodes:
            #     node.properties["name"] = (
            #         node.id
            #     )  # Set "name" property to the original ID
            #     node.id = node.id.lower().replace(
            #         " ", "_"
            #     )  # Convert ID to lowercase and replace spaces with underscores

            # # Reassign deduplicated nodes back to their respective graph documents
            # for gd in graph_docs:
            #     gd.nodes = [node for node in all_nodes if node in gd.nodes]
            #     for node in gd.nodes:
            #         print(node.id, node.properties, "\n")

            # for gd in graph_docs:
            #     for node in gd.nodes:
            #         node.properties["name"] = node.id # Set "name" property to the original ID
            #         node.id = node.id.lower().replace(" ", "_")  # Convert ID to lowercase and replace spaces with underscores

            # Create relationships between the document node and all other nodes
            global_relationships = []
            for gd in graph_docs:
                for node in gd.nodes:
                    # Create a relationship from the document node to the current node
                    relationship = Relationship(
                        source=doc_node,
                        target=node,
                        type="CONTAINS",  # Define the relationship type
                        properties={
                            "_confidence": 1.0
                        },  # Optional properties for the relationship
                    )
                    global_relationships.append(relationship)

            meta = {
                "doc_id": doc_id,
            }

            # Add the document node and relationships to the graph
            doc_graph = GraphDocument(
                nodes=[doc_node],
                relationships=global_relationships,
                source=Document(
                    page_content=input_bytes_or_str, metadata={"id": "generated-by-llm"}
                ),
            )

            # Append the document graph to the list of graph documents
            graph_docs.append(doc_graph)

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
        print("[DEBUG]: Successfully wrote data to Neo4j AuraDB.")
        # print the length of the nodes and relationships
        # pp.pprint(graph_docs[0].nodes)
        # pp.pprint(graph_docs[0].relationships)
        print(
            f"[DEBUG]: Number of nodes: {len(graph_docs[0].nodes)}, and edges: {len(graph_docs[0].relationships)}"
        )
        print(f"< < < < < < Done extracting graphs (len: {len(graph_docs)})\n\n")
        print("\n\n")
        # Return the number of documents ingested
        return len(graph_docs)

    except Exception as e:
        # Log the error (you can replace this with a proper logging mechanism)
        print(f"[DEBUG]: Error in ingest_document: {e}")
        return 0  # Return
