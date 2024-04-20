# frc-oracle Requirements
The desired functionality of the system.

## Terms
The following domain specific terms are used in FRC:
* EVENT - a multi-day competition
* MATCH - a single game
    * QUALIFICATION MATCH
    * PLAYOFF MATCH
* TEAM - a team that builds a robot
* ALLIANCE - a grouping of three TEAMS for a match

## Web Application 
|ID|Workflow|Description|Nav To|
|-|-|-|-|
|1|Login|Used to limit access to the site, certain features, or log who entered data|2|
|2|Choose EVENT|Only certain events will be indexed and available|3|
|3|Display TEAM rankings|Sorted best to worst|2,4,5,6|
|4|Display all EVENTS|All upcoming matches|3|
|5|Display TEAM EVENTS|Only upcoming MATCHES for specified TEAM|3|
|6|Replay EVENT|Admin feature to replay predictions and results|3|

## Data Sources and Initialization
* EVENT, TEAM, and MATCH information
    * There are two main options for obtaining data: the FRC API and the Blue Alliance API.  
    * The Blue Alliance API uses the FRC API and adds additional data.  
    * Information we are interested includes, but may not be limited to:
        * EVENT - name, location, date
        * TEAM - name, number, home town
        * MATCH - number, type (qualification or playoff), winning alliance, alliance stats (score, ranking points)
* Setting up an EVENT
    * There are hundreds of EVENTS each year, but most teams only go to one.
    * Hence, we can choose to only setup the EVENTS we are interested in
    * The matches will be loaded in order along with the teams that play each match
        * NOTE: during a live EVENT, the TEAMS in each QUALIFICATION MATACH published after the first day
        * The TEAMS in the PLAYOFF MATCHES are not known until just before they occur
        * For simplicity we will just load all of these up front.
        * To use at a live event, they will need to be manually loaded or dynamically obtained from the API sources.  

## Prediction Action
When a match is completed, new information is now available for those 6 teams.  Predictions will be updated for:
* The TEAM's overall ranking
* Each of the TEAM's future matches

## Replay Action
When a replay action is triggered, the following happens:
1. MATCH results are deleted
2. MATCH predictions are deleted
3. TEAM rankings are deleted
This resets the event information as if it has not yet happened.

Then, a replay agent triggers match results.  This can be on a specified interval (e.g. 1 second).  As each match result is triggered, the Prediction Action happens.