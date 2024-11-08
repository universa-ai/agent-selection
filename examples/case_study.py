"""
This script shows how the case studies (see README.md) was calculated.
"""

import _import_root  # noqa : E402
import uuid

from universa.memory.chromadb.chromadb import ChromaDB
from universa.memory.embedding_functions.chromadb_default import ChromaDBDefaultEF


if __name__ == "__main__":

    ## Missing the best agent
    print(">> Missing the best agent\n")
    agent_descriptions = [
        "A blogger specializing in Node.js, building API services and PostgreSQL databases.",
        "A Python programmer skilled in developing API services and implementing user authorization and authorization endpoints.",
        "A JavaScript engineer experienced in constructing web APIs and managing data with PostgreSQL.",
        "A Node.js specialist proficient in creating web services and handling user authentication and authorization with JWT.",
        "An ExpressJS specialist, developing web APIs and using PostgreSQL databases.",
        "A Node.js and ExpressJS expert with a background in developing API services with PostgreSQL."
    ]
    
    # Create an instance of ChromaDB
    chroma = ChromaDB(
        embedding_function=ChromaDBDefaultEF(),
        collection_name="example_collection"
    )

    # Add data to the collection
    chroma.add_data(
        documents=agent_descriptions,
        ids=[str(uuid.uuid4()) for _ in range(len(agent_descriptions))]
    )

    # Query the data using a task related to web development
    result = chroma.query_data(
        ["Create an API of a blog app in which users can create, read, update, and delete posts."
         " The API should be built using Node.js and ExpressJS and should interact with a PostgreSQL database."
         " Implement user authentication and authorization for creating and managing posts."], 
    )
    for doc, score in zip(result["documents"][0], result["distances"][0]):
        print(f"Distance: {round(score, 2)}\tDocument: {doc}")

    ## Understanding the network
    print("\n>> Understanding the network\n")
    agent_descriptions = [
        "A JavaScript engineer experienced in constructing web APIs and managing data with PostgreSQL",
        "A Node.js specialist proficient in creating web services and handling user authentication and authorization with JWT",
        "An ExpressJS specialist, developing web APIs and using PostgreSQL databases",
        "A Node.js and ExpressJS expert with a background in developing API services with PostgreSQL"
    ]
    agent_weights = [0.28, 0.41, 0.35, 0.77]

    # Create a new instance of ChromaDB
    chroma = ChromaDB(
        embedding_function=ChromaDBDefaultEF(),
        collection_name="example_collection"
    )

    # Add data to the collection
    ids = [str(uuid.uuid4()) for _ in range(len(agent_descriptions))]
    chroma.add_data(
        documents=agent_descriptions,
        ids=ids
    )

    # Query the data using a task related to web development
    result = chroma.query_data(
        ["Create an API of a blog app in which users can create, read, update, and delete posts."
         " The API should be built using Node.js and ExpressJS and should interact with a PostgreSQL database."
         " Implement user authentication and authorization for creating and managing posts."], 
    )
    adjusted_scores = []
    for doc, score, _id in zip(result["documents"][0], result["distances"][0], result["ids"][0]):
        which_agent = ids.index(_id)
        adjusted_scores.append(agent_weights[which_agent] * score)
        print(f"Distance: {round(score, 2)}\tWeight: {agent_weights[which_agent]}\tDocument: {doc}")

    # Print results again, but taking an average of weight and distance
    sorted_documents = sorted(zip(result["documents"][0], adjusted_scores), key=lambda x: x[1], reverse=True)
    print()
    for scored_doc, distance in zip(sorted_documents, result["distances"][0]):
        doc, score = scored_doc
        print(f"Adjusted score: {round(score, 2)}\tDistance: {distance}\tDocument: {doc}")
