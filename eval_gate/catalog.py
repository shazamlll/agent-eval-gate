"""Synthetic bookstore catalog and a tiny rule-based "system under test".

Everything here is invented for demo purposes: no real books, authors or
prices. The stub answerer is deliberately simple -- it exists so the eval
gate has something deterministic to measure, not to be a good QA system.
"""

from __future__ import annotations

import re

BOOKS = [
    {"title": "The Clockmaker's Daughter", "author": "Ada Marsh",
     "genre": "historical fiction", "price": 18.99, "year": 2021, "in_stock": True},
    {"title": "Salt & Cinder", "author": "Ada Marsh",
     "genre": "fantasy", "price": 24.50, "year": 2023, "in_stock": True},
    {"title": "A Field Guide to Vanishing Birds", "author": "Tomás Rivera",
     "genre": "nature", "price": 29.00, "year": 2020, "in_stock": True},
    {"title": "The Cartographer's Apprentice", "author": "Ines Duarte",
     "genre": "adventure", "price": 16.95, "year": 2022, "in_stock": False},
    {"title": "Notes from a Small Observatory", "author": "Priya Nair",
     "genre": "science", "price": 21.00, "year": 2019, "in_stock": True},
    {"title": "The Winter Market", "author": "Henrik Solberg",
     "genre": "literary fiction", "price": 19.99, "year": 2024, "in_stock": True},
    {"title": "Beneath the Neon Harbor", "author": "Mei Lin",
     "genre": "mystery", "price": 15.50, "year": 2023, "in_stock": True},
    {"title": "How to Build a Treehouse", "author": "Sam Okafor",
     "genre": "DIY", "price": 12.99, "year": 2018, "in_stock": True},
    {"title": "The Long Way to Orbit", "author": "Yuki Tanaka",
     "genre": "science fiction", "price": 22.95, "year": 2024, "in_stock": False},
    {"title": "Letters Never Sent", "author": "Ines Duarte",
     "genre": "romance", "price": 14.95, "year": 2021, "in_stock": True},
    {"title": "The Algorithmic Gardener", "author": "Priya Nair",
     "genre": "technology", "price": 27.50, "year": 2024, "in_stock": True},
    {"title": "Storms Over Aldermere", "author": "Henrik Solberg",
     "genre": "fantasy", "price": 23.00, "year": 2022, "in_stock": True},
]

GENRES = sorted({b["genre"] for b in BOOKS})
AUTHORS = sorted({b["author"] for b in BOOKS})


def _money(price: float) -> str:
    return f"${price:.2f}"


def _describe(book: dict) -> str:
    stock = "in stock" if book["in_stock"] else "out of stock"
    return (f"'{book['title']}' by {book['author']} "
            f"({_money(book['price'])}, {book['year']}, {stock})")


def _titles_in(question: str) -> list[dict]:
    """Books whose title is quoted in the question (exact or partial)."""
    found = []
    for book in BOOKS:
        if book["title"].lower() in question.lower():
            found.append(book)
    return found


def _quoted(question: str) -> list[str]:
    return re.findall(r"'([^']+)'", question)


def answer(question: str) -> str:
    """Rule-based stub answerer over the synthetic catalog."""
    q = question.lower()
    quoted = _quoted(question)
    titles = _titles_in(question)

    # Unknown quoted title -> honest "not found".
    if quoted and not titles:
        return f"{quoted[0]} is not in the catalog."

    # Two-title price comparison.
    if len(titles) >= 2 and ("cheaper" in q or "more expensive" in q):
        a, b = titles[0], titles[1]
        cheap, dear = (a, b) if a["price"] <= b["price"] else (b, a)
        if "cheaper" in q:
            return (f"{cheap['title']} ({_money(cheap['price'])}) is cheaper "
                    f"than {dear['title']} ({_money(dear['price'])}).")
        return (f"{dear['title']} ({_money(dear['price'])}) is more expensive "
                f"than {cheap['title']} ({_money(cheap['price'])}).")

    # "Who wrote the most/cheapest expensive book?"
    if "who wrote" in q and ("most expensive" in q or "cheapest" in q):
        book = max(BOOKS, key=lambda b: b["price"]) if "most expensive" in q \
            else min(BOOKS, key=lambda b: b["price"])
        superlative = "most expensive" if "most expensive" in q else "cheapest"
        return (f"{book['author']} wrote the {superlative} book, "
                f"'{book['title']}' ({_money(book['price'])}).")

    # Single-title detail questions.
    if len(titles) == 1:
        book = titles[0]
        if "how much" in q or "price" in q or "cost" in q:
            return f"'{book['title']}' costs {_money(book['price'])}."
        if "who wrote" in q:
            return f"{book['author']} wrote '{book['title']}'."
        if "what year" in q or "published" in q:
            return f"'{book['title']}' was published in {book['year']}."
        if "what genre" in q:
            return f"'{book['title']}' is a {book['genre']} book."
        if "in stock" in q:
            state = "is in stock" if book["in_stock"] else "is out of stock"
            return f"'{book['title']}' by {book['author']} {state}."
        return _describe(book) + "."

    # Author questions.
    for author in AUTHORS:
        if author.lower() in q:
            books = [b for b in BOOKS if b["author"] == author]
            if "in stock" in q:
                books = [b for b in books if b["in_stock"]]
            if "how many" in q:
                listed = "; ".join(_describe(b) for b in books)
                return f"There are {len(books)} books by {author}: {listed}."
            if "total" in q or "cost" in q:
                total = sum(b["price"] for b in books)
                listed = "; ".join(_describe(b) for b in books)
                return (f"The {len(books)} {author} books cost "
                        f"{_money(total)} in total: {listed}.")
            listed = "; ".join(_describe(b) for b in books)
            return f"Books by {author}: {listed}."

    # Genre questions.
    for genre in GENRES:
        if genre in q:
            books = [b for b in BOOKS if b["genre"] == genre]
            if "how many" in q:
                listed = "; ".join(_describe(b) for b in books)
                return (f"There are {len(books)} {genre} books: {listed}.")
            if "in stock" in q or "available" in q:
                in_stock = [b for b in books if b["in_stock"]]
                if not in_stock:
                    return (f"No {genre} books in stock. The only {genre} "
                            f"book, '{books[0]['title']}', is out of stock.")
                books = in_stock
            listed = "; ".join(_describe(b) for b in books)
            return f"{genre.title()} books: {listed}."

    # Price filters.
    m = re.search(r"less than \$(\d+(?:\.\d+)?)", q)
    if m:
        limit = float(m.group(1))
        books = [b for b in BOOKS if b["price"] < limit]
        listed = "; ".join(_describe(b) for b in books)
        return f"Books under {_money(limit)}: {listed}."

    # Year questions.
    m = re.search(r"published in (\d{4})", q)
    if m:
        year = int(m.group(1))
        books = [b for b in BOOKS if b["year"] == year]
        listed = "; ".join(_describe(b) for b in books)
        return f"Books published in {year}: {listed}."
    if "published before" in q:
        m = re.search(r"before (\d{4})", q)
        year = int(m.group(1)) if m else 9999
        books = [b for b in BOOKS if b["year"] < year]
        listed = "; ".join(_describe(b) for b in books)
        return f"Books published before {year}: {listed}."
    if "newest" in q:
        year = max(b["year"] for b in BOOKS)
        books = [b for b in BOOKS if b["year"] == year]
        listed = "; ".join(_describe(b) for b in books)
        return f"The newest books are from {year}: {listed}."

    # Extremes over the whole catalog.
    if "cheapest" in q:
        book = min(BOOKS, key=lambda b: b["price"])
        return (f"{book['title']} ({_money(book['price'])}) is the cheapest "
                f"book in the catalog.")
    if "most expensive" in q:
        book = max(BOOKS, key=lambda b: b["price"])
        return (f"{book['title']} ({_money(book['price'])}) is the most "
                f"expensive book in the catalog.")

    # Out-of-stock listing.
    if "out of stock" in q:
        books = [b for b in BOOKS if not b["in_stock"]]
        listed = "; ".join(_describe(b) for b in books)
        return f"Books out of stock: {listed}."

    return "I couldn't find an answer to that in the catalog."
