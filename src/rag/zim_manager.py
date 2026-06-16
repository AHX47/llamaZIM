import os
import libzim
import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

class ZimManager:
    def __init__(self, config):
        self.config = config
        self.zim_dir = config['zim_archives_dir']
        self.vector_db_path = config['vector_db_path']
        self.embedding_model = SentenceTransformer(config['embedding_model_name'])
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=self.vector_db_path)
        self.collection = self.chroma_client.get_or_create_collection(name="zim_knowledge")
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config['chunk_size'],
            chunk_overlap=config['chunk_overlap']
        )

    def index_zim_file(self, zim_filename):
        zim_path = os.path.join(self.zim_dir, zim_filename)
        if not os.path.exists(zim_path):
            print(f"ZIM file not found: {zim_path}")
            return

        print(f"Indexing ZIM file: {zim_filename}...")
        archive = libzim.Archive(zim_path)
        
        # Iterate through articles (simplified for demonstration)
        # In a real scenario, we'd use a more efficient way to traverse or target specific articles
        count = 0
        for i in range(archive.entry_count):
            try:
                entry = archive.get_entry_by_id(i)
                if entry.is_redirect or not entry.get_item().mimetype.startswith("text/html"):
                    continue
                
                # Extract text content (this is a simple extraction, could be improved with BeautifulSoup)
                content = entry.get_item().content.tobytes().decode('utf-8', errors='ignore')
                # Basic HTML tag removal
                import re
                clean_text = re.sub('<[^<]+?>', '', content)
                
                chunks = self.text_splitter.split_text(clean_text)
                
                for j, chunk in enumerate(chunks):
                    embedding = self.embedding_model.encode(chunk).tolist()
                    self.collection.add(
                        ids=[f"{zim_filename}_{i}_{j}"],
                        embeddings=[embedding],
                        documents=[chunk],
                        metadatas=[{"source": zim_filename, "article_title": entry.title}]
                    )
                
                count += 1
                if count % 100 == 0:
                    print(f"Indexed {count} articles...")
                if count >= 500: # Limit for demo purposes to save time/memory
                    break
                    
            except Exception as e:
                # print(f"Error processing entry {i}: {e}")
                continue
        
        print(f"Finished indexing {count} articles from {zim_filename}.")

    def search(self, query, n_results=3):
        query_embedding = self.embedding_model.encode(query).tolist()
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        return results['documents'][0]
