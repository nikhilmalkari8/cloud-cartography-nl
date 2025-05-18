from neo4j import GraphDatabase

# Neo4j connection details
uri = "bolt://localhost:7690"  # Use the correct port
username = "neo4j"             # Default username
password = "ssrtLvuf43123!"       # Use the password you set

# Try to connect
try:
    print(f"Attempting to connect to Neo4j at {uri} with user {username}")
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    # Test connection with a simple query
    with driver.session() as session:
        result = session.run("RETURN 'Connection successful' as message")
        message = result.single()[0]
        print(message)
    
    # Close the driver
    driver.close()
    print("Connection closed successfully")
    
except Exception as e:
    print(f"Error connecting to Neo4j: {type(e).__name__}: {str(e)}")