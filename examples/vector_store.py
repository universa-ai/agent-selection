"""
This module demonstrates how you can store data to a vector storage. 
Currently, we have support for ChromaDB, and it can be utilized to store 
embeddings of data using any embedding function.

This examples showcases how you can use ChromaDB using our provided default
embedding function. Please refer to the official ChromaDB documentation to
learn more about different methods to storing and querying data.
"""

import examples._import_root as _import_root  # noqa : E402
import uuid

from universa.memory.chromadb.chromadb import ChromaDB
from universa.memory.embedding_functions.chromadb_default import ChromaDBDefaultEF


if __name__ == "__main__":

    agent1_description = " ".join([
        "This is an advanced AI agent designed to simplify",
        "and accelerate the development of full stack web applications.", 
        "With proficiency in core web technologies such as JavaScript,",
        "CSS, and HTML, It empowers users to create dynamic, responsive,",
        "and visually appealing web applications. Whether you are a",
        "novice looking to build your first website or an experienced",
        "developer seeking to automate repetitive tasks, it provides the",
        "tools and expertise to bring your web development projects to life."
    ])

    agent2_description = " ".join([
        "TravelPlanner is an intelligent AI agent designed to help you plan",
        "and organize your trips effortlessly. Whether you're dreaming of",
        "a beach vacation, a cultural tour, or an adventurous getaway,",
        "TravelPlanner takes the hassle out of travel planning, making your",
        "journey smooth and enjoyable.\n\n",
        "TravelPlanner acts as your personal travel assistant, guiding you",
        "through every step of the planning process. From finding the best",
        "destinations to booking flights, accommodations, and activities,",
        "TravelPlanner ensures that every detail of your trip is well taken care of."
    ])
    
    # Create an instance of ChromaDB
    chroma = ChromaDB(
        embedding_function=ChromaDBDefaultEF(),
        collection_name="example_collection"
    )
    print("Collection size: ", chroma.collection.count()) # 0 - no data in the collection

    # Add data to the collection
    chroma.add_data(
        documents=[agent1_description, agent2_description],
        ids=[str(uuid.uuid4()), str(uuid.uuid4())]
    )
    print("Collection size: ", chroma.collection.count()) # 2 - added two descriptions

    # Query the data using a task related to web development
    print(">> Querying data related to web development\n")
    result = chroma.query_data(
        ["Create a layout for the landing page of the website."], 
    )
    print(result['documents'][0]) 

    # Query the data using a task related to travel planning
    print("\n>> Querying data related to travel planning\n")
    result = chroma.query_data(
        ["Research and Select Destinations"]
    )
    print(result['documents'][0])
