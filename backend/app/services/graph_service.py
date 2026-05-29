from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    'bolt://localhost:7687',
    auth=('neo4j', 'password')
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