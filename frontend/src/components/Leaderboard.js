import React, {useEffect, useState} from 'react'
import { useParams } from "react-router-dom"
import Container from "react-bootstrap/Container"
import Table from "react-bootstrap/Table"
import axios from 'axios'


function Leaderboard() {
  const params = useParams()
  const [refreshTimer, setRefreshTimer] = useState(0)
  const [leaderboard, setLeaderboard] = useState([])

  useEffect(() => {
    getLeaderboard()
    setTimeout(() => setRefreshTimer(prevState => prevState + 1), 1000)
  }, [refreshTimer]);

  function getLeaderboard() {
      axios.get("http://127.0.0.1:5000/api/" + params.gameid + '/leaderboard')
      .then(function (response) {
        console.log(response);
        setLeaderboard(response.data)

      })
      .catch(function (error) {
        console.log(error);
      });
  }

  return (
    <Container className="p-5">
      <h2>Leaderboard</h2>
      {
          <Table>
            <thead>
                <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Score</th>
                </tr>
            </thead>
            <tbody>
                {
                    leaderboard.map(({id, name, score}) => (
                        <tr>
                        <td>{id}</td>
                        <td>{name}</td>
                        <td>{score}</td>
                        </tr>
                    ))
                }
            </tbody>
          </Table>
      }
    </Container>
  )
}

export default Leaderboard
