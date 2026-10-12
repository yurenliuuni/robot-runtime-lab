"""Event-driven, non-preemptive atomic robot/resource scheduler.

The event heap holds only arrivals and completions. All events at a timestamp
are processed before dispatch; completions at the horizon count as completed.
No policy can inspect future jobs. Durations are perfectly known in this model.
"""
from dataclasses import dataclass, asdict
import heapq
import math
import random
from statistics import mean

SPEEDS = ({"move": 1.6, "local": 1.2},
          {"inspect": 1.5, "local": 1.0},
          {"move": 1.0, "inspect": .9, "transfer": 1.1, "local": .8})
ROBOT_NAMES = ("carrier", "inspector", "generalist")
RESOURCES = {"move": ("corridor",), "inspect": ("station",),
             "transfer": ("corridor", "station"), "local": ()}
MIXES = {"balanced": (.35, .30, .15, .20),
         "bottleneck": (.65, .10, .15, .10),
         "local_heavy": (.15, .15, .10, .60)}
RATES = {"low": .10, "medium": .22, "high": .40}
BASE_POLICIES = ("fifo", "spt", "edf", "resource_aware", "resource_aware_v2")
POLICIES = BASE_POLICIES + ("resource_aware_v3",)


@dataclass(frozen=True)
class Job:
    id: int
    arrival: float
    kind: str
    work: float
    deadline: float


def duration(job, robot):
    return job.work / SPEEDS[robot][job.kind]


def generate(seed, mix="balanced", rate=.22, horizon=480):
    if mix not in MIXES or not math.isfinite(rate) or rate <= 0:
        raise ValueError("unknown mix or invalid arrival rate")
    if not math.isfinite(horizon) or horizon <= 0:
        raise ValueError("horizon must be finite and positive")
    rng, jobs, now = random.Random(seed), [], 0.0
    while True:
        now += rng.expovariate(rate)
        if now >= horizon:
            break
        kind = rng.choices(tuple(RESOURCES), MIXES[mix])[0]
        work = rng.uniform(4, 12) * (3 if rng.random() < .15 else 1)
        fastest = work / max(s[kind] for s in SPEEDS if kind in s)
        jobs.append(Job(len(jobs), now, kind, work,
                        now + fastest * rng.uniform(1.5, 4)))
    return jobs


def dispatch(waiting, idle, free, now, policy):
    """Return (job,robot) pairs without mutating the simulation state."""
    def feasible(j, r):
        return j.kind in SPEEDS[r] and set(RESOURCES[j.kind]) <= free

    if not policy.startswith("resource_aware"):
        chosen, pool, available, resources = [], list(waiting), set(idle), set(free)
        while available:
            candidates = []
            for j in pool:
                robots = [r for r in available if feasible(j, r)
                          and set(RESOURCES[j.kind]) <= resources]
                if not robots:
                    continue
                r = min(robots, key=lambda r: (duration(j, r), r))
                key = {"fifo": j.arrival, "spt": duration(j, r), "edf": j.deadline}[policy]
                candidates.append((key, j.arrival, j.id, r, j))
            if not candidates:
                break
            _, _, _, r, j = min(candidates)
            chosen.append((j, r))
            pool.remove(j)
            available.remove(r)
            resources.difference_update(RESOURCES[j.kind])
        return chosen

    def cost(j, r):
        d = duration(j, r)
        urgency = 2 * max(0, now + d - j.deadline) if policy.endswith("v2") else 0
        if policy.endswith("v3"):
            # Only rescue jobs that can still meet their deadline. Bound the
            # bonus by one service duration; overdue jobs retain ordinary aging.
            slack = j.deadline - now - d
            urgency = max(0, d - slack) if slack >= 0 else 0
        return d - .5 * (now - j.arrival) - urgency

    # At most two other selected jobs can occupy candidate IDs. Retaining the
    # best three per identical resource signature is sufficient for this fleet.
    candidates = {}
    for r in sorted(idle):
        groups = {}
        for j in waiting:
            if feasible(j, r):
                groups.setdefault(RESOURCES[j.kind], []).append(j)
        candidates[r] = [j for group in groups.values()
                         for j in sorted(group, key=lambda j: (cost(j, r), j.id))[:3]]
    robots, best, best_key = sorted(idle), [], (1,)

    def search(i, pairs, used_ids, used_resources, score):
        nonlocal best, best_key
        if i == len(robots):
            key = (-len(pairs), score, tuple((r, j.id) for j, r in pairs))
            if key < best_key:
                best_key, best = key, list(pairs)
            return
        r = robots[i]
        search(i + 1, pairs, used_ids, used_resources, score)
        for j in candidates[r]:
            needed = set(RESOURCES[j.kind])
            if j.id not in used_ids and not needed & used_resources:
                search(i + 1, pairs + [(j, r)], used_ids | {j.id},
                       used_resources | needed, score + cost(j, r))
    search(0, [], set(), set(), 0.0)
    return best


def quantile95(values):
    return sorted(values)[max(0, math.ceil(.95 * len(values)) - 1)] if values else 0.0


def simulate(jobs, policy="fifo", horizon=480):
    if policy not in POLICIES or not math.isfinite(horizon) or horizon <= 0:
        raise ValueError("unknown policy or invalid horizon")
    jobs = list(jobs)
    if len({j.id for j in jobs}) != len(jobs):
        raise ValueError("duplicate job IDs")
    for j in jobs:
        if (j.kind not in RESOURCES or not all(math.isfinite(x) for x in
                (j.arrival, j.work, j.deadline)) or not 0 <= j.arrival < horizon
                or j.work <= 0 or j.deadline < j.arrival):
            raise ValueError("invalid job")
    by_id = {j.id: j for j in jobs}
    events = [(j.arrival, 1, j.id, -1) for j in jobs]
    heapq.heapify(events)
    waiting, idle, free, trace = [], set(range(3)), set(("corridor", "station")), []
    robot_busy, resource_busy = [0.] * 3, {r: 0. for r in free}
    while events:
        now = events[0][0]
        while events and events[0][0] == now:
            _, event_type, jid, robot = heapq.heappop(events)
            j = by_id[jid]
            if event_type == 1:
                waiting.append(j)
            else:
                idle.add(robot)
                free.update(RESOURCES[j.kind])
        for j, robot in dispatch(waiting, idle, free, now, policy):
            assert robot in idle and set(RESOURCES[j.kind]) <= free
            finish = now + duration(j, robot)
            busy = max(0., min(finish, horizon) - min(now, horizon))
            robot_busy[robot] += busy
            for resource in RESOURCES[j.kind]:
                resource_busy[resource] += busy
            idle.remove(robot)
            free.difference_update(RESOURCES[j.kind])
            waiting.remove(j)
            heapq.heappush(events, (finish, 0, j.id, robot))
            trace.append({**asdict(j), "robot": robot, "start": now, "finish": finish,
                          "wait": now - j.arrival, "miss": finish > j.deadline})
    assert not waiting and len(trace) == len(jobs), "deadlock or lost job"
    waits = [x["wait"] for x in trace]
    n, completed = len(jobs), sum(x["finish"] <= horizon for x in trace)
    metrics = {"jobs": n, "completed": completed, "throughput_per_hour": completed / horizon * 60,
               "average_wait": mean(waits) if n else 0., "p95_wait": quantile95(waits),
               "max_wait": max(waits, default=0.), "deadline_misses": sum(x["miss"] for x in trace),
               "miss_rate": mean(x["miss"] for x in trace) if n else 0.,
               "backlog": n - completed, "makespan": max((x["finish"] for x in trace), default=0.),
               "robot_utilization": sum(robot_busy) / (3 * horizon)}
    metrics.update({r + "_utilization": v / horizon for r, v in resource_busy.items()})
    metrics.update({ROBOT_NAMES[r] + "_utilization": v / horizon for r, v in enumerate(robot_busy)})
    by_kind = {}
    for kind in RESOURCES:
        subset = [x for x in trace if x["kind"] == kind]
        if subset:
            by_kind[kind] = {"count": len(subset), "average_wait": mean(x["wait"] for x in subset),
                             "miss_rate": mean(x["miss"] for x in subset)}
    return {"metrics": metrics, "by_kind": by_kind, "trace": sorted(trace, key=lambda x: x["id"])}
