from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
import pickle
import json



def Load_Dataset(path):
    try:
        ## load the dataset
        with open(path , 'r' , encoding= "utf-8") as f:
            data = json.load(f)
        ## now creation of list of complete dataset:
        documents = []

        for key , values in data.items:
            Questions = values.get("QUESTION" , "")
            Answers   = values.get("LONG_ANSWER" , "")
            contexts = values.get("CONTEXTS", [])
            labels = ", ".join(values.get("LABELS", []))

            full_text = f"Question: {Questions}\nLabels: {labels}\n\nContext: {' '.join(contexts)}\n\nAnswer: {long_answer}"
        
            documents.append(Document(page_content=full_text, metadata={"id": key}))
        return documents

    except Exception as e:
        raise ValueError(str(e))
    

def split_documents(documents):
    # Recursive splitter keeps sentence flow intact
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,  
        chunk_overlap=150,  
        length_function=len,
        separators=["\n\n", "\n", ".", "!", "?", " ", ""]
    )
    split_docs = text_splitter.split_documents(documents)
    return split_docs

def embedding():
    embedding_model = HuggingFaceEmbeddings(model_name="BAAI/bge-base-en-v1.5")
    return embedding_model


print("i am currently getting the location of the data")
dataset_path = "chatbot/dataset.json"
docs = Load_Dataset(dataset_path)
print("Loading of data has been done!")
split_docs = split_documents(docs)
model = embedding()
vector_store = FAISS.from_documents(split_docs, model)
faiss_index_path = "faiss_index"
vector_store.save_local(faiss_index_path)

print(f"✅ FAISS index saved at: {faiss_index_path}")


            
        
