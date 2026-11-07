import config
from repository import BookRepository

repo = BookRepository(config.MONGODB_URI, config.DB_NAME)

sample_books = [
    {"isbn": "978-0141439518", "title": "Pride and Prejudice", "author": "Jane Austen", "category": "Classic", "year": 1813, "price": 12.99},
    {"isbn": "978-0451524935", "title": "1984", "author": "George Orwell", "category": "Dystopian", "year": 1949, "price": 10.50},
    {"isbn": "978-0061120084", "title": "To Kill a Mockingbird", "author": "Harper Lee", "category": "Classic", "year": 1960, "price": 14.00},
    {"isbn": "978-0345391803", "title": "The Hitchhiker's Guide to the Galaxy", "author": "Douglas Adams", "category": "Sci-Fi", "year": 1979, "price": 11.20},
    {"isbn": "978-0743273565", "title": "The Great Gatsby", "author": "F. Scott Fitzgerald", "category": "Classic", "year": 1925, "price": 15.00},
    {"isbn": "978-0451457998", "title": "Dune", "author": "Frank Herbert", "category": "Sci-Fi", "year": 1965, "price": 18.50},
    {"isbn": "978-0385490818", "title": "The Handmaid's Tale", "author": "Margaret Atwood", "category": "Dystopian", "year": 1985, "price": 13.40},
    {"isbn": "978-0618640157", "title": "The Fellowship of the Ring", "author": "J.R.R. Tolkien", "category": "Fantasy", "year": 1954, "price": 22.00},
    {"isbn": "978-0307474278", "title": "The Da Vinci Code", "author": "Dan Brown", "category": "Thriller", "year": 2003, "price": 9.99},
    {"isbn": "978-0140283334", "title": "The Catcher in the Rye", "author": "J.D. Salinger", "category": "Classic", "year": 1951, "price": 11.00},
    {"isbn": "978-0547928227", "title": "The Hobbit", "author": "J.R.R. Tolkien", "category": "Fantasy", "year": 1937, "price": 16.80},
    {"isbn": "978-0143105954", "title": "Moby-Dick", "author": "Herman Melville", "category": "Classic", "year": 1851, "price": 14.50},
    {"isbn": "978-0307277671", "title": "The Road", "author": "Cormac McCarthy", "category": "Post-Apocalyptic", "year": 2006, "price": 12.00},
    {"isbn": "978-0553293357", "title": "Foundation", "author": "Isaac Asimov", "category": "Sci-Fi", "year": 1951, "price": 10.99},
    {"isbn": "978-1400033416", "title": "Beloved", "author": "Toni Morrison", "category": "Classic", "year": 1987, "price": 13.99}
]

for book in sample_books:
    try:
        repo.create(book)
    except Exception:
        pass

print("15 книг успешно загружены в MongoDB.")