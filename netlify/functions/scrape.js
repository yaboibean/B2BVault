const { spawn } = require('child_process');
const path = require('path');

exports.handler = async (event, context) => {
  // Set CORS headers
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'POST, GET, OPTIONS'
  };

  // Handle OPTIONS request for CORS
  if (event.httpMethod === 'OPTIONS') {
    return {
      statusCode: 200,
      headers,
      body: ''
    };
  }

  if (event.httpMethod !== 'POST') {
    return {
      statusCode: 405,
      headers,
      body: JSON.stringify({ error: 'Method not allowed' })
    };
  }

  try {
    const { tags } = JSON.parse(event.body);
    
    if (!tags || !Array.isArray(tags)) {
      return {
        statusCode: 400,
        headers,
        body: JSON.stringify({ error: 'Tags array is required' })
      };
    }

    // For Netlify deployment, we'll trigger the scraping process
    // Note: This is a simplified version - full scraping would need a more robust solution
    
    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({
        success: true,
        message: `Scraping initiated for tags: ${tags.join(', ')}`,
        note: 'This is a demo response. For full functionality, implement with a proper backend service.'
      })
    };

  } catch (error) {
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({ 
        error: 'Internal server error',
        details: error.message 
      })
    };
  }
};
        return {
            statusCode: 500,
            body: JSON.stringify({ error: error.message })
        };
    }
};
