// Intentionally simulated. No credentials, network calls, card logging or storage.
class DemoPaymentGateway {
    authorize(card) {
        return { status: card.startsWith('4') ? 'PAID' : 'DENIED', mode: 'demo' };
    }
}
module.exports = { DemoPaymentGateway };
