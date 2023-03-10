/* eslint-disable no-undef */
// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************
//
//
// -- This is a parent command --
// Cypress.Commands.add('login', (email, password) => { ... })
//
//
// -- This is a child command --
// Cypress.Commands.add('drag', { prevSubject: 'element'}, (subject, options) => { ... })
//
//
// -- This is a dual command --
// Cypress.Commands.add('dismiss', { prevSubject: 'optional'}, (subject, options) => { ... })
//
//
// -- This will overwrite an existing command --
// Cypress.Commands.overwrite('visit', (originalFn, url, options) => { ... })

import { mount } from 'cypress/react18'

Cypress.Commands.add('mount', mount)

// Creates a game from the home page
Cypress.Commands.add('createGame', (password) => {
  cy.visit(Cypress.env('baseUrl'))
  cy.contains('Create').click()
  cy.get('[data-cy="password-input"]').clear()
  cy.get('[data-cy="password-input"]').type(password)
  cy.get('form > .mantine-Button-root').click()
  // Waits up to 4s for the returned game id to be visible so we can grab it and alias it later
  cy.get('[data-cy="game-id"]').should('be.visible')
})

// Joins a game as a player from the home page
Cypress.Commands.add('joinGameAsPlayer', (gameId, name, url, valid = true) => {
  cy.visit(Cypress.env('baseUrl'))
  cy.contains('Join').click()
  cy.get('[data-cy="game-id-input"]').clear()
  cy.get('[data-cy="game-id-input"]').type(gameId)
  cy.get('[data-cy="player-name-input"]').clear()
  cy.get('[data-cy="player-name-input"]').type(name)
  cy.get('[data-cy="url-input"]').clear()
  cy.get('[data-cy="url-input"]').type(url)
  cy.get('form > .mantine-UnstyledButton-root').click()
  if (valid) {
    // waits up to 4s for player id to be visible before aliasing
    cy.get('[data-cy="player-id"]').should('be.visible')
  }
})

// Joins a game as a moderator from the home page
Cypress.Commands.add('joinGameAsModerator', (gameId, password) => {
  cy.visit(Cypress.env('baseUrl'))
  cy.contains('Join').click()
  cy.get('.mantine-8jlqcf').click()
  cy.get('[data-cy="mod-game-id-input"]').clear()
  cy.get('[data-cy="mod-game-id-input"]').type(gameId)
  cy.get('[data-cy="mod-pwd-input"]').clear()
  cy.get('[data-cy="mod-pwd-input"]').type(password)
  cy.get('form > .mantine-Button-root').click()
})

// Check nav bar buttons for admins are all visible
Cypress.Commands.add('checkAdminNavMenu', () => {
  cy.get('[data-cy="nav-menu"]').click()
  cy.contains('Admin Page').should('be.visible')
  cy.contains('Leaderboard').should('be.visible')
  cy.contains('Players').should('be.visible')
})

// Check nav bar buttons for players are all visible
Cypress.Commands.add('checkPlayerNavMenu', () => {
  cy.get('[data-cy="nav-menu"]').click()
  cy.contains('My Player Page').should('be.visible')
  cy.contains('Leaderboard').should('be.visible')
  cy.contains('Players').should('be.visible')
})
