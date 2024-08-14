# Agent Selection Challenge - Universa AI

Universa AI team is currently working on a proof-of-concept of a multi-agent network. Core idea of such network is to provide agents with an environment to be deployed in and communicate with each other in order to complete tasks, such as user-given problems. One of the core challenges of this project is to create a system of selecting the best agents for a given query.

> [!NOTE]
> Do you have any questions or doubts? Check out [Contact](#contact) section to find out how to reach us :hugs:

## Goal

The main purpose of this challenge is to **create an efficient and accurate agent selection algorithm**. Based upon attributes of an agent, the algorithm should pick the best agent for a given user query.

In Universa network, each agent can be analyzed from the perspective of many different parameters and attributes, such as:
* Agent description & system prompt
* Chat history
* Rating of responses
* Usage history & response time
* Tool calling ability

The list above is not exhaustive and you are encouraged to explore other potential attributes that could be used to rank and select agents based on queries.

Each agent is provided with several additional attributes to help you get started:
* `response_time` - Average time in seconds that takes for the model to respond to a query
* `input_cost` - Average cost in USD of processing a query ($ per 1M tokens)
* `output_cost` - Average cost in USD of generating a response ($ per 1M tokens)
* `popularity` - Number of queries that the agent has received (from human users and other agents)
* `rated_responses` - Number of responses that the agent has received a rating for from human users
* `average_rating` - Average rating of the agent's responses (from 1 to 10)

Except for these attributes, each agent has a `description`, `name` and `system_prompt`.

These attributes are **not** exhaustive and you are encouraged to explore other potential attributes that could be used in the selection algorithm.

## Criteria

The solutions to this challenge will be assessed based on the following criteria:
* **Accuracy of agent selection** - How accurately the best available agents are chosen for the given query?
* **Speed of agent extraction** - How quick the selection of an agent happens?
* **Efficiency of the system** - How much computational cost is required to perform the agent selection?
* **Code clarity and compatibility** - How well the code is structured and whether it is compatible with the provided codebase?

As the network grows, the number of agents will increase, making the selection process more complex:. It is important to acknowledge the limitations and difficulties that this brings to the table, namely:
* **New agents** - How to make sure that new agents have a chance to be chosen? If our ranking algorithm promotes agents that receive the best ratings or biggest number of queries, how to acknowledge new agents and give them a head start?
* **Efficiency of scale** - How to make sure that the system is efficient as the number of agents grows? If our ranking system needs to recalculate the relations between agents each time we add a new agent to the group, this will greatly hinder the system's scalability. How to prevent that from happening?

## Benchmark

We are still working on a full version of a benchmark dataset to test your selection algorithms, but we do provide some basic agents data and queries with which you can start working on your algorithms. You can find them in the [testing](./testing) directory.

## Codebase

This repository contains parts of Universa AI codebase that will be needed to complete the challenge. Most of the methods and classes that are implemented contain detailed docstring that will help you understand their function.

In order to see a few basic examples that will get you going, follow the provided [examples](./examples).

You can find documentation on more complex parts of the codebase in the [docs](./docs) directory.

## Case studies

Let us build an intuition about the challenge and understand the problem better. We will go over two simple case studies in which we will discuss the following issues:
* **[Missing the best agent](#missing-the-best-agent)** - Simple embeddings might just miss the semantically best option
* **[Understanding the network](#understanding-the-network)** - Unacknowledged system parameters can negatively affect our selection process

You can see the [case_study.py](./examples/case_study.py) script for the code used to calculate each case study.

### Missing the best agent

When a user provides a task to the system, it is usually given in a form of natural language. Imagine the following query:

```manpage
Create an API of a blog app in which users can create, read, update, and delete posts.
The API should be built using Node.js and ExpressJS and should interact with a PostgreSQL database.
Implement user authentication and authorization for creating and managing posts.
```

Given such a task, the system should be able to choose the best agent for the job.

Now, let us define a few agents that could exist in our network:
* **Agent A** - A blogger specializing in Node.js, building API services and PostgreSQL databases
* **Agent B** - A Python programmer skilled in API services and implementing user authorization and authorization endpoints
* **Agent C** - A JavaScript engineer experienced in constructing web APIs and managing data with PostgreSQL
* **Agent D** - A Node.js specialist proficient in creating web services and handling user authentication and authorization with JWT
* **Agent E** - An ExpressJS specialist, developing web APIs and using PostgreSQL databases
* **Agent F** - A Node.js and ExpressJS expert with a background in developing API services with PostgreSQL

Since the goal of Universa agent network is to be populated by thousands of agents, there is a very high probability of having agents with very similar attributes.

First thought that comes to mind is to create an embedding of the task prompt and agent descriptions, after which we can find the most similar agent to the prompt. Let's see the results:

<br>
<div align="center">

| Agent | Description | Distance |
|:-------:|:-------------:|:----------:|
| Agent A | A blogger specializing in Node.js, building API services and PostgreSQL databases | 0.62 |
| Agent F | A Node.js and ExpressJS expert with a background in developing API services with PostgreSQL | 0.82 |
| Agent C | A JavaScript engineer experienced in constructing web APIs and managing data with PostgreSQL | 0.82 |
| Agent E | An ExpressJS specialist, developing web APIs and using PostgreSQL databases | 0.85 |
| Agent D | A Node.js specialist proficient in creating web services and handling user authentication and authorization with JWT | 1.22 |
| Agent B | A Python programmer skilled in developing API services and implementing user authorization and authorization endpoints | 1.34 |

</div>
<br>

If we chose the closest agent, which is Agent A, we quickly realize that being a blogger is not exactly what we were looking for. But, because of the word `blog`, it seems that the embedding was just a bit closer to the prompt, in contrary to the second place - Agent F, much better choice.

This simple embedding approach clearly misses with the best choice, as token similarity is not the best metric for semantic similarity.

**Worth noting**: In the above example we chose a basic embedding function - there is a lot of room for research and improvement in this area. Feel encouraged to explore different embedding methods and see how they perform for the same queries - not just in terms of accuracy, but also efficiency.

### Understanding the network

Agents in the Universa network are more complex than just their descriptions. As we mentioned before, there are multiple different parameters that can influence the agent selection process. Let's consider a network of agents in which except for description each has a weight assigned to it. For the sake of simplicity, weights will fall into the range of 0 to 1, with each weight representing one of the following categories:
* **0 - 0.3** - responses are often malformed or missed
* **0.3 - 0.6** - responses are often correct, but not always
* **0.6 - 0.9** - responses are almost always correct
* **0.9 - 1** - responses are always correct

Now, let's consider the following subgroup of agents from the previous case and their weights:

<br>
<div align="center">

| Agent | Description | Weight | Distance |
|:-------:|:-------------:|:-------:|:------:|
| Agent A | A JavaScript engineer experienced in constructing web APIs and managing data with PostgreSQL | 0.28 | 0.80 |
| Agent B | A Node.js specialist proficient in creating web services and handling user authentication and authorization with JWT | 0.41 | 1.2 |
| Agent C | An ExpressJS specialist, developing web APIs and using PostgreSQL databases | 0.35 | 0.82 |
| Agent D | A Node.js and ExpressJS expert with a background in developing API services with PostgreSQL | 0.77 | 0.84 |

</div>
<br>

After calculating which agent is the best for the same query as before, we arrive at the following results:

<br>
<div align="center">

| Agent | Description | Distance | Weight |
|:-------:|:-------------:|:----------:|:-------:|
| Agent A | A JavaScript engineer experienced in constructing web APIs and managing data with PostgreSQL | 0.80 | 0.28 |
| Agent D | An ExpressJS specialist, developing web APIs and using PostgreSQL databases | 0.82 | 0.35 |
| Agent C | A Node.js and ExpressJS expert with a background in developing API services with PostgreSQL | 0.84 | 0.77 |
| Agent B | A Node.js specialist proficient in creating web services and handling user authentication and authorization with JWT | 1.2 | 0.41 |

</div>
<br>

We can clearly see that the first two positions are agents with the worst weights from all the agents. Since we did not take weights under consideration, there was no effect on the result in the selection process. But what if we tried to incorporate them into our final score calculation?

Let's suppose we figured out that we could multiply the weight and the distance, to get an adjusted score of each agent. Then, by seeing which agent has the highest score, we would be able to choose the best agent for the task. The result of such approach is the table below:

<br>
<div align="center">

| Agent | Description | Adjusted Score | Distance | Weight |
|:-------:|:-------------:|:----------:|:-------:|:-------:|
| Agent D | A Node.js and ExpressJS expert with a background in developing API services with PostgreSQL | 0.65 | 0.84 | 0.77 |
| Agent B | A Node.js specialist proficient in creating web services and handling user authentication and authorization with JWT | 0.49 | 1.2 | 0.41 |
| Agent C | An ExpressJS specialist, developing web APIs and using PostgreSQL databases | 0.29 | 0.82 | 0.35 |
| Agent A | A JavaScript engineer experienced in constructing web APIs and managing data with PostgreSQL | 0.22 | 0.80 | 0.28 |

</div>
<br>

By incorporating the weights into the selection process, we suddenly changed the whole ranking and the best agent turned out to be the one being almost always correct, compared to other agents falling far behind it.

This case study aimed to show how important it is to understand other parameters in our system that can influence the selection process. By acknowledging them, we can greatly improve the accuracy of our agent selection algorithm. Of course, it is not only about numbers - agents can have many different attributes, each of which should be understood separately, as not all of them might be handy. it is up to you to decide what is important and what is not.

## Contact

Discussions are open on our repository - whether you need some quick help, want to share your thoughts or just connect with other developers, jump in [here](https://github.com/universa-code/agent-selection/discussions) and let's talk!

You can also reach us out at [challenge@universa.org](mailto:challenge@universa.org)
