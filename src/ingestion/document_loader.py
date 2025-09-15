# src/ingestion/document_loader.py

import os
from langchain_core.documents import Document
from unstructured.partition.pdf import partition_pdf
from unstructured.documents.elements import Table, NarrativeText
from langchain_text_splitters import RecursiveCharacterTextSplitter


def load_and_chunk_pdfs(directory_path: str) -> list[Document]:
    """
    Loads PDFs from a directory, applies a hierarchical chunking strategy,
    and returns a list of processed Document chunks.
    """
    all_chunks = []
    print(f"Loading and chunking documents from: {directory_path}")

    if not os.path.isdir(directory_path):
        print(f"Error: Directory '{directory_path}' not found.")
        return all_chunks

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1024, chunk_overlap=100)

    for filename in os.listdir(directory_path):
        if filename.lower().endswith(".pdf"):
            file_path = os.path.join(directory_path, filename)
            try:
                # Use unstructured to partition the PDF into elements
                elements = partition_pdf(filename=file_path, strategy="hi_res")

                for element in elements:
                    if isinstance(element, Table):
                        # Treat entire tables as single chunks
                        table_html = getattr(element, "text_as_html", None) or ""
                        if table_html:
                            table_md = f"Table:\n\n{element.text}\n\n"
                            metadata = element.metadata.to_dict()
                            metadata["source_file"] = filename
                            all_chunks.append(
                                Document(page_content=table_md, metadata=metadata)
                            )
                    elif isinstance(element, NarrativeText):
                        # Chunk the normal text paragraphs
                        metadata = element.metadata.to_dict()
                        metadata["source_file"] = filename
                        split_chunks = text_splitter.create_documents(
                            [element.text], metadatas=[metadata]
                        )
                        all_chunks.extend(split_chunks)

                print(f"Successfully processed and chunked {filename}")
            except Exception as e:
                print(f"Error processing file {filename}: {e}")

    return all_chunks
