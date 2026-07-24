from neo4j import GraphDatabase, Driver
from app.core.config import settings
from typing import Optional

class Neo4jConnector:
    def __init__(self):
        self._driver: Optional[Driver] = None

    def connect(self):
        """Initializes the Neo4j driver instance."""
        if not self._driver:
            self._driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
            )

    def close(self):
        """Closes the Neo4j driver connection pool."""
        if self._driver:
            self._driver.close()
            self._driver = None

    def get_driver(self) -> Driver:
        if not self._driver:
            self.connect()
        return self._driver

neo4j_connector = Neo4jConnector()