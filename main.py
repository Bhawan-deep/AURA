#!/usr/bin/env python3
import argparse
import sys
import logging
import task_matcher as tm
import dispatcher as disp
import voice_dispatch as vd

# Basic logging for startup tasks
logging.basicConfig(level=logging.INFO, format="%(asctime)s\t%(levelname)s\t%(message)s")
logger = logging.getLogger("main")

def main():
    parser = argparse.ArgumentParser(description="AURA main entrypoint")
    parser.add_argument("--voice", action="store_true", help="Record once, transcribe and dispatch")
    parser.add_argument("--voice-loop", action="store_true", help="Enter continuous voice loop")
    parser.add_argument("--reindex", action="store_true", help="Re-index scripts directory into script_index.txt")
    parser.add_argument("--regen-embeddings", action="store_true", help="Regenerate script embeddings from docstrings")
    parser.add_argument("--no-startup", action="store_true", help="Skip index/embedding steps on startup")
    args = parser.parse_args()

    # Startup indexing / embedding (skip if user asks)
    if not args.no_startup:
        try:
            if args.reindex:
                logger.info("Re-indexing scripts...")
                tm.index_scripts()
            else:
                # ensure index exists; index_scripts is cheap and idempotent
                logger.info("Ensuring script index exists...")
                tm.index_scripts()

            if args.regen_embeddings:
                logger.info("Regenerating embeddings from script docstrings...")
                tm.generate_embeddings()
            else:
                # safe default: only generate if embeddings missing
                try:
                    import os
                    if not os.path.exists("embeddings/script_embeddings.pkl"):
                        logger.info("Embeddings missing; generating embeddings...")
                        tm.generate_embeddings()
                    else:
                        logger.info("Embeddings found; skipping generation.")
                except Exception as e:
                    logger.warning("Embedding existence check failed: %s. Attempting to generate.", e)
                    tm.generate_embeddings()
        except Exception as e:
            logger.exception("Startup index/embedding step failed: %s", e)
            # proceed — dispatcher and voice may still work if matcher has fallback

    # Runtime modes
    if args.voice_loop:
        vd.live_loop()
        return

    if args.voice:
        vd.transcribe_and_dispatch_once()
        return

    # Default: interactive text prompt
    try:
        user_input = input("Hukum krein aaka (in English please):\n")
        disp.dispatch(user_input)
    except KeyboardInterrupt:
        print("\nExiting.")
        return

if __name__ == "__main__":
    main()