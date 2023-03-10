/* eslint-disable no-unused-expressions */
/* eslint-disable react/react-in-jsx-scope */
/* eslint-disable no-undef */
/// <reference types="cypress" />

// Summary:
// approx time: 38s
// Test 1 and 2:
//  - Nav menu and buttons should be visible on all urls (for admin and player)
//  - Make sure player cannot see admin page button
// Test 3 and 4:
//  - Nav menu buttons should navigate correctly (for admin and player)
//  - Correct child components should be visible on their corresponding urls
//  - TODO: maybe check isAdmin requests are being made and that they give the correct response?
// Test 5:
//  - Check fetchAllPlayers requests are being made and check responses format
// Test 6:
//  - Check that correct data is displayed on the leaderboard for a mock response
//  - Check streaks are displayed correctly and the on fire badge
//
// TODO: Check graph

describe('Game page', () => {
  beforeEach(() => {
    cy.createGame('test')

    // save gameId of created game under alias gameId for tests to use later
    cy.get('[data-cy="game-id"]').invoke('text').as('gameId')
  })

  it('nav menu is visible on all game urls', function () {
    cy.visit(Cypress.env('baseUrl') + this.gameId)
    cy.checkAdminNavMenu()

    cy.visit(Cypress.env('baseUrl') + this.gameId + '/players')
    cy.checkAdminNavMenu()

    cy.visit(Cypress.env('baseUrl') + this.gameId + '/admin')
    cy.checkAdminNavMenu()

    // Create a player so we can check that nav menu is showing on player page
    cy.joinGameAsPlayer(this.gameId, 'walter', 'https://www.google.com')
    cy.get('[data-cy="player-id"]').invoke('text').as('playerId').then(() => {
      cy.visit(Cypress.env('baseUrl') + this.gameId + '/players/' + this.playerId)
      cy.checkAdminNavMenu()
    })
  })

  it('for players, nav menu shows player page button instead of admin button', function () {
    cy.clearCookies()

    // Create a player, then check nav menu on all pages
    cy.joinGameAsPlayer(this.gameId, 'walter', 'https://www.google.com')
    cy.get('[data-cy="player-id"]').invoke('text').as('playerId').then(() => {
      cy.visit(Cypress.env('baseUrl') + this.gameId)
      cy.checkPlayerNavMenu()

      cy.visit(Cypress.env('baseUrl') + this.gameId + '/players')
      cy.checkPlayerNavMenu()

      cy.visit(Cypress.env('baseUrl') + this.gameId + '/players/' + this.playerId)
      cy.checkPlayerNavMenu()
    })
  })

  it('nav menu buttons should all work and correct component is displayed at each url', function () {
    cy.visit(Cypress.env('baseUrl') + this.gameId)

    // Click on Admin page button
    cy.get('[data-cy="nav-menu"]').click()
    cy.contains('Admin Page').click()
    cy.url().should('equal', Cypress.env('baseUrl') + this.gameId + '/admin')
    cy.get('h1').should('have.text', 'Admin Page')

    // Click on Leaderboard button
    cy.get('[data-cy="nav-menu"]').click()
    cy.contains('Leaderboard').click()
    cy.url().should('equal', Cypress.env('baseUrl') + this.gameId)
    cy.get('h1').should('have.text', 'Leaderboard')

    // Click on Players button
    cy.get('[data-cy="nav-menu"]').click()
    cy.contains('Players').click()
    cy.url().should('equal', Cypress.env('baseUrl') + this.gameId + '/players')
    cy.get('h1').should('have.text', 'Players')
  })

  it('for players, nav menu buttons should all work', function () {
    cy.clearCookies()

    // Create a player, then check nav menu buttons
    cy.joinGameAsPlayer(this.gameId, 'walter', 'https://www.google.com')
    cy.get('[data-cy="player-id"]').invoke('text').as('playerId').then(() => {
      cy.visit(Cypress.env('baseUrl') + this.gameId)

      // Click on Player page button
      cy.get('[data-cy="nav-menu"]').click()
      cy.contains('My Player Page').click()
      cy.url().should('equal', Cypress.env('baseUrl') + this.gameId + '/players/' + this.playerId)
      cy.get('h1').should('contain.text', 'walter')

      // Click on Leaderboard button
      cy.get('[data-cy="nav-menu"]').click()
      cy.contains('Leaderboard').click()
      cy.url().should('equal', Cypress.env('baseUrl') + this.gameId)
      cy.get('h1').should('have.text', 'Leaderboard')

      // Click on Players button
      cy.get('[data-cy="nav-menu"]').click()
      cy.contains('Players').click()
      cy.url().should('equal', Cypress.env('baseUrl') + this.gameId + '/players')
      cy.get('h1').should('have.text', 'Players')
    })
  })

  it('fetchAllPlayers requests are being made and check responses', function () {
    // Create 2 players for the game
    cy.joinGameAsPlayer(this.gameId, 'walter', 'https://www.google.com')
    cy.get('[data-cy="player-id"]').invoke('text').as('playerId').then(() => {
      cy.joinGameAsPlayer(this.gameId, 'jesse', 'https://www.google.co.uk')
    })

    cy.visit(Cypress.env('baseUrl') + this.gameId)
    cy.intercept('GET', '/api/' + this.gameId + '/players').as('fetch-all-players')

    cy.wait('@fetch-all-players').then(({ request, response }) => {
      expect(request.body).to.equal('')
      expect(response.statusCode).to.equal(200)
      expect(response.body).to.have.property('players')
      expect(Object.keys(response.body.players)).to.have.length(2)
      expect(response.body.players[this.playerId]).to.have.property('score')
    })

    cy.wait('@fetch-all-players').then(({ request, response }) => {
      expect(request.body).to.equal('')
      expect(response.statusCode).to.equal(200)
      expect(response.body).to.have.property('players')
      expect(Object.keys(response.body.players)).to.have.length(2)
      expect(response.body.players[this.playerId]).to.have.property('score')
    })

    cy.wait('@fetch-all-players')
  })

  it('shows correct data on leaderboard for mock response data', function () {
    cy.intercept('GET', '/api/' + this.gameId + '/players', { fixture: 'players.json' })

    cy.visit(Cypress.env('baseUrl') + this.gameId)

    // Assert that leaderboard table is sorted and displays information correctly
    cy.get('tbody > :nth-child(1) > :nth-child(2)').should('have.text', 'mock_jesse')

    cy.get('tbody > :nth-child(1) > :nth-child(1)').should('have.text', 'player2')
    cy.get('tbody > :nth-child(1) > :nth-child(4)').should('have.text', '420')
    cy.get('tbody > :nth-child(2) > :nth-child(1)').should('have.text', 'player3')
    cy.get('tbody > :nth-child(2) > :nth-child(4)').should('have.text', '21')
    cy.get('tbody > :nth-child(3) > :nth-child(1)').should('have.text', 'player1')
    cy.get('tbody > :nth-child(3) > :nth-child(4)').should('have.text', '-10')

    cy.get('tbody > :nth-child(2) > :nth-child(5)').should('have.text', ' ON FIRE! ')
    cy.get('tbody > :nth-child(1) > :nth-child(5)').should('have.text', '')

    // Annoying way to check that the streaks are of the correct colour
    cy.get('tbody > :nth-child(1) > :nth-child(3) > :nth-child(1) > :nth-child(1) > :nth-child(3)').should('have.css', 'background-color', 'rgb(255, 0, 0)')
    cy.get('tbody > :nth-child(1) > :nth-child(3) > :nth-child(1) > :nth-child(2) > :nth-child(3)').should('have.css', 'background-color', 'rgb(255, 165, 0)')
    cy.get('tbody > :nth-child(1) > :nth-child(3) > :nth-child(1) > :nth-child(3) > :nth-child(3)').should('have.css', 'background-color', 'rgb(0, 128, 0)')
  })

  it('shows correct graph for mock response data', function () {
    // TODO
  })
})
