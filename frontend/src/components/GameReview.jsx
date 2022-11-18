import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { Table, Title, Card, Grid, Space } from '@mantine/core'
import FinalChart from './FinalChart'
import FinalBoard from './FinalBoard'
import FinalStats from './FinalStats'
import { fetchFinalLeaderboard } from '../utils/requests'

function GameReview () {
  const params = useParams()

  const [finalLeaderboard, setFinalLeaderboard] = useState([])
  // const [stats, setStats] = useState({})
  // const [keyPoints, setKeyPoints] = useState([])

  const mockKeyPoints = [
    {
      title: 'key point 1',
      description: 'player X beat previous leader and maintained that position for more than 15 seconds',
      occurence_time: 30000,
      achieved_by_team: 'team 2'
    }
  ]

  useEffect(() => {
    const getReviewData = async () => {
      try {
        // Fetch game data here
        const [leaderboardResponse] = await Promise.all([
          fetchFinalLeaderboard(params.gameId)
        ])

        setFinalLeaderboard(leaderboardResponse)
        // setStats(mockStats)
        // setKeyPoints(mockKeyPoints)
      } catch (error) {
        console.error(error)
      }
    }

    getReviewData()
  }, [])

  const asMappable = (leaderboard) => {
    if (Array.isArray(leaderboard)) {
      return leaderboard
    } else {
      return Object.keys(leaderboard).map(key => leaderboard[key])
    }
  }

  const chartPlayersOfLeaderBoard = (leaderboard) => {
    return asMappable(leaderboard).map(p => {
      return {
        id: p.player_id,
        name: p.name
      }
    })
  }

  return (
    <>
      <h1>Game Review: {params.gameId}</h1>
      <Grid style={{ maxWidth: '100%' }}>
        <Grid.Col lg={8} md={12}>
          <Card>
            <Title order={1} color="white" weight={1000}>Final Chart</Title>
            <Space h='lg' />
            <FinalChart gameId={params.gameId} players={chartPlayersOfLeaderBoard(finalLeaderboard)} />
          </Card>
        </Grid.Col>

        <Grid.Col lg={4} md={12}>
            <Card sx={{ height: '100%', overflow: 'auto' }}>
              <Title order={1} color="white" weight={1000}>Final leaderboard</Title>
              <Space h='lg' />
              <FinalBoard finalBoard={asMappable(finalLeaderboard)} />
            </Card>
        </Grid.Col>

        <Grid.Col lg={6} md={12}>
            <Card sx={{ height: '100%' }}>
              <Title order={1} color="white" weight={1000}>Stats</Title>
              <Space h='lg' />
              <FinalStats/>
            </Card>
        </Grid.Col>
      </Grid>

      <div>
        <h3>Analysis</h3>
      </div>
      <h3>Key points</h3>
      <Table>
        <thead>
          <tr>
            <th>Title</th>
            <th>Description</th>
            <th>Occurrence Time</th>
            <th>Player</th>
          </tr>
        </thead>
        <tbody>
          {
            mockKeyPoints.map((keyPoint) => (
              <tr key={keyPoint.id}>
                <td>{keyPoint.title}</td>
                <td style={{ width: '300px' }}>{keyPoint.description}</td>
                <td>{keyPoint.occurence_time}</td>
                <td>{keyPoint.acheived_by_team}</td>
              </tr>
            ))
          }
        </tbody>
      </Table>
    </>
  )
}

export default GameReview
