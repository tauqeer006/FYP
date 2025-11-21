from flask import Flask, request, jsonify
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
import json
import os

app = Flask(__name__)

# Global variables for the RAG system
vector_store = None
embedding_model = None

def load_dataset(path):
    """Load the dataset from JSON file"""
    try:
        with open(path, 'r', encoding="utf-8") as f:
            data = json.load(f)
        
        documents = []
        for key, values in data.items():
            questions = values.get("QUESTION", "")
            answers = values.get("LONG_ANSWER", "")
            contexts = values.get("CONTEXTS", [])
            labels = ", ".join(values.get("LABELS", []))

            full_text = f"Question: {questions}\nLabels: {labels}\n\nContext: {' '.join(contexts)}\n\nAnswer: {answers}"
            documents.append(Document(page_content=full_text, metadata={"id": key}))
        
        return documents
    except Exception as e:
        raise ValueError(str(e))

def split_documents(documents):
    """Split documents into chunks"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
        length_function=len,
        separators=["\n\n", "\n", ".", "!", "?", " ", ""]
    )
    split_docs = text_splitter.split_documents(documents)
    return split_docs

def initialize_rag_system():
    """Initialize the RAG system"""
    global vector_store, embedding_model
    
    try:
        # Load dataset
        dataset_path = "dataset.json"
        docs = load_dataset(dataset_path)
        split_docs = split_documents(docs)
        
        # Initialize embedding model
        embedding_model = HuggingFaceEmbeddings(model_name="BAAI/bge-base-en-v1.5")
        
        # Create vector store
        vector_store = FAISS.from_documents(split_docs, embedding_model)
        
        print("✅ RAG system initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Error initializing RAG system: {str(e)}")
        return False

def get_answer(question):
    """Get answer using RAG system"""
    global vector_store
    
    if vector_store is None:
        return "RAG system not initialized"
    
    try:
        # Search for similar documents
        docs = vector_store.similarity_search(question, k=3)
        
        if not docs:
            return "No relevant information found for your question."
        
        # Combine the most relevant documents
        context = "\n\n".join([doc.page_content for doc in docs])
        
        # Simple response (you can enhance this with a proper LLM)
        return f"Based on the available information:\n\n{context}"
        
    except Exception as e:
        return f"Error processing your question: {str(e)}"

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        
        if 'question' not in data:
            return jsonify({'error': 'No question provided'}), 400
        
        question = data['question']
        answer = get_answer(question)
        
        return jsonify({
            'question': question,
            'answer': answer
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy', 
        'service': 'chatbot',
        'rag_initialized': vector_store is not None
    })

@app.route('/initialize', methods=['POST'])
def initialize():
    """Initialize the RAG system"""
    success = initialize_rag_system()
    
    if success:
        return jsonify({'message': 'RAG system initialized successfully'})
    else:
        return jsonify({'error': 'Failed to initialize RAG system'}), 500

if __name__ == '__main__':
    # Initialize RAG system on startup
    print("Initializing RAG system...")
    initialize_rag_system()
    
    app.run(debug=True, host='0.0.0.0', port=5004)


