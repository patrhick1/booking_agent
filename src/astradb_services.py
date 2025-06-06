"""Thin wrapper for AstraDB service. GmailService and SlackService are commented out pending implementation."""

import os
from typing import List
from astrapy import DataAPIClient

from utils import generate_embedding, decode_embedding


class AstraDBService:

    def __init__(self):
        token = os.getenv("ASTRA_DB_TOKEN")
        if not token:
            raise ValueError("ASTRA_DB_TOKEN is not set")
        endpoint = os.getenv("ASTRA_DB_ENDPOINT")
        if not endpoint:
            raise ValueError("ASTRA_DB_ENDPOINT is not set")
        keyspace = os.getenv("ASTRA_DB_KEYSPACE")
        client = DataAPIClient(token)
        self.db = client.get_database_by_api_endpoint(endpoint,
                                                      keyspace=keyspace)
        collection_name = os.getenv("ASTRA_DB_COLLECTION")
        if not collection_name:
            raise ValueError("ASTRA_DB_COLLECTION is not set")
        self.collection = self.db.get_collection(collection_name)

    def fetch_threads(self, query: str, top_k: int = 2) -> List[str]:
        """
        Fetch relevant email threads from AstraDB matching the vector query.
        """
        vector = generate_embedding(query)
        collection = self.get_collection()
        cursor = collection.find({}, sort={"$vector": vector})
        threads: List[str] = []
        for i, doc in enumerate(cursor):
            if i >= top_k:
                break
            threads.append(doc.get("email_thread"))
        return threads

    def get_collection(self):
        """
        Get the default collection handle from AstraDB.
        """
        return self.collection

    def insert_document(self, document: dict):
        """
        Insert a document into the specified AstraDB collection.
        Expected document keys: sender, client, email_thread, description, $vector.
        """
        required_fields = {
            "sender", "client", "email_thread", "description", "$vector"
        }
        missing = required_fields - set(document.keys())
        if missing:
            raise ValueError(f"Document missing required fields: {missing}")
        collection = self.get_collection()
        return collection.insert_one(document)
