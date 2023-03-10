/* eslint-disable no-unused-expressions */
/* eslint-disable react/react-in-jsx-scope */
/* eslint-disable no-undef */
/// <reference types="cypress" />

// Summary:
// approx time: 17s
// Test 1:
//  - Correct components are displayed on the correct urls
// Test 2:
//  - You can only navigate to game id's that exist
// Test 3:
//  - You can only navigate to player pages for player id's that exist
// Test 4:
//  - only admins can access the admin page
//
// TODO: You can only navigate to your own player page

describe('Game page', () => {
  beforeEach(() => {
    cy.createGame('test')

    // save gameId of created game under alias gameId for tests to use later
    cy.get('[data-cy="game-id"]').invoke('text').as('gameId')
  })

  it('shows correct components on correct urls', function () {
    cy.joinGameAsPlayer(this.gameId, 'walter', 'https://www.google.com')
    cy.get('[data-cy="player-id"]').invoke('text').as('playerId').then(() => {
      // Home component
      cy.visit(Cypress.env('baseUrl'))
      cy.contains('Extreme Startup').should('be.visible')

      // Game + Leaderboard component
      cy.visit(Cypress.env('baseUrl') + this.gameId)
      cy.get('[data-cy="nav-menu"]').should('be.visible')
      cy.contains('Leaderboard').should('be.visible')

      // Players component
      cy.visit(Cypress.env('baseUrl') + this.gameId + '/players')
      cy.contains('Players').should('be.visible')

      // Player component
      cy.visit(Cypress.env('baseUrl') + this.gameId + '/players/' + this.playerId)
      cy.contains('Player:').should('be.visible')

      // Admin component
      cy.visit(Cypress.env('baseUrl') + this.gameId + '/admin')
      cy.contains('Admin Page').should('be.visible')

      // Not Found component
      cy.visit(Cypress.env('baseUrl') + this.gameId + '/invalidurl')
      cy.contains('not found').should('be.visible')
    })
  })

  it('shows not found page when trying to visit a url with invalid game id', function () {
    cy.visit('localhost:5173/420')
    cy.contains('not found').should('be.visible')
  })

  it('shows not found page when trying to visit a url with invalid player id', function () {
    cy.visit(Cypress.env('baseUrl') + this.gameId + '/players/420')
    cy.contains('not found').should('be.visible')
  })

  it('only allows admins to see the admin page', function () {
    cy.clearCookies()

    cy.joinGameAsPlayer(this.gameId, 'walter', 'https://www.savewalterwhite.com')

    // Try to visit admin page
    cy.visit(Cypress.env('baseUrl') + this.gameId + '/admin')

    // Assert that you are redirected back to the game page
    cy.get('h1').should('have.text', 'Leaderboard')
    cy.url().should('equal', Cypress.env('baseUrl') + this.gameId)
  })

  it('only allows you to see your own player page', function () {
    // TODO (need to be able to check authentication of cookie with backend)
  })
})
