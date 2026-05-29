from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
    auth=(
        os.getenv('NEO4J_USER', 'neo4j'),
        os.getenv('NEO4J_PASSWORD', '')
    )
)

def create_event_node(actor, action):
    with driver.session() as session:
        session.run(
            '''
            CREATE (e:Event {
                actor: $actor,
                action: $action
            })
            ''',
            actor=actor,
            action=action
        )
