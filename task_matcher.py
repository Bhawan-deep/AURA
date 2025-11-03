import os # s

def index_scripts(script_folder="scripts/", index_file="script_index.txt"):
    with open(index_file, "w") as f:
        for file in os.listdir(script_folder):
            if file.endswith(".py"):
                f.write(file + "\n")

def generate_embeddings(index_file="script_index.txt"):
    import pickle
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    with open(index_file) as f:
        scripts = [line.strip() for line in f]
    embeddings = model.encode(scripts)
    with open("embeddings/script_embeddings.pkl", "wb") as f:
        pickle.dump((scripts, embeddings), f)

def match_command(user_input):
    import pickle, numpy as np
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    model = SentenceTransformer("all-MiniLM-L6-v2")
    with open("embeddings/script_embeddings.pkl", "rb") as f:
        scripts, embeddings = pickle.load(f)
    input_embedding = model.encode([user_input])
    scores = cosine_similarity(input_embedding, embeddings)[0]
    best_match = scripts[np.argmax(scores)]
    return best_match