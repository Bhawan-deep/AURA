import os

def index_scripts(script_folder="scripts/", index_file="script_index.txt"):
    with open(index_file, "w") as f:
        for file in os.listdir(script_folder):
            if file.endswith(".py"):
                f.write(file + "\n")

index_scripts()