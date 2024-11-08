# Benchmark

In order to test your agent selection algorithms, we provide a benchmark with a set of queries and a set of agents to run your selection algorithm on.

Please see `ExampleAlgorithm` in [`selection.py`](./selection.py) for an example of how to implement the provided interface for selection algorithms.

Your algorithm code should be able to run with the following snippet:

```python
# Example usage
benchmark = Benchmark()
algorithm = YourAlgorithm(benchmark.agents, benchmark.agent_ids)
result = benchmark.validate(algorithm, verbose=True)
```

It is highly encouraged for a each solution to provide **any** benchmark result in the report and a proper implementation of the `SelectionAlgorithm` interface.
