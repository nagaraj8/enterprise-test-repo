from neo4j import GraphDatabase

uri = 'bolt://localhost:7687'
username = 'neo4j'
password = 'password'


driver = GraphDatabase.driver(
    uri,
    auth=(username, password)
)

with driver.session() as session:
    result = session.run('RETURN 1 AS number')

    for record in result:
        print(record['number'])