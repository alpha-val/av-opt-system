from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_community.graphs import Neo4jGraph
from langchain_openai import ChatOpenAI
from ..config import NODE_TYPES, EDGE_TYPES, NEO4J_CONFIG


def ingest_document(input_bytes_or_str):
    try:
        # Step 1: Load and parse input
        try:
            raw_docs = (
                PyMuPDFLoader(input_bytes_or_str).load()
                if isinstance(input_bytes_or_str, bytes)
                else [{"text": input_bytes_or_str}]
            )
        except Exception as e:
            raise ValueError(f"Error loading or parsing input: {e}")

        try:
            chunks = RecursiveCharacterTextSplitter(
                chunk_size=2000, chunk_overlap=200
            ).split_documents(raw_docs)
        except Exception as e:
            raise ValueError(f"Error splitting text into chunks: {e}")

        # Step 2: Transform into graph documents
        try:
            transformer = LLMGraphTransformer(
                llm=ChatOpenAI(model="gpt-4o-mini", temperature=0),
                allowed_nodes=NODE_TYPES,
                allowed_edges=EDGE_TYPES,
                use_functions=True,
            )
            graph_docs_raw = transformer.transform_documents(chunks)
            graph_docs = transformer.postprocess_graph_documents(
                graph_docs_raw, score_threshold=0.80
            )
        except Exception as e:
            raise RuntimeError(f"Error during graph transformation: {e}")

        # Print the graph_docs object before ingestion
        print("Graph documents to be ingested into Neo4j:", graph_docs)

        # # Step 3: Write to Neo4j
        # try:
        #     neo = Neo4jGraph(**NEO4J_CONFIG)
        #     neo.add_graph_documents(graph_docs, include_source=True)
        # except Exception as e:
        #     raise ConnectionError(f"Error connecting to Neo4j or writing data: {e}")

        # Return the number of documents ingested
        return len(graph_docs)

    except Exception as e:
        # Log the error (you can replace this with a proper logging mechanism)
        print(f"Error in ingest_document: {e}")
        return 0  # Return
