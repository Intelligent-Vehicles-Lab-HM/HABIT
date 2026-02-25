# Metrics

This document describes all evaluation metrics used by the HABIT benchmark. The metrics follow the CARLA Leaderboard framework with the addition of HABIT-specific injury severity metrics.

## Core Metrics

### Driving Score (DS)

The driving score is the primary aggregate metric. It is computed as:

```
DS = RC * IS
```

where RC is Route Completion and IS is the Infraction Score. The driving score captures both how far the agent progresses along the route and how safely it drives.

### Route Completion (RC)

Route completion measures the percentage of the route that the agent successfully traverses before the scenario ends. A value of 100 means the agent reached the final waypoint.

The route is defined as a sequence of GPS waypoints in `data/routes/town10_routes.xml`. The evaluator tracks the agent's progress along this route and records the furthest percentage reached.

- Range: 0 to 100
- A route is considered fully completed when RC >= 100

### Infraction Score (IS)

The infraction score is a penalty multiplier that starts at 1.0 and decreases as the agent commits infractions. It is computed using an additive-then-inverse formula:

```
infraction_value = sum of all penalty values for committed infractions
IS = (1 / (1 + infraction_value)) * outside_lanes_factor
```

The `outside_lanes_factor` is a separate multiplicative term for lane departure infractions, computed as `(1 - percentage_outside / 100)`.

- Range: 0.0 to 1.0
- A perfect run with no infractions yields IS = 1.0

## Infraction Penalties

Each infraction adds a fixed value to `infraction_value`, which is then converted to the infraction score. The penalty values are:

| Infraction Type | Penalty Value | Description |
|----------------|---------------|-------------|
| Collision with pedestrian | 1.00 | Ego vehicle collides with a pedestrian (walker) |
| Collision with vehicle | 0.70 | Ego vehicle collides with another vehicle |
| Collision with static object | 0.60 | Ego vehicle collides with a static object (barrier, pole, etc.) |
| Running a red light | 0.40 | Ego vehicle crosses a red traffic light |
| Running a stop sign | 0.25 | Ego vehicle fails to stop at a stop sign |
| Scenario timeout | 0.40 | The scenario times out before route completion |
| Yield to emergency vehicle | 0.40 | Ego vehicle fails to yield to an emergency vehicle |
| Minimum speed infraction | 0.40 (scaled) | Agent drives below minimum speed for too long; penalty is scaled by `(1 - percentage / 100)` |

**How the penalty accumulates:** each infraction event adds its penalty value to a running total. For example, if the agent collides with one pedestrian (1.00) and runs one red light (0.40), the total infraction value is 1.40, and the infraction score becomes `1 / (1 + 1.40) = 0.417`.

**Equivalent multiplicative penalties:** for reference, the penalty values above correspond to the following effective multipliers on the first infraction of each type (assuming no other infractions):

| Infraction Type | Effective Multiplier |
|----------------|---------------------|
| Collision with pedestrian | 0.50 |
| Collision with vehicle | 0.59 |
| Collision with static object | 0.63 |
| Running a red light | 0.71 |
| Running a stop sign | 0.80 |

**Note:** collisions are only counted when the ego vehicle's speed exceeds a minimum threshold (0.1 m/s), preventing stationary contact from being penalized.

## Scenario-Ending Events

Certain events terminate the current route immediately:

- **Route deviation:** the agent deviates too far from the prescribed route
- **Vehicle blocked:** the agent remains stationary (below minimum speed) for too long

These events stop the route and record the failure reason in the results.

## HABIT-Specific Metrics

### pMAIS3+ (Probability of MAIS >= 3)

pMAIS3+ estimates the probability that a pedestrian collision results in a Maximum Abbreviated Injury Scale score of 3 or higher (serious-to-fatal injury). This metric is computed for every pedestrian collision using the Yanagisawa et al. logistic regression model, which was fitted to real-world crash data from the Pedestrian Crash Data Study (PCDS).

**Formula:**

```
logit = beta0 - beta1 * relative_speed
pMAIS3+ = 1 / (1 + exp(logit))
```

where:
- `relative_speed` = magnitude of the velocity difference between the ego vehicle and the pedestrian, in m/s
- `beta0 = 3.164`
- `beta1 = 0.288`

**Interpretation:**
- At low relative speeds (< 5 m/s), pMAIS3+ is very low (< 5%)
- At moderate speeds (~25 km/h / ~7 m/s), the risk rises significantly
- At high speeds (> 40 km/h / ~11 m/s), pMAIS3+ exceeds 50%

This metric is logged for each pedestrian collision event and reported alongside the standard collision count. It provides a severity-weighted view of collision outcomes rather than treating all collisions equally.

### FPBR (False Positive Braking Rate)

The false positive braking rate measures how often the agent performs unnecessary hard braking events. A "false positive brake" is a hard braking event that occurs when there is no actual collision risk -- for example, braking aggressively for a pedestrian that is not on a collision course.

FPBR captures an important aspect of driving comfort and realism that is not reflected in the standard infraction score. An overly cautious agent that brakes at every pedestrian would achieve a low collision rate but a high FPBR.

## Infractions Per Kilometer

In addition to the route-level infraction score, the benchmark reports the number of each infraction type normalized per kilometer driven. This allows comparison across routes of different lengths.

The distance denominator is computed as:

```
km_driven = sum over routes of (route_length_meters / 1000) * (route_completion / 100)
```

This means only the portion of the route that was actually driven counts toward the denominator.

Reported per-km metrics include:
- Collisions with pedestrians per km
- Collisions with vehicles per km
- Collisions with static objects (layout) per km
- Red light infractions per km
- Stop sign infractions per km
- Off-road infractions (outside route lanes, reported as fraction of distance)
- Route deviations per km
- Vehicle blocked events per km

## Results Structure

After evaluation, results are saved in JSON format with the following structure:

- **Global record:** averaged scores and per-km infraction counts across all routes
  - `scores_mean.score_composed` -- mean driving score
  - `scores_mean.score_route` -- mean route completion
  - `scores_mean.score_penalty` -- mean infraction score
  - `scores_std_dev` -- standard deviation of each score
  - `infractions` -- per-km counts for each infraction type
  - `meta.total_length` -- total route length in meters

- **Per-route records:** detailed breakdown for each route
  - `scores.score_composed` -- driving score for this route
  - `scores.score_route` -- route completion percentage
  - `scores.score_penalty` -- infraction score
  - `infractions` -- list of infraction messages for each type
  - `status` -- "Perfect", "Completed", or "Failed" with reason
  - `meta` -- route length, game duration, system duration

The results file is written incrementally during evaluation, so partial results are available even if the simulation is interrupted.
