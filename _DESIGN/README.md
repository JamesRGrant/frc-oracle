# frc-oracle Design
Technology choices and components

## Event Based 
The nature of this problem (triggering predictions as events happen) make it ideal candidate for an event-based design.

I've selected **Kafka as the core event engine**.  Kafka is a popular choice for event streaming, open source, has a "replay" feature, and it was covered in our course.   Given this choice, we can establish some parameters of the design:
* Topics are a type of event
* Producers submit events to a topic
* Consumers read events from a topic
* Consumers can reset their pointer and replay history

So, now we need to think though what should be event, what should be preserved state, and what should be actions.

## Entity Storage
We need some mechanism to store our current state.  These are things like EVENTS, MATCHES, and TEAMS.  Predictions are a bit more tricky.  Should they be a stored entity, or should they just be in a stream? 

### Relational or Document Oriented?
I have a great deal of familiarity with relational databases and they generally scale very well.  However, I expect this system to evolve quite a bit and the data definitions will change.  Updating schema and queries to a relation database can be tiresome.  That's where document oriented database have an advantage.  You can extend the schema easily, and code that uses it does not necessarily have to be updated (as long as you don't remove something).  I don't forsee any immediate needs for a distributed engine such as Spark. 

I've selected **Mongo for entity storage**.  In the first version, it will be containerized and not have durable storage.  Meaning, if the container dies, the EVENTs will need to be reinitialized.

### Core Entities
|Entity|Key|Example|Attributes|
|-|-|-|-|
|`event`|SeasonCode|2024wimi|None, pull from API|
|`team`|id|6223|None, pull from API|
|`match`|Sequence|1|name (e.g. Q3), red teams, blue teams, result (optional)

### Storing Predictions
The first thing to consider is if we want to store the prediction history or just the current prediction.  Either would be fine for the core requirements, but I want to the prediction history to see if they are improving as the EVENT unfolds.  So each MATCH will have 0 to n predictions.

We also have to remember that we will be building support for multiple prediction algorithms in parallel.  That means you will have 1 to n replicas of the predictions.

Predictions could simply be stored in another Kafka topic.  That would make persisting the prediction very easy (publish one event), but reading it would be harder (for the topic for given event, event-match, event-algorithm, pull out the predictions, and construct the data).  Since I am assuming there will be more reads (users looking at the data) than writes (the one prediction), I will lean towards making the write harder and the read easier.

I will **store predictions on the entity as lists**.  But what are they lists of?  Is a simple win/loss prediction?  Or is a probability of winning?  Will we predict ranking points for both the winners and losers?  How do we manage the multiple algorithms?

### Match Results
First, we will think about the data we store for the match results.  To start, just `win`, `tie`, and `total` for each alliance (red and blue).  Later, these can be expanded with ranking points, sub-scores, etc.

Then, for the predictions, there is an array of algorithm results.  Each algorithm has the algorithm name, and accuracy score, and the predictions.  The predicted values are the same format and structure of the results, but the value is an array of predictions.

Here is an example:

```
{"match": {
    sequence: 15,
    name: "q15",
    event: "2024wimi",
    teams: {
        red: ["6223","2202","2358"],
        blue: ["1781","7900","3381"],
    }
    predictions: [{
        algorithm: "average_score",
        red {
            win: [0, 1, 0, 1, 1, 1]
        }
        blue {
            win: [1, 0, 1, 0, 0, 0]
        }
    }]
    results: {
        red: {
            win: 1,
            tie: 0,
            total: 47,
        }
        blue {
            win: 0,
            tie: 0,
            total: 42
        }
    }
}} 
```
When predictions are made, they are added to the arrays.  When the match completes, the results section is added.  As more detailed results are added, the algorithms can be updated to simply use that data to make better predictions of winning or even predict those outcomes (e.g. predict total points).

### Team Ranking
For our first ranking method, we are going to simply say that the best team is the one with the best winning record.  We can predict this at any time by reviewing the matches they played and what our current predictions are.

For example, let say a team has a record of 3-2-0 after 5 matches and we predict they will be 4-1-0 in upcoming matches.  This would have a predicted total record of 7-3-0.  

```
{"team": {
    id: "6223",
    predictions: [{
        algorithm: "average_score",
        wins: [1, 2, 7],
        ties: [0, 0, 0],
        losses: [9, 8, 3],
    }]
    results: {
        wins: 10,
        ties: 0,
        loses: 0,
    }

}}
```

## Event Flow
We can finally design the event flow of the system.  When a match completes, we want to:
1. Update the completed match with the results.
2. Predict new match outcomes for all future matches, for the teams that played in this match.
3. Update the team's predicted ranking

Let's say you just finished the last match in round 5 (everyone has played 5 matches).  There are six teams that each have 5 more qualifying matches.  That means we could have 30 match prediction events.

Then, we want to update the team stats.  We could have each match prediction kick off an event to update it, but then we are triggering 30 updates to team stats.  In reality, we only need 6 (one for each team).  So, i if we have several events (match-complete, predict-match, predict-team) we need to either coordinate all the predict-match events completing before processing predict-team, or we simply predict more team updates than we need to.

To simplify this, we will only use a single event, `match-complete`.  A single consumer can update the match results.  Then, one or more algorithm consumers can update the future matches and team.  The algorithms do not need to wait on the other consumuer to update the match results because they will have them in the message also.  There is still an opportunity for parallelism of the match predictions, but that can be implemented by each algorithm consumer.

OK, so here are the main components with the events the produce or consume

### Initialize the System
1. Load event data
2. At this time, we will not predict the first round of match
3. Trigger a replay of match results

### Producer: Replay
1. Submit a `match_complete` event for every match 

### Consumer: Match
1. Update the `match` entity with the results block.

### Consumer: Algorithm
1. Generate a new match prediction in the `match` for each future match for this team
2. Generate a new team prediction in the `team`
Each algorithm consumer should only be updating predictions for its algorithm.  We'll have to test to ensure there are no collisions.

## API Routes

|Route|Method|Description|
|-|-|-|
|events|GET|All the events indexed by the system.|
|events/\<code>|GET|Info for the event.|
|events/\<code>|PUT|Create the event.  If existing, removes all results and prediction data.  If results exist, will queue them up for processing by any currently active prediction algorithms.|
|events/\<code>|DELETE|Removes the event and all match info|
|events/\<code>/matches|GET|List of matches|
|events/\<code>/matches|PATCH|Add match results or predictions|
|events/\<code>/replay|POST|Triggers match complete events if the match history exists.  This is used for testing.|
