import { React, useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { Button, Card, Badge, Group } from "@mantine/core";
import axios from "axios";

import PlayerEventCard from "./PlayerEventCard";

// const api = axios.create({
//   baseURL: "https://extreme-restartup.fly.dev/",
// });

function Player() {
  const params = useParams();
  const [events, setEvents] = useState([]);

  useEffect(() => {
    const getEvents = async () => {
      const events = await fetchEvents();
      console.log(events);
      setEvents(events);
    };

    getEvents();
  }, []);

  const fetchEvents = async () => {
    try {
      const response = await axios.get(`/api/${params.gameid}/players/${params.id}/events`);
      return response;
    } catch (error) {
      // console.error(error);

      // Only here because no data from real endpoint yet
      return [
        { id: 1, query: "event1", difficulty: 0, response_type: "NO_RESPONSE", points_gained: -5 },
        { id: 2, query: "event2", difficulty: 1, response_type: "WRONG", points_gained: -3 },
        { id: 3, query: "event3", difficulty: 2, response_type: "CORRECT", points_gained: 5 },
      ];
    }
  };

  const deletePlayer = (id) => {
    console.log("deleted player", id);
  };

  return (
    <div>
      <div> Hello {params.id}</div>
      <div> Your score is: </div>
      <Button
        onClick={() => {
          deletePlayer(params.id);
        }}
      >
        Withdraw
      </Button>
      <Card>
        <ul>
          {events.map((event) => (
            <Card key={event.id} shadow="sm" radius="md" withBorder>
              <Group>
                <div>id: {event.id}</div>
                <div>difficulty: {event.difficulty}</div>
                <div>{event.points_gained} points </div>
                {event.response_type == "NO_RESPONSE" && (
                  <div>
                    <Badge color="red"> NO RESPONSE </Badge>
                  </div>
                )}
                {event.response_type == "WRONG" && (
                  <div>
                    <Badge color="orange"> INCORRECT </Badge>
                  </div>
                )}
                {event.response_type == "CORRECT" && (
                  <div>
                    <Badge color="green"> CORRECT </Badge>
                  </div>
                )}
              </Group>
            </Card>
          ))}
        </ul>
      </Card>
    </div>
  );
}

export default Player;
