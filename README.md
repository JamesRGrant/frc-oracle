# frc-oracle
A system to predict winners and recommend alliance partners at a FIRST Robotics Competition event.

## What is FIRST and why is this system needed?
_"FIRST® is a global nonprofit organization that prepares young people for the future through a suite of life-changing youth robotics programs that build skills, confidence, and resilience."_ see https://www.firstinspires.org/.  There are four main programs, and this system is used for FRC, which is high school students building large robots to compete in a game.  Check out teams in your area and become a mentor!

The structure of an event is important to understand.  Matches are played with an ALLIANCE of 3 TEAMS vs another ALLIANCE of three TEAMS.  So, to win at the event, you need to:

1. Build a robot that can perform tasks to achieve high scores.
2. Be on an alliance with two other good robots

Match results are posted at the event as they happen and are available from a couple of APIs, usually within minutes. **Since the matches results are by ALLIANCE, it can be difficult to determine how well a TEAM is performing.**  For example, a really great robot could be paired with robots that are struggling, and it may not look like a good team.  

This is why human scouting is important.  If you can record data about at TEAM, you can have a better idea of how that actual TEAM is performing.  This information can be a competitive advantage if you are in a position to select your ALLIANCE partners.

There is a bit more complexity on how TEAMS are chosen for an ALLIANCE:
* During qualification matches:
    * FIRST targets each TEAM playing 10 matches at an event
    * Your alliances partners are pre-selected by FIRST
    * Winning a game gives you 2 ranking points
    * Depending on the year, there could be up to 2 additional ranking points which are awarded for completing certain tasks
    * So, a winning team may achieve 2 to 4 ranking points and a losing team would have 0 to 2
* During finals, the top 8 TEAMS pick their ALLIANCE partners
    * The top 8 TEAMS are determined by the highest ranking point average
    * The teams select in a round-robin fashion, so you need to know what is the best TEAM, that is still available, for your ALLIANCE
    * The winner of a finals match is determined by match score (no ranking points)
    * Finals is a double-elimination bracket to determine the winner
* The winning ALLIANCE TEAM captain and first-pick TEAM go the World Competition!

 

## System Functionality
**This system is designed to help a TEAM pick the best ALLIANCE partners to maximize their chance of winning the event.**

The first version of this application has these core functions in the context of a FRC EVENT:

1. Rank teams (used for selecting an ALLIANCE)
2. Predict which ALLIANCE will win an upcoming match (used to assess accuracy)

It is designed to respond to the current situation as the FRC EVENT unfolds over a couple of days.  Predictions are updated as match results become available.  
* For a TEAM's first qualification match, there is no data and the prediction is random.  
* As matches get played, the system can start predicting future matches and overall team performance.  
* After the first round of matches, there are now 6 data points (6 teams each played one match) to predict a TEAM's second match.
* For the TEAM's last qualification match, there could be up to 54 data points available (each of the 6 TEAMs will have played 9 matches) for the final prediction.

The system will support the ability to "replay" an EVENT at any time to test current or new functionality.

The system is designed to support multiple prediction modules at once.  This will allow contributors to test and compare different methods of Machine Learning to improve the systems prediction ability.

Recording scouting data by TEAM is not yet supported but will likely improve prediction accuracy.

Reference additional information in the [_Requirements](./_REQUIREMENTS/README.md)  folder

## Technology Choices
This system was created as a final project for a course in Microservices and Cloud Computing at Milwaukee School of Engineering, a required course for a Master's Degree in Machine Learning.

Hence, in addition to producing the core functionality, there will be exploration of various technology choices.  

To start, we will be focused on development velocity: get the system working ASAP:
* Use external APIs for EVENT, TEAM, and MATCH data 
* Python for all components: REST APIs, website, prediction engine
* Kafka for event streaming

Reference additional information in the [_Design](./_DESIGN/README.md) folder

## How to run
The system can be run local on a single laptop that is running linux (use WSL for Windows).  This is primarily for development purposes, but it could be run locally to try it out at an event.  

In the root directory, simnply run 
`docker compose up`
This will run in the window with the logs running.  Use `-d` if you want to run it in the background.

Alternatively, every subdirectory can be run directly from the terminal window if you are debugging issues.

Ultimately, the system is designed to run in a cloud envionment so that a team could share data and simply access it from their cell phones or tablets.  I was able to quickly deploy in a VM, called a Droplet in Digital Ocean.  See this article for instructions on how to select the correct image: 
    https://www.digitalocean.com/community/questions/how-do-i-upload-a-docker-compose-application-that-it-in-github

Before running docker compose, I needed to:
1. Create .env files in the subdirectories for all the secrets/paths
2. apt install docker-compose

Finally, Google Auth requires URL will a trusted domain suffix.  So accessing it via the IP will not work.  I was able to use the nip.io service.

Instead of: http://your-IP:8000/

Try: http://your-IP.nip.io:8000/