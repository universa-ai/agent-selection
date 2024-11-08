<div align="center">
<h1>Agent Selection Challenge</h1>

<h3>Deadline for submission: 11.11.24 23:59 CET</h3>
<h4>Submit codebase via <a href="mailto:challenge@universa.org">official email</a</h4>
</div>

---

> [!IMPORTANT]
> Deadline is near! Please follow the [Submission](#submission) instructions to submit your solution.

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

Each agent is provided with several additional attributes to help you get started:
* `response_time` - Average time in seconds that takes for the model to respond to a query
* `input_cost` - Average cost in USD of processing a query ($ per 1M tokens)
* `output_cost` - Average cost in USD of generating a response ($ per 1M tokens)
* `popularity` - Number of queries that the agent has received (from human users and other agents)
* `rated_responses` - Number of responses that the agent has received a rating for from human users
* `average_rating` - Average rating of the agent's responses (from 1 to 10)

Except for these attributes, each agent has a `description`, `name` and `system_prompt`.

For the sake of this challenge, you can only use these parameters in your selection algorithm.

## Criteria

The solutions to this challenge will be assessed based on the following criteria:
* **Accuracy of agent selection** - How accurately the best available agents are chosen for the given query?
* **Speed of agent extraction** - How quick the selection of an agent happens?
* **Efficiency of the system** - How much computational cost is required to perform the agent selection?
* **Code clarity and compatibility** - How well the code is structured and whether it is compatible with the provided codebase?

As the network grows, the number of agents will increase, making the selection process more complex. It is important to acknowledge the limitations and difficulties that this brings to the table, namely:
* **New agents** - How to make sure that new agents have a chance to be chosen? If our ranking algorithm promotes agents that receive the best ratings or biggest number of queries, how to acknowledge new agents and give them a head start?
* **Efficiency of scale** - How to make sure that the system is efficient as the number of agents grows? If our ranking system needs to recalculate the relations between agents each time we add a new agent to the group, this will greatly hinder the system's scalability. How to prevent that from happening?

## Codebase

This repository contains parts of Universa AI codebase that will be needed to complete the challenge. Most of the methods and classes that are implemented contain detailed docstring that will help you understand their function.

In order to see a few basic examples that will get you going, follow the provided [examples](./examples).

You can find documentation on more complex parts of the codebase in the [docs](./docs) directory.

## Case studies

To build a better intuition for this challenge, we encourage you to go through the [`CASE_STUDIES.md`](./CASE_STUDIES.md) document.

## Submission

Your solution should be submitted either as a .zip archive or a link to a GitHub repository. Please mind that we will be assessing solutions based on the following criteria:
* **Benchmark results** - How your algorithm performed on the provided [benchmark](./benchmark) and how much time it took for it to run
* **Code clarity & quality** - Structure, clarity and ingenuity of your code
* **Report** - A report containing your thoughts on the challenge, the approach you took and describing clearly your solution (report can be contained in the README.md of your repository)

We also encourage you to provide your own becnhamrking examples that showcase the quality of the result.

Good luck! :tada:

## Contact

Discussions are open on our repository - whether you need some quick help, want to share your thoughts or just connect with other developers, jump in [here](https://github.com/universa-ai/agent-selection/discussions) and let's talk!

You can also reach us out at [challenge@universa.org](mailto:challenge@universa.org)
