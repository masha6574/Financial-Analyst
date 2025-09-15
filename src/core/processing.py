# src/core/processing.py

# CHANGED: Corrected the typo in HuggingFaceEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_community.vectorstores.utils import filter_complex_metadata

CHROMA_DB_PATH = "chroma_db"


def create_and_store_embeddings(ticker: str, all_chunks: list[Document]):
    """
    Takes a list of document chunks, filters complex metadata,
    creates embeddings, and stores them in ChromaDB.
    """
    if not all_chunks:
        print(f"No chunks provided for {ticker}. Aborting embedding process.")
        return

    filtered_chunks = filter_complex_metadata(all_chunks)

    print(
        f"Creating and storing embeddings for {len(filtered_chunks)} chunks for {ticker}..."
    )

    embedding_model = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    Chroma.from_documents(
        documents=filtered_chunks,
        embedding=embedding_model,
        collection_name=ticker.lower(),
        persist_directory=CHROMA_DB_PATH,
    )

    print(f"Successfully stored embeddings for {ticker}.")
