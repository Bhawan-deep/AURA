import sys
import task_matcher as tm
import dispatcher as disp
import voice_dispatch as vd

# Index all .py scripts in the scripts/ folder into script_index.txt
tm.index_scripts()

# Generate embeddings from script_index.txt and save to embeddings/script_embeddings.pkl
tm.generate_embeddings()

# Prompt user for natural language command
if "--voice-loop" in sys.argv:
    vd.live_loop()
elif "--voice" in sys.argv:
    vd.transcribe_and_dispatch()
else:
    user_input = input("Hukum krein aaka (in English please):\n")
    disp.dispatch(user_input)
