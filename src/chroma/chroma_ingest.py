import chromadb
import json
from sentence_transformers import SentenceTransformer
import time
from memory_profiler import memory_usage


#Decide on the model to use:
embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


#Create an embedding for a query:
def encode_text(info):

    return embedding_model.encode(info).tolist()

#Create the Chroma client; need PersistentClient and not Client because we do not want
#data disappearing
def create_chroma_client(path="./chroma_db"):
    client = chromadb.PersistentClient(path=path)
    return client.get_or_create_collection(name="ds4300_course_notes")

"""chroma_client = chromadb.PersistentClient(path="./chroma_db")

#Create collection to index; pulling from existing preprocesed data
stored_collection = chroma_client.get_or_create_collection(name="ds4300_course_notes")"""

def log_chroma_performance(start_time, memory_usage, end_time):
    total_time = end_time - start_time
    highest_memory_usage = max(memory_usage)

    print(f" Total Execution Time: {total_time:.2f} seconds")
    print(f"Peak Memory Usage: {highest_memory_usage:.2f} MB")


#Going to obtain embeddings, create ids for them, and proceed to store them
def store_embedding(info, chunk_size):
    information = encode_text(info)
    stored_collection = create_chroma_client()

    #Create an id and then add it to the stored collection. Also handle duplicates:
    id_gen = str(hash(info))
    current_docs = stored_collection.get(ids=[id_gen])
    #Now apply check:
    if current_docs and len(current_docs["documents"]) > 0:
        print("Skipping already-made ids")
        return 

    #Store in the db
    stored_collection.add(documents=[info], embeddings=[information], ids=[id_gen], metadatas=[{"chunk_size": chunk_size}])
    print(f'Values have been stored: {info[:50]}')
    print(f'Stored values: (size {chunk_size}): {info[:50]}')

def process_docs(data):
    for i in data["processed_pdfs"]:
        title = i.get("title", "Unknown Title")
        print(f'Title processing: {title}')
        for chunk_size, chunked_material in i.get("chunked_content", {}).items():
            for j in chunked_material:
                store_embedding(j, chunk_size)


#Pull from json database:
def pull_from_json(path):

    try: 

        #Open and process the data
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)


        #Loop through the processed pdfs
        """for i in data["processed_pdfs"]: 
            title = i.get("title", "Unknown Title")
            print(f'Title processing: {title}')
            for chunk_size, chunked_material in i.get("chunked_content", {}).items():
                for j in chunked_material:
                    store_embedding(j, chunk_size)"""
        
        start_time = time.time()
        memory_data = memory_usage((process_docs, (data,), {}), interval=0.1)
        end_time = time.time()
        log_chroma_performance(start_time, memory_data, end_time)

        print("Embeddings were stored.")

        #Add in exception when fails:
    except Exception as e:
        print(f'There was an error with the json file: {e}')



#Get path to json data
def main():
    path = "data/processed_json/ds4300_course_notes.json"
    pull_from_json(path)

if __name__ == "__main__":
    main()