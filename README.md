# Extreme Startup Scaled
Extreme startup is a software development game which allows players to compete with each other to write code and deliver new features, simulating real-world scenarios where developers develop software to satisfy changing market demand. It's a game designed to teach good software development practices such as CI/CD and test-driven development. 

To play the game, players need to register an endpoint with the game server, and the server will start sending questions/challenges to the endpoint. Players get points when their code can respond correctly to challenges presented by the software, and get penalised otherwise. As players solve a set of challenges, the server will introduce a new set of challenges while occasionally presenting players with challenges which has been solved, encouraging players to write reusable code. 

## How to play
Visit https://d1zlib8d3siide.cloudfront.net/ to create a game or join a game as a player/moderator. To join as a player, you will need an API endpoint to receive and respond to questions, and register it when joining the game.

## Architecture
[Diagram here]

## File Structure
[Code here]

## Version history
The original software is written by [rchatley](https://github.com/rchatley/extreme_startup), which is hosted locally and designed to be played by a small group of people in a room. As part of the college's group project, my group and I [rewrote the software](https://gitlab.doc.ic.ac.uk/g226002123/extreme-restartup) using modern and well-tested code, revamped the user interface, add additional features such as games and player monitoring, and enable multiple game session to be hosted in a self-service way. You can play create and join the game which is deployed [on this site](https://extreme-startup.fly.dev/). 

We also attempted to implement [a scaled version](https://gitlab.doc.ic.ac.uk/g226002123/extreme-restartup-scaled) of the software which supports elastic scalability using AWS Simple Queue Service(SQS) and cloud functions, but the version still required a flask server to be deployed and run 24/7, and fall shorts in multiple aspects to support stable gameplay.

This version picks up from the scaled version, is implemented to support true elastic scalability and serverless model, and restructures the storage structure and code to support more efficient queries and updates of the game state.


## Known Issues
* Fix/Reimplement GameStats - the review page currently shows a prototype game statistics
* Data Race between game runners - the lambda function to reset score and the function to administer question might attempt to modyfing a player item at the same time
* Duplicated game monitoring tasks - SQS standard queue might duplicate message and resulting in same game event task to be run
* Inefficient frontend code - the frontend make a request to poll data every seconds even when the game is not running
