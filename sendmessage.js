const fs = require('fs');
const path = require('path');
const { Client, LocalAuth } = require('whatsapp-web.js');
const puppeteer = require('puppeteer'); // Full Puppeteer package

// Path for the log file and client status file
const logFilePath = 'logs/messages.log';
const statusFilePath = 'client_status.json';

// Utility function to log messages
function logMessage(message) {
    const timestamp = new Date().toISOString();
    fs.appendFile(logFilePath, `${timestamp} - ${message}\n`, (err) => {
        if (err) console.error('Failed to write log:', err);
    });
}

// Utility function to create client status file if it does not exist
function ensureStatusFile() {
    if (!fs.existsSync(statusFilePath)) {
        const initialStatus = { status: 'initialized', lastUpdated: new Date().toISOString() };
        fs.writeFileSync(statusFilePath, JSON.stringify(initialStatus, null, 2), 'utf8');
        logMessage('Created client_status.json file.');
    }
}

async function getChromiumPath() {
    // Check if Chrome or Chromium is already installed
    const chromiumPath = puppeteer.executablePath();
    return chromiumPath;
}

async function ensureChromium() {
    logMessage('Checking for Chromium...');
    const chromiumPath = await getChromiumPath();
    return chromiumPath;
}

(async () => {
    try {
        ensureStatusFile(); // Ensure status file is created

        const chromiumPath = await ensureChromium();

        const client = new Client({
            authStrategy: new LocalAuth(),
            puppeteer: {
                executablePath: chromiumPath, // Use Puppeteer's Chromium
            }
        });

        client.on('ready', () => {
            logMessage('Client is ready!');
            updateStatusFile('Client is ready');
            processMessages();
        });

        async function processMessages() {
            const jsonFilePath = process.argv[2];
            if (!jsonFilePath) {
                const errorMessage = 'No JSON file path provided.';
                console.error(errorMessage);
                logMessage(errorMessage);
                return;
            }

            try {
                const data = JSON.parse(fs.readFileSync(jsonFilePath, 'utf8'));
                const { contacts, message } = data;

                logMessage(`Contacts: ${contacts}`);
                logMessage(`Message: ${message}`);

                for (const contact of contacts) {
                    await sendMessage(contact, message);
                    logMessage(`Message sent to ${contact}`);
                }

                deleteJsonFile(jsonFilePath);

            } catch (error) {
                const errorMessage = `Error processing messages: ${error}`;
                console.error(errorMessage);
                logMessage(errorMessage);
            }
        }

        async function sendMessage(contactId, message) {
            try {
                const chat = await client.getChatById(contactId);
                await chat.sendMessage(message);
            } catch (error) {
                const errorMessage = `Error sending message to ${contactId}: ${error}`;
                console.error(errorMessage);
                logMessage(errorMessage);
            }
        }

        function deleteJsonFile(filePath) {
            fs.unlink(filePath, (err) => {
                if (err) {
                    const errorMessage = `Failed to delete file ${filePath}: ${err}`;
                    console.error(errorMessage);
                    logMessage(errorMessage);
                } else {
                    logMessage(`Successfully deleted file ${filePath}.`);
                }
            });
        }

        function updateStatusFile(status) {
            const statusData = {
                status: status,
                lastUpdated: new Date().toISOString()
            };
            fs.writeFileSync(statusFilePath, JSON.stringify(statusData, null, 2), 'utf8');
            logMessage(`Updated client_status.json: ${status}`);
        }

        client.initialize();
    } catch (err) {
        const errorMessage = `Error during initialization: ${err}`;
        console.error(errorMessage);
        logMessage(errorMessage);
    }
})();
