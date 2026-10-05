from dataclasses import dataclass, field

from random_dag import DAG, generate

EPS = 1e-9


@dataclass
class Schedule:
    proc: dict[int, int] = field(default_factory=dict)
    start: dict[int, float] = field(default_factory=dict)
    finish: dict[int, float] = field(default_factory=dict)

    def makespan(self) -> float:
        return max(self.finish.values(), default=0.0)


def finish_time(dag: DAG, schedule: Schedule, proc_free: list[float],
                pred: dict[int, list[int]], t: int, proc: int) -> tuple[float, float]:

    ready = 0.0
    for i in pred[t]:
        arrival = schedule.finish[i]
        if schedule.proc[i] != proc:
            arrival += dag.comm_cost[(i, t)]
        ready = max(ready, arrival)

    start = max(ready, proc_free[proc])
    finish = start + dag.comp_cost[t][proc]
    return start, finish


def list_schedule(dag: DAG, priority: dict[int, float] | None = None) -> Schedule:

    pred = dag.pred()
    in_degree = {t: len(pred[t]) for t in dag.succ}
    ready = [t for t in dag.succ if in_degree[t] == 0]
    proc_free = [0.0] * dag.num_procs
    schedule = Schedule()

    while ready:
        if priority is None:
            t = ready.pop(0)
        else:
            t = max(ready, key=lambda task: priority[task])
            ready.remove(t)

        best_proc, best_start, best_finish = 0, 0.0, float("inf")
        for proc in range(dag.num_procs):
            start, finish = finish_time(dag, schedule, proc_free, pred, t, proc)
            if finish < best_finish:
                best_proc, best_start, best_finish = proc, start, finish

        schedule.proc[t] = best_proc
        schedule.start[t] = best_start
        schedule.finish[t] = best_finish
        proc_free[best_proc] = best_finish

        for v in dag.succ[t]:
            in_degree[v] -= 1
            if in_degree[v] == 0:
                ready.append(v)

    return schedule


def check(dag: DAG, schedule: Schedule) -> None:

    assert set(schedule.proc) == set(dag.succ), "every task must be scheduled"

    for t in dag.succ:
        p = schedule.proc[t]
        assert 0 <= p < dag.num_procs, f"task {t} on unknown processor {p}"
        expected = schedule.start[t] + dag.comp_cost[t][p]
        assert abs(schedule.finish[t] - expected) < EPS, f"task {t} has a wrong duration"

    for i in dag.succ:
        for j in dag.succ[i]:
            arrival = schedule.finish[i]
            if schedule.proc[i] != schedule.proc[j]:
                arrival += dag.comm_cost[(i, j)]
            assert schedule.start[j] >= arrival - EPS, f"task {j} starts before data from {i} arrives"

    for p in range(dag.num_procs):
        tasks = sorted((t for t in dag.succ if schedule.proc[t] == p), key=lambda t: schedule.start[t])
        for a, b in zip(tasks, tasks[1:]):
            assert schedule.start[b] >= schedule.finish[a] - EPS, f"tasks {a} and {b} overlap on processor {p}"


if __name__ == "__main__":
    example = DAG(
        succ={0: [1, 2], 1: [3], 2: [3], 3: []},
        comp_cost={0: [2, 3], 1: [3, 1], 2: [4, 4], 3: [2, 3]},
        comm_cost={(0, 1): 1, (0, 2): 2, (1, 3): 3, (2, 3): 1},
        num_procs=2,
    )
    s = list_schedule(example)
    check(example, s)
    for t in sorted(s.proc):
        print(f"task {t}: P{s.proc[t]}  [{s.start[t]:g}, {s.finish[t]:g}]")
    print("makespan:", s.makespan())

    for seed in range(100):
        dag = generate(n=50, alpha=1.0, p=0.1, num_procs=4, ccr=1.0, beta=0.5, seed=seed)
        check(dag, list_schedule(dag))
    print("100 random DAGs: ok")
