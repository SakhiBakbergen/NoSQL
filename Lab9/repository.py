from pymongo import MongoClient
from typing import List, Optional

class BookRepository:
    def __init__(self, uri: str, db_name: str):
        self.client = MongoClient(uri, serverSelectionTimeoutMS=3000)
        self.db = self.client[db_name]
        self.collection = self.db['books']
        self.collection.create_index("isbn", unique=True)

    def create(self, data: dict) -> dict:
        self.collection.insert_one(data)
        return self.get_by_isbn(data['isbn'])

    def get_by_isbn(self, isbn: str) -> Optional[dict]:
        return self.collection.find_one({"isbn": isbn}, {"_id": 0})

    def get_all(self, author: Optional[str] = None, category: Optional[str] = None) -> List[dict]:
        query = {}
        if author:
            query["author"] = {"$regex": author, "$options": "i"}
        if category:
            query["category"] = {"$regex": category, "$options": "i"}
        return list(self.collection.find(query, {"_id": 0}))

    def update(self, isbn: str, data: dict) -> Optional[dict]:
        update_data = {k: v for k, v in data.items() if v is not None}
        if not update_data:
            return self.get_by_isbn(isbn)
        result = self.collection.update_one({"isbn": isbn}, {"$set": update_data})
        if result.matched_count == 0:
            return None
        return self.get_by_isbn(isbn)

    def delete(self, isbn: str) -> bool:
        result = self.collection.delete_one({"isbn": isbn})
        return result.deleted_count > 0