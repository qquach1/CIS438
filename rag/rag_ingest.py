#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from pathlib import Path

#%%
if __name__ == "__main__":    
    import argparse    
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("kb_path", type=Path, help="path to the knowledge base")    
    parser.add_argument("-c", "--collection", required=True, type=str, help="name of the collection to be created")
    parser.add_argument("-r", "--retriever", choices=['hypo', 'parent'], help="The default is multi-query rerank retriever\nhypo: hypothetical question retriever\nparent: parent-child retriever")
    args = parser.parse_args()

#%%

from simonbb.cis438.rag import load_documents, MultiQueryRerankRetriever, ParentDocumentRetriever, HypotheticalQuestionRetriever, build_rag


import torch
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
from langchain_huggingface import HuggingFaceEmbeddings
from sentence_transformers import CrossEncoder
embedding_model = HuggingFaceEmbeddings( model_name="BAAI/bge-large-en-v1.5", model_kwargs = {'device': device}, encode_kwargs = {'normalize_embeddings': False} )
reranker_model = CrossEncoder("BAAI/bge-reranker-large")

from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv( override=True )

store_path = Path.home() / 'chroma'

def checkChroma():
    import chromadb
    import sqlite3
    client = chromadb.PersistentClient(path=store_path)
    conn = sqlite3.connect( store_path / "chroma.sqlite3" )
    cursor = conn.cursor()
    cursor.execute("SELECT collection, id FROM segments WHERE scope = 'VECTOR'")
    folder_map = dict(cursor.fetchall())
    conn.close()
    for collection in client.list_collections():
        folder_name = folder_map.get( str(collection.id), "No folder created yet" )
        print( f"Name: {collection.name} | Count: {collection.count()} | Folder: {folder_name}" )        

#%%
    
if __name__ == "__main__":
    kb_path = args.kb_path
    collection_name = args.collection
    docs, success_cnt, page_cnt = load_documents( kb_path )
    if docs is None:
        exit()
    else:
        print(f"Files: {success_cnt}, Pages: {page_cnt}, documents: {len(docs)}")
    
    if args.retriever is not None:
        if args.retriever == 'hypo':
            llm = ChatOpenAI( model='simonbb', max_tokens=4096, temperature=0.7, extra_body={"chat_template_kwargs": {"enable_thinking": False}},)            
            retriever = HypotheticalQuestionRetriever(
                llm = llm,
                persist_directory= store_path,
                embeddings = embedding_model,
                question_collection = f'{collection_name}_hypothetical_question',
                chunk_collection= f'{collection_name}_original_chunks',
                create_collection_if_not_exists = True
            )
            retriever.ingest( docs, source_dir=str(kb_path) )
        elif args.retriever == 'parent':
            retriever = ParentDocumentRetriever(
                persist_directory= store_path,
                embeddings = embedding_model,
                parent_collection = f'{collection_name}_parent',
                child_collection = f'{collection_name}_child',  
            )
            retriever.ingest( docs, source_dir=str(kb_path), parent_chunk_size=1000, child_chunk_size=500 )
    else:
        retriever = MultiQueryRerankRetriever(  persist_directory=store_path, collection_name=collection_name, embeddings=embedding_model, chunk_size=500, chunk_overlap=50, create_collection_if_not_exists=True)
        retriever.ingest( docs, source_dir=str(kb_path) )            
    
else:
    checkChroma()
    
#%%    
    kb_name = 'gba411'
    kb_name = 'cis438'
    kb_name = 'cis433'  
    kb_name = 'paestum'
    
    query = 'what is this course about?'
    query = 'Is there a final exam?'
    query = 'When is the office hours?'
    query = 'who is the ta?'
    query = 'what is the most famous place to visit?'    
#%%    
    retriever = MultiQueryRerankRetriever( persist_directory=store_path, collection_name=kb_name, embeddings=embedding_model )   
    
    retriever = MultiQueryRerankRetriever( persist_directory= store_path, collection_name=kb_name, embeddings=embedding_model, query_llm=retriever.llm, reranker=reranker_model, k=3, top_n=5 )
       
#%%
    retriever = ParentDocumentRetriever(
        persist_directory= store_path,
        embeddings = embedding_model,
        parent_collection = f'{kb_name}_parent',
        child_collection = f'{kb_name}_child',
    )
#%%    
    retriever = HypotheticalQuestionRetriever(
        persist_directory= store_path,
        embeddings = embedding_model,
        question_collection = f'{kb_name}_hypothetical_question',
        chunk_collection= f'{kb_name}_original_chunks'
    )
    
#%%
    llm = ChatOpenAI( model='simonbb', max_tokens=4096, temperature=0.7, extra_body={"chat_template_kwargs": {"enable_thinking": False}} )
    rag_chain = build_rag( retriever, llm )
    
#%%    
    response = rag_chain.invoke( query )
    response['answer']
