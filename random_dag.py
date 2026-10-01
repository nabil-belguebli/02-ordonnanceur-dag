import random
from collections import deque
from dataclasses import dataclass
from math import sqrt

def topological_sort(graph: dict[int, list[int]]) -> list[int]:

    in_degree: dict[int, int] = {}
    for node in graph:
        in_degree.setdefault(node, 0)
        for v in graph[node]:
            in_degree[v] = in_degree.get(v, 0) + 1

    order: list[int] = []

    queue = deque()
    for node in in_degree:
        if in_degree[node] == 0:
            queue.append(node)

    while queue:
        node = queue.popleft()
        order.append(node)
        for v in graph.get(node, []):
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)

    if len(order) < len(in_degree):
        raise ValueError("graph contains a cycle")

    return order


def easy_random_dag(n: int, p: float, seed: int) -> dict[int, list[int]]:

    dag: dict[int, list[int]] = {}
    rng = random.Random(seed)

    for i in range(n):
        dag[i] = []
        for j in range(i + 1, n):
            if rng.random() < p:
                dag[i].append(j)

    return dag


def random_dag(n: int, alpha: float, p: float, seed: int) -> dict[int, list[int]]:

    rng = random.Random(seed)
    width = sqrt(n) * alpha

    sizes: list[int] = []
    placed = 0
    while placed < n:
        size = rng.randint(1, max(1, round(2 * width - 1)))
        size = min(size, n - placed)
        sizes.append(size)
        placed += size

    layers: list[list[int]] = []
    next_id = 0
    for size in sizes:
        layers.append(list(range(next_id, next_id + size)))
        next_id += size

    dag: dict[int, list[int]] = {i: [] for i in range(n)}

    for k in range(1, len(layers)):
        for j in layers[k]:
            parent = rng.choice(layers[k - 1])
            dag[parent].append(j)

    for k in range(len(layers)):
        for i in layers[k]:
            for upper in layers[k + 1:]:
                for j in upper:
                    if j not in dag[i] and rng.random() < p:
                        dag[i].append(j)

    return dag


def comp_costs(num_procs: int,avg_cost:float, seed: int, beta: float, n: int)-> dict[int, list[float]]:
    rng = random.Random(seed) 
    comp_cost = {}

    for t in range(n):
        mean_cost = rng.uniform(1,2*avg_cost)
        costs = []
        for i in range(num_procs):
            real_cost = rng.uniform(mean_cost * (1 - beta/2), mean_cost * (1 + beta/2))
            costs.append(real_cost)
   
        comp_cost[t] = costs



    return comp_cost

def comm_costs(seed:int, random_graph:dict[int, list[int]], ccr:float, avg_cost:float)->dict[tuple[int, int], float]:
    #ccr = communication to computation ratio 
    rng = random.Random(seed) 
    comm_cost = {}
    for i in random_graph:
        for j in random_graph[i]:
            cost = rng.uniform(0,2*ccr*avg_cost)
            comm_cost[(i,j)] = cost

    return comm_cost


@dataclass
class DAG:
    succ: dict[int, list[int]]
    comp_cost: dict[int, list[float]]
    comm_cost: dict[tuple[int, int], float]
    num_procs: int

    def pred(self) -> dict[int, list[int]]:
        pred: dict[int, list[int]] = {t: [] for t in self.succ}
        for i in self.succ:
            for j in self.succ[i]:
                pred[j].append(i)
        return pred


def generate(n: int, alpha: float, p: float, num_procs: int,
             ccr: float, beta: float, seed: int, avg_cost: float = 10) -> DAG:

    rng = random.Random(seed)
    graph_seed = rng.getrandbits(32)
    comp_seed = rng.getrandbits(32)
    comm_seed = rng.getrandbits(32)

    succ = random_dag(n, alpha, p, graph_seed)
    comp_cost = comp_costs(num_procs, avg_cost, comp_seed, beta, n)
    comm_cost = comm_costs(comm_seed, succ, ccr, avg_cost)

    return DAG(succ, comp_cost, comm_cost, num_procs)
