from __future__ import annotations

import argparse

from bookrag.index_store import build_index


def main() -> None:
    parser = argparse.ArgumentParser("Index book.txt")
    parser.add_argument("--book", required=True)
    parser.add_argument("--index-dir", default="data/book_index")
    parser.add_argument("--model", default="paraphrase-multilingual-MiniLM-L12-v2")
    args = parser.parse_args()
    build_index(args.book, args.index_dir, args.model)


if __name__ == "__main__":
    main()
