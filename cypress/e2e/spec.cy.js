describe('empty spec', () => {
  it('Visit blobconverter', () => {
    cy.viewport(1920,1080)
    cy.visit('http://127.0.0.1:8000')

    cy.contains("Zoo Model").click()
    cy.contains("Continue").click()

    cy.get('#zoo-name option', { timeout: 10000 }).each(($el, index, $list) => {


      if (index <=2) {
        return
      }
      cy.log("loop index: " + index)
      cy.get('#zoo-name').select(index)
      cy.contains("button", /^Convert$/, { timeout: 600000 }).click()
    })
  })
})