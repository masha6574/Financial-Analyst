# src/core/qa_agent.py

import os
import json
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.utils.database_handler import get_cached_stock_overview

# NEW: Load environment variables to access API keys
load_dotenv()
CHROMA_DB_PATH = "chroma_db"


def get_base_rag_components(ticker: str):
    """Helper function to get the components common to both RAG chains."""
    embedding_model = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    template = """
    You are an expert financial analyst. Your task is to provide clear, concise, and detailed answers based on the following context.
    Combine all available information to give the most comprehensive answer possible.

    UNSTRUCTURED CONTEXT (from reports and news):
    {context}

    STRUCTURED FINANCIAL DATA:
    {stock_data}

    QUESTION:
    {question}

    ANSWER:
    """
    prompt = ChatPromptTemplate.from_template(template)

    # NEW: Securely get the API key and validate it
    groq_api_key = os.getenv("GROQ_AI_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables.")

    # UPDATED: Pass the API key directly to the ChatGroq constructor
    llm = ChatGroq(
        groq_api_key=groq_api_key, model_name="gemma2-9b-it", temperature=0.1
    )

    return embedding_model, prompt, llm


def create_persistent_rag_chain(ticker: str):
    """Creates a RAG chain that queries the persistent, cached ChromaDB."""
    embedding_model, prompt, llm = get_base_rag_components(ticker)

    vector_store = Chroma(
        persist_directory=CHROMA_DB_PATH,
        embedding_function=embedding_model,
        collection_name=ticker.lower(),
    )
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})

    stock_overview_data = get_cached_stock_overview(ticker)
    stock_data_str = (
        json.dumps(stock_overview_data, indent=2)
        if stock_overview_data
        else "Not available."
    )

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    rag_chain = (
        {
            "context": retriever | format_docs,
            "stock_data": lambda x: stock_data_str,
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain


def create_live_rag_chain(documents: list[Document], stock_overview: dict):
    """
    Creates a temporary, in-memory RAG chain from live-fetched documents.
    """
    embedding_model, prompt, llm = get_base_rag_components("live")

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=100)
    chunks = text_splitter.split_documents(documents)

    vector_store = Chroma.from_documents(chunks, embedding_model)
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})

    stock_data_str = (
        json.dumps(stock_overview, indent=2) if stock_overview else "Not available."
    )

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    rag_chain = (
        {
            "context": retriever | format_docs,
            "stock_data": lambda x: stock_data_str,
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain
