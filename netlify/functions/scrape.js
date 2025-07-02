const { spawn } = require('child_process');
const path = require('path');

exports.handler = async (event, context) => {
    if (event.httpMethod !== 'POST') {
        return {
            statusCode: 405,
            body: JSON.stringify({ error: 'Method not allowed' })
        };
    }

    try {
        const { tags } = JSON.parse(event.body);
        
        if (!tags || tags.length === 0) {
            return {
                statusCode: 400,
                body: JSON.stringify({ error: 'No tags provided' })
            };
        }

        // Run the scraper with the selected tags
        const tagsString = tags.join(',');
        
        return new Promise((resolve) => {
            const scraper = spawn('python3', ['B2Bscraper.py', '--tags', tagsString], {
                cwd: '/opt/build/repo' // Netlify build directory
            });

            let output = '';
            let error = '';

            scraper.stdout.on('data', (data) => {
                output += data.toString();
            });

            scraper.stderr.on('data', (data) => {
                error += data.toString();
            });

            scraper.on('close', (code) => {
                if (code === 0) {
                    resolve({
                        statusCode: 200,
                        body: JSON.stringify({ 
                            success: true, 
                            message: 'Scraping completed successfully',
                            output: output
                        })
                    });
                } else {
                    resolve({
                        statusCode: 500,
                        body: JSON.stringify({ 
                            error: 'Scraping failed', 
                            details: error 
                        })
                    });
                }
            });
        });

    } catch (error) {
        return {
            statusCode: 500,
            body: JSON.stringify({ error: error.message })
        };
    }
};
