const { Client, LocalAuth } = require('whatsapp-web.js');
const QRCode = require('qrcode');
const fs = require('fs');
const sqlite3 = require('sqlite3').verbose(); // Import sqlite3 for database operations
const puppeteer = require('puppeteer'); // Import puppeteer for Chromium management
const path = require('path');

// Define the directory and filename for the log file
const logDir = 'logs';
const logFileName = 'qr_log.log';
const logFilePath = path.join(logDir, logFileName);

// Ensure the log directory exists
if (!fs.existsSync(logDir)) {
    fs.mkdirSync(logDir);
}

// Function to log messages to a file
function logToFile(message) {
    fs.appendFile(logFilePath, `${new Date().toISOString()} - ${message}\n`, err => {
        if (err) {
            console.error('Failed to write to log file', err);
        }
    });
}

// Override console methods to log to file
console.log = (...args) => {
    const message = args.join(' ');
    logToFile(`INFO: ${message}`);
    process.stdout.write(`${message}\n`);
};

console.error = (...args) => {
    const message = args.join(' ');
    logToFile(`ERROR: ${message}`);
    process.stderr.write(`${message}\n`);
};

// Initialize the database
const db = new sqlite3.Database('contacts.db'); // database name

// Function to ensure Chromium is installed and get the executable path
async function ensureChromium() {
    console.log('Checking for Chromium...');
    const browser = await puppeteer.launch();  // Automatically installs Chromium if not present
    const chromiumExecutablePath = puppeteer.executablePath(); // Get the path to the Chromium executable
    await browser.close(); // Close browser after retrieving executable path
    return chromiumExecutablePath;
}

// Function to initialize the database tables
function initializeDatabase() {
    db.run('CREATE TABLE IF NOT EXISTS contacts (id INTEGER PRIMARY KEY, name TEXT, phone TEXT)');
    db.run('CREATE TABLE IF NOT EXISTS groups (id INTEGER PRIMARY KEY, name TEXT)');
    db.run('CREATE TABLE IF NOT EXISTS group_contacts (group_id INTEGER, contact_id INTEGER, FOREIGN KEY(group_id) REFERENCES groups(id), FOREIGN KEY(contact_id) REFERENCES contacts(id))');
}

// Function to save contacts to the database
async function saveContactsToDatabase(client) {
    const contacts = await client.getContacts();
    for (let contact of contacts) {
        if (contact.name || contact.number) {
            db.run(`INSERT INTO contacts (name, phone) VALUES (?, ?)`, [contact.name || "Unknown", contact.number || "Unknown"]);
        }
    }
    console.log('Contacts have been saved to the database.');
}

// Function to update the status in client.json
function updateClientStatus(status) {
    try {
        const clientData = JSON.parse(fs.readFileSync('client.json', 'utf-8')); // Read the client.json file
        clientData.loggedIn = status; // Update the loggedIn field
        fs.writeFileSync('client.json', JSON.stringify(clientData, null, 2)); // Write back the updated JSON
        console.log(`Updated client.json: loggedIn is now ${status}`);
    } catch (err) {
        console.error('Error updating client_status.json', err);
    }
}

// Initialize the client and database
(async () => {
    try {
        const chromiumPath = await ensureChromium(); // Ensure Chromium is available

        const client = new Client({
            authStrategy: new LocalAuth(),
            puppeteer: {
                executablePath: chromiumPath, // Use the retrieved Chromium path
            }
        });

        // Ensure database tables are set up before client is ready
        initializeDatabase();

        client.on('ready', async () => {
            console.log('Client is ready!');
            
            // Update client.json status to true
            updateClientStatus(true);
            
            // Save contacts to the database once the client is ready
            await saveContactsToDatabase(client);
        });

        client.on('qr', async qr => {
            try {
                // Generate the QR code and save it as an image
                await QRCode.toFile('qrcode.png', qr, {
                    color: {
                        dark: '#000000',  // Dark color of the QR code
                        light: '#FFFFFF'  // Light color of the QR code background
                    }
                });
                console.log('QR code saved as qrcode.png');
            } catch (err) {
                console.error('Failed to generate QR code', err);
            }
        });

        client.initialize();
    } catch (err) {
        console.error('Error during initialization', err);
    }
})();
