const { loadConfig } = require('./config');
const { createApp } = require('./create-app');

async function start() {
    const config = loadConfig();
    const runtime = await createApp({ config });
    const server = runtime.app.listen(config.port, config.host);
    server.once('error', () => {
        runtime.close();
        console.error('Não foi possível iniciar o servidor');
        process.exitCode = 1;
    });
    server.once('listening', () => console.log(`LMS DEMO pronto em http://${config.host}:${server.address().port}`));
    let stopping = false;
    const stop = () => {
        if (stopping) return;
        stopping = true;
        server.close(() => { runtime.close(); });
    };
    process.once('SIGINT', stop);
    process.once('SIGTERM', stop);
    return server;
}
if (require.main === module) {
    start().catch(() => { console.error('Falha na inicialização; verifique a configuração'); process.exitCode = 1; });
}
module.exports = { start };
