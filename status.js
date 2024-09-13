const fs = require('fs');
const { Client, LocalAuth } = require('whatsapp-web.js');  // Import Client and LocalAuth
const puppeteer = require('puppeteer');                    // Import puppeteer for Chromium management

// Path to the status file
const statusFilePath = 'client_status.json';

// Function to ensure Chromium is installed and get the executable path
async function ensureChromium() {
    console.log('Checking for Chromium...');
    const browser = await puppeteer.launch({ headless: true }); // Launch Chromium in headless mode
    const chromiumExecutablePath = puppeteer.executablePath();  // Get the path to the Chromium executable
    await browser.close(); // Close browser after retrieving executable path
    return chromiumExecutablePath;
}

// Initialize or reset the status file to loggedIn: false
const initializeStatusFile = () => {
    fs.writeFileSync(statusFilePath, JSON.stringify({ loggedIn: false }));
};

// Update the status file based on client status
const updateStatusFile = (loggedIn) => {
    fs.writeFileSync(statusFilePath, JSON.stringify({ loggedIn }));
};

// Initialize the client and database
(async () => {
    try {
        const chromiumPath = await ensureChromium(); // Ensure Chromium is available

        // Always reset the status to false at the start of the script
        initializeStatusFile();

        // Create a new client instance with LocalAuth and Chromium path
        const client = new Client({
            authStrategy: new LocalAuth(),
            puppeteer: {
                executablePath: chromiumPath, // Use the retrieved Chromium path
            }
        });

        // When the client is ready, log status and update the status file
        client.once('ready', () => {
            console.log('Client is ready!');
            updateStatusFile(true); // Set loggedIn to true once the client is ready
        });

        client.initialize();

        // Handle graceful shutdown
        process.on('SIGINT', async () => {
            console.log('Shutting down client...');
            await client.destroy();
            updateStatusFile(false); // Set loggedIn to false when shutting down
            process.exit(0);
        });

    } catch (error) {
        console.error('Error initializing the client:', error);
        updateStatusFile(false); // Ensure loggedIn is false if there's an error during initialization
    }
})();
