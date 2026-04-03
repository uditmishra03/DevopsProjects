# Real-Time Earth Viewer Platform

## Project Overview
Build a platform that aggregates real-time satellite imagery, webcams, and live feeds from around the world, allowing users to virtually "visit" any location in real-time.

## Data Sources & Integration

### 1. Satellite Imagery APIs
- **NASA Earth Imagery API** - Free, real-time satellite data
- **Sentinel Hub API** - European Space Agency satellite data
- **Planet Labs API** - High-resolution commercial satellite imagery
- **Google Earth Engine** - Massive satellite data archive
- **USGS Earth Explorer** - US geological survey imagery

### 2. Live Webcam Networks
- **Windy.com Webcams** - Weather webcams worldwide
- **EarthCam Network** - Tourist and city webcams
- **YouTube Live Streams** - Public live streams from locations
- **Traffic Cameras** - Government traffic monitoring cameras
- **Weather Station Cameras** - Meteorological webcams

### 3. Drone/IoT Camera Networks
- **Custom IoT cameras** deployed at specific locations
- **Agricultural monitoring cameras** for farms
- **Security cameras** (public access only)

## AWS Architecture

### Core Infrastructure
```yaml
# serverless.yml
service: real-time-earth-viewer

provider:
  name: aws
  runtime: nodejs18.x
  region: us-east-1
  environment:
    LOCATIONS_TABLE: ${self:service}-locations-${opt:stage}
    FEEDS_TABLE: ${self:service}-feeds-${opt:stage}
    IMAGES_BUCKET: ${self:service}-images-${opt:stage}
    WEBSOCKET_TABLE: ${self:service}-connections-${opt:stage}

functions:
  # WebSocket API for real-time updates
  websocketConnect:
    handler: src/websocket/connect.handler
    events:
      - websocket: $connect
  
  websocketDisconnect:
    handler: src/websocket/disconnect.handler
    events:
      - websocket: $disconnect
  
  # Location and feed management
  searchLocations:
    handler: src/handlers/searchLocations.handler
    events:
      - http:
          path: /locations/search
          method: get
          cors: true
  
  getFeedsByLocation:
    handler: src/handlers/getFeedsByLocation.handler
    events:
      - http:
          path: /feeds/{locationId}
          method: get
          cors: true
  
  # Image processing and caching
  processImageFeed:
    handler: src/handlers/processImageFeed.handler
    events:
      - schedule: rate(5 minutes)
    timeout: 300
  
  # Satellite data fetcher
  fetchSatelliteData:
    handler: src/handlers/fetchSatelliteData.handler
    events:
      - schedule: rate(30 minutes)
    timeout: 900

resources:
  Resources:
    # DynamoDB Tables
    LocationsTable:
      Type: AWS::DynamoDB::Table
      Properties:
        TableName: ${self:provider.environment.LOCATIONS_TABLE}
        AttributeDefinitions:
          - AttributeName: locationId
            AttributeType: S
          - AttributeName: country
            AttributeType: S
        KeySchema:
          - AttributeName: locationId
            KeyType: HASH
        GlobalSecondaryIndexes:
          - IndexName: CountryIndex
            KeySchema:
              - AttributeName: country
                KeyType: HASH
            Projection:
              ProjectionType: ALL
        BillingMode: PAY_PER_REQUEST
    
    FeedsTable:
      Type: AWS::DynamoDB::Table
      Properties:
        TableName: ${self:provider.environment.FEEDS_TABLE}
        AttributeDefinitions:
          - AttributeName: feedId
            AttributeType: S
          - AttributeName: locationId
            AttributeType: S
        KeySchema:
          - AttributeName: feedId
            KeyType: HASH
        GlobalSecondaryIndexes:
          - IndexName: LocationIndex
            KeySchema:
              - AttributeName: locationId
                KeyType: HASH
            Projection:
              ProjectionType: ALL
        BillingMode: PAY_PER_REQUEST
    
    # S3 Bucket for image storage
    ImagesBucket:
      Type: AWS::S3::Bucket
      Properties:
        BucketName: ${self:provider.environment.IMAGES_BUCKET}
        CorsConfiguration:
          CorsRules:
            - AllowedHeaders: ['*']
              AllowedMethods: [GET, PUT, POST]
              AllowedOrigins: ['*']
    
    # CloudFront for fast image delivery
    ImagesCDN:
      Type: AWS::CloudFront::Distribution
      Properties:
        DistributionConfig:
          Origins:
            - DomainName: !GetAtt ImagesBucket.RegionalDomainName
              Id: S3Origin
              S3OriginConfig:
                OriginAccessIdentity: ''
          Enabled: true
          DefaultCacheBehavior:
            TargetOriginId: S3Origin
            ViewerProtocolPolicy: redirect-to-https
            CachePolicyId: 4135ea2d-6df8-44a3-9df3-4b5a84be39ad # Managed caching policy
```

## Backend Implementation

### Location Search Handler
```javascript
// src/handlers/searchLocations.js
const AWS = require('aws-sdk');
const dynamodb = new AWS.DynamoDB.DocumentClient();

exports.handler = async (event) => {
  const { query, country, type, lat, lng, radius } = event.queryStringParameters || {};
  
  try {
    let params = {
      TableName: process.env.LOCATIONS_TABLE
    };
    
    if (country) {
      params.IndexName = 'CountryIndex';
      params.KeyConditionExpression = 'country = :country';
      params.ExpressionAttributeValues = { ':country': country };
    } else {
      params = { ...params, ...{ ScanFilter: {} } };
    }
    
    if (query) {
      params.FilterExpression = 'contains(#name, :query) OR contains(description, :query)';
      params.ExpressionAttributeNames = { '#name': 'name' };
      params.ExpressionAttributeValues = { 
        ...params.ExpressionAttributeValues,
        ':query': query 
      };
    }
    
    const result = country ? 
      await dynamodb.query(params).promise() : 
      await dynamodb.scan(params).promise();
    
    let locations = result.Items;
    
    // Filter by proximity if coordinates provided
    if (lat && lng && radius) {
      locations = locations.filter(location => {
        const distance = calculateDistance(
          parseFloat(lat), parseFloat(lng),
          location.latitude, location.longitude
        );
        return distance <= parseFloat(radius);
      });
    }
    
    return {
      statusCode: 200,
      headers: { 'Access-Control-Allow-Origin': '*' },
      body: JSON.stringify({
        locations: locations.slice(0, 50), // Limit results
        total: locations.length
      })
    };
  } catch (error) {
    console.error('Search error:', error);
    return {
      statusCode: 500,
      headers: { 'Access-Control-Allow-Origin': '*' },
      body: JSON.stringify({ error: 'Search failed' })
    };
  }
};

function calculateDistance(lat1, lon1, lat2, lon2) {
  const R = 6371; // Earth's radius in km
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLon/2) * Math.sin(dLon/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c;
}
```

### Satellite Data Fetcher
```javascript
// src/handlers/fetchSatelliteData.js
const AWS = require('aws-sdk');
const axios = require('axios');
const s3 = new AWS.S3();
const dynamodb = new AWS.DynamoDB.DocumentClient();

exports.handler = async (event) => {
  try {
    // Get all active locations
    const locations = await dynamodb.scan({
      TableName: process.env.LOCATIONS_TABLE,
      FilterExpression: '#status = :active',
      ExpressionAttributeNames: { '#status': 'status' },
      ExpressionAttributeValues: { ':active': 'active' }
    }).promise();
    
    for (const location of locations.Items) {
      await Promise.all([
        fetchNASAImagery(location),
        fetchSentinelImagery(location),
        fetchWeatherData(location)
      ]);
    }
    
    return { statusCode: 200, body: 'Satellite data updated' };
  } catch (error) {
    console.error('Satellite fetch error:', error);
    return { statusCode: 500, body: 'Failed to fetch satellite data' };
  }
};

async function fetchNASAImagery(location) {
  try {
    const { latitude, longitude, locationId } = location;
    const date = new Date().toISOString().split('T')[0];
    
    // NASA Earth Imagery API
    const response = await axios.get('https://api.nasa.gov/planetary/earth/imagery', {
      params: {
        lon: longitude,
        lat: latitude,
        date: date,
        dim: 0.10, // Image width/height in degrees
        api_key: process.env.NASA_API_KEY
      },
      responseType: 'arraybuffer'
    });
    
    if (response.status === 200) {
      const imageKey = `satellite/${locationId}/${date}-nasa.jpg`;
      
      await s3.putObject({
        Bucket: process.env.IMAGES_BUCKET,
        Key: imageKey,
        Body: response.data,
        ContentType: 'image/jpeg',
        Metadata: {
          source: 'nasa',
          location: locationId,
          timestamp: new Date().toISOString()
        }
      }).promise();
      
      // Update feed record
      await updateFeedRecord(locationId, 'satellite-nasa', imageKey);
    }
  } catch (error) {
    console.error(`NASA imagery fetch failed for ${location.locationId}:`, error.message);
  }
}

async function fetchSentinelImagery(location) {
  try {
    const { latitude, longitude, locationId } = location;
    
    // Sentinel Hub API (requires authentication)
    const response = await axios.post('https://services.sentinel-hub.com/ogc/wms/your-instance-id', {
      // Sentinel Hub WMS request parameters
      service: 'WMS',
      request: 'GetMap',
      layers: 'TRUE_COLOR',
      bbox: `${longitude-0.01},${latitude-0.01},${longitude+0.01},${latitude+0.01}`,
      width: 512,
      height: 512,
      format: 'image/jpeg'
    }, {
      headers: {
        'Authorization': `Bearer ${process.env.SENTINEL_TOKEN}`
      },
      responseType: 'arraybuffer'
    });
    
    if (response.status === 200) {
      const imageKey = `satellite/${locationId}/${Date.now()}-sentinel.jpg`;
      
      await s3.putObject({
        Bucket: process.env.IMAGES_BUCKET,
        Key: imageKey,
        Body: response.data,
        ContentType: 'image/jpeg'
      }).promise();
      
      await updateFeedRecord(locationId, 'satellite-sentinel', imageKey);
    }
  } catch (error) {
    console.error(`Sentinel imagery fetch failed for ${location.locationId}:`, error.message);
  }
}

async function updateFeedRecord(locationId, feedType, imageKey) {
  await dynamodb.put({
    TableName: process.env.FEEDS_TABLE,
    Item: {
      feedId: `${locationId}-${feedType}`,
      locationId,
      type: feedType,
      imageUrl: `https://${process.env.IMAGES_BUCKET}.s3.amazonaws.com/${imageKey}`,
      lastUpdated: new Date().toISOString(),
      status: 'active'
    }
  }).promise();
}
```### W
ebcam Feed Processor
```javascript
// src/handlers/processImageFeed.js
const AWS = require('aws-sdk');
const axios = require('axios');
const s3 = new AWS.S3();
const dynamodb = new AWS.DynamoDB.DocumentClient();

exports.handler = async (event) => {
  try {
    // Get all webcam feeds
    const feeds = await dynamodb.scan({
      TableName: process.env.FEEDS_TABLE,
      FilterExpression: '#type = :webcam AND #status = :active',
      ExpressionAttributeNames: { 
        '#type': 'type',
        '#status': 'status' 
      },
      ExpressionAttributeValues: { 
        ':webcam': 'webcam',
        ':active': 'active' 
      }
    }).promise();
    
    const updatePromises = feeds.Items.map(feed => processWebcamFeed(feed));
    await Promise.all(updatePromises);
    
    return { statusCode: 200, body: 'Webcam feeds processed' };
  } catch (error) {
    console.error('Feed processing error:', error);
    return { statusCode: 500, body: 'Failed to process feeds' };
  }
};

async function processWebcamFeed(feed) {
  try {
    const response = await axios.get(feed.sourceUrl, {
      responseType: 'arraybuffer',
      timeout: 10000
    });
    
    if (response.status === 200) {
      const imageKey = `webcam/${feed.locationId}/${Date.now()}.jpg`;
      
      await s3.putObject({
        Bucket: process.env.IMAGES_BUCKET,
        Key: imageKey,
        Body: response.data,
        ContentType: 'image/jpeg',
        Metadata: {
          source: 'webcam',
          feedId: feed.feedId,
          timestamp: new Date().toISOString()
        }
      }).promise();
      
      // Update feed with new image
      await dynamodb.update({
        TableName: process.env.FEEDS_TABLE,
        Key: { feedId: feed.feedId },
        UpdateExpression: 'SET imageUrl = :url, lastUpdated = :timestamp',
        ExpressionAttributeValues: {
          ':url': `https://${process.env.IMAGES_BUCKET}.s3.amazonaws.com/${imageKey}`,
          ':timestamp': new Date().toISOString()
        }
      }).promise();
      
      // Notify connected clients via WebSocket
      await notifyClients(feed.locationId, {
        type: 'FEED_UPDATE',
        feedId: feed.feedId,
        imageUrl: `https://${process.env.IMAGES_BUCKET}.s3.amazonaws.com/${imageKey}`,
        timestamp: new Date().toISOString()
      });
    }
  } catch (error) {
    console.error(`Failed to process feed ${feed.feedId}:`, error.message);
  }
}

async function notifyClients(locationId, message) {
  const apiGateway = new AWS.ApiGatewayManagementApi({
    endpoint: process.env.WEBSOCKET_ENDPOINT
  });
  
  // Get connected clients for this location
  const connections = await dynamodb.query({
    TableName: process.env.WEBSOCKET_TABLE,
    IndexName: 'LocationIndex',
    KeyConditionExpression: 'locationId = :locationId',
    ExpressionAttributeValues: { ':locationId': locationId }
  }).promise();
  
  const notifications = connections.Items.map(async (connection) => {
    try {
      await apiGateway.postToConnection({
        ConnectionId: connection.connectionId,
        Data: JSON.stringify(message)
      }).promise();
    } catch (error) {
      if (error.statusCode === 410) {
        // Connection is stale, remove it
        await dynamodb.delete({
          TableName: process.env.WEBSOCKET_TABLE,
          Key: { connectionId: connection.connectionId }
        }).promise();
      }
    }
  });
  
  await Promise.all(notifications);
}
```

## Frontend React Application

### Main Map Component
```jsx
// src/components/EarthViewer.jsx
import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './EarthViewer.css';

const EarthViewer = () => {
  const [locations, setLocations] = useState([]);
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [feeds, setFeeds] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const wsRef = useRef(null);
  
  const API_BASE = process.env.REACT_APP_API_URL;
  const WS_URL = process.env.REACT_APP_WS_URL;
  
  useEffect(() => {
    loadInitialLocations();
    connectWebSocket();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);
  
  const loadInitialLocations = async () => {
    try {
      const response = await fetch(`${API_BASE}/locations/search?limit=100`);
      const data = await response.json();
      setLocations(data.locations);
    } catch (error) {
      console.error('Failed to load locations:', error);
    }
  };
  
  const connectWebSocket = () => {
    wsRef.current = new WebSocket(WS_URL);
    
    wsRef.current.onmessage = (event) => {
      const message = JSON.parse(event.data);
      
      if (message.type === 'FEED_UPDATE') {
        setFeeds(prevFeeds => 
          prevFeeds.map(feed => 
            feed.feedId === message.feedId 
              ? { ...feed, imageUrl: message.imageUrl, lastUpdated: message.timestamp }
              : feed
          )
        );
      }
    };
    
    wsRef.current.onclose = () => {
      // Reconnect after 3 seconds
      setTimeout(connectWebSocket, 3000);
    };
  };
  
  const searchLocations = async () => {
    if (!searchQuery.trim()) return;
    
    setLoading(true);
    try {
      const response = await fetch(
        `${API_BASE}/locations/search?query=${encodeURIComponent(searchQuery)}`
      );
      const data = await response.json();
      setLocations(data.locations);
    } catch (error) {
      console.error('Search failed:', error);
    }
    setLoading(false);
  };
  
  const selectLocation = async (location) => {
    setSelectedLocation(location);
    
    try {
      const response = await fetch(`${API_BASE}/feeds/${location.locationId}`);
      const data = await response.json();
      setFeeds(data.feeds);
      
      // Subscribe to updates for this location
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          action: 'subscribe',
          locationId: location.locationId
        }));
      }
    } catch (error) {
      console.error('Failed to load feeds:', error);
    }
  };
  
  const customIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
  });
  
  return (
    <div className="earth-viewer">
      <div className="sidebar">
        <div className="search-section">
          <h2>🌍 Real-Time Earth Viewer</h2>
          <div className="search-bar">
            <input
              type="text"
              placeholder="Search locations (e.g., Bhopal, Mount Fuji, Delhi Highway)"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && searchLocations()}
            />
            <button onClick={searchLocations} disabled={loading}>
              {loading ? '🔍' : '🔍'}
            </button>
          </div>
        </div>
        
        <div className="locations-list">
          <h3>Available Locations ({locations.length})</h3>
          {locations.map(location => (
            <div 
              key={location.locationId}
              className={`location-item ${selectedLocation?.locationId === location.locationId ? 'selected' : ''}`}
              onClick={() => selectLocation(location)}
            >
              <div className="location-info">
                <h4>{location.name}</h4>
                <p>{location.description}</p>
                <span className="location-meta">
                  📍 {location.country} • {location.feedCount || 0} feeds
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      <div className="main-content">
        <div className="map-container">
          <MapContainer
            center={[20.5937, 78.9629]} // Center of India
            zoom={5}
            style={{ height: '50vh', width: '100%' }}
          >
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            />
            {locations.map(location => (
              <Marker
                key={location.locationId}
                position={[location.latitude, location.longitude]}
                icon={customIcon}
                eventHandlers={{
                  click: () => selectLocation(location)
                }}
              >
                <Popup>
                  <div>
                    <h4>{location.name}</h4>
                    <p>{location.description}</p>
                    <button onClick={() => selectLocation(location)}>
                      View Feeds
                    </button>
                  </div>
                </Popup>
              </Marker>
            ))}
          </MapContainer>
        </div>
        
        {selectedLocation && (
          <div className="feeds-section">
            <h3>📡 Live Feeds for {selectedLocation.name}</h3>
            <div className="feeds-grid">
              {feeds.map(feed => (
                <div key={feed.feedId} className="feed-card">
                  <div className="feed-header">
                    <span className="feed-type">{getFeedTypeIcon(feed.type)} {feed.type}</span>
                    <span className="feed-time">
                      {new Date(feed.lastUpdated).toLocaleTimeString()}
                    </span>
                  </div>
                  <div className="feed-image">
                    <img 
                      src={feed.imageUrl} 
                      alt={`${feed.type} view of ${selectedLocation.name}`}
                      onError={(e) => {
                        e.target.src = '/placeholder-image.jpg';
                      }}
                    />
                  </div>
                  <div className="feed-info">
                    <p>{feed.description || 'Live view'}</p>
                    {feed.weather && (
                      <div className="weather-info">
                        🌡️ {feed.weather.temperature}°C • {feed.weather.condition}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const getFeedTypeIcon = (type) => {
  const icons = {
    'satellite-nasa': '🛰️',
    'satellite-sentinel': '🛰️',
    'webcam': '📹',
    'weather': '🌤️',
    'traffic': '🚗',
    'drone': '🚁'
  };
  return icons[type] || '📷';
};

export default EarthViewer;
```

### CSS Styles
```css
/* src/components/EarthViewer.css */
.earth-viewer {
  display: flex;
  height: 100vh;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.sidebar {
  width: 350px;
  background: #f8f9fa;
  border-right: 1px solid #dee2e6;
  overflow-y: auto;
}

.search-section {
  padding: 20px;
  border-bottom: 1px solid #dee2e6;
}

.search-section h2 {
  margin: 0 0 15px 0;
  color: #2c3e50;
}

.search-bar {
  display: flex;
  gap: 10px;
}

.search-bar input {
  flex: 1;
  padding: 10px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 14px;
}

.search-bar button {
  padding: 10px 15px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.search-bar button:hover {
  background: #0056b3;
}

.locations-list {
  padding: 20px;
}

.locations-list h3 {
  margin: 0 0 15px 0;
  color: #495057;
}

.location-item {
  padding: 15px;
  margin-bottom: 10px;
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.location-item:hover {
  border-color: #007bff;
  box-shadow: 0 2px 4px rgba(0,123,255,0.1);
}

.location-item.selected {
  border-color: #007bff;
  background: #e3f2fd;
}

.location-info h4 {
  margin: 0 0 5px 0;
  color: #2c3e50;
}

.location-info p {
  margin: 0 0 8px 0;
  color: #6c757d;
  font-size: 14px;
}

.location-meta {
  font-size: 12px;
  color: #868e96;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.map-container {
  border-bottom: 1px solid #dee2e6;
}

.feeds-section {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.feeds-section h3 {
  margin: 0 0 20px 0;
  color: #2c3e50;
}

.feeds-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.feed-card {
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.feed-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 15px;
  background: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
}

.feed-type {
  font-weight: 600;
  color: #495057;
  text-transform: capitalize;
}

.feed-time {
  font-size: 12px;
  color: #6c757d;
}

.feed-image {
  position: relative;
  height: 200px;
  overflow: hidden;
}

.feed-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.feed-info {
  padding: 15px;
}

.feed-info p {
  margin: 0 0 10px 0;
  color: #495057;
}

.weather-info {
  font-size: 14px;
  color: #28a745;
  background: #d4edda;
  padding: 8px 12px;
  border-radius: 4px;
}

/* Responsive design */
@media (max-width: 768px) {
  .earth-viewer {
    flex-direction: column;
  }
  
  .sidebar {
    width: 100%;
    height: 300px;
  }
  
  .feeds-grid {
    grid-template-columns: 1fr;
  }
}
```#
# Data Seeding Script

### Location and Feed Setup
```javascript
// scripts/seedData.js
const AWS = require('aws-sdk');
const dynamodb = new AWS.DynamoDB.DocumentClient();

const locations = [
  {
    locationId: 'bhopal-farm-001',
    name: 'Bhopal Agricultural Area',
    description: 'Farming region near Bhopal, Madhya Pradesh',
    country: 'India',
    latitude: 23.2599,
    longitude: 77.4126,
    type: 'agricultural',
    status: 'active'
  },
  {
    locationId: 'delhi-mumbai-highway-km70',
    name: 'Delhi-Mumbai Highway KM 70',
    description: 'McDonald\'s at foothill location on NH48',
    country: 'India',
    latitude: 28.4595,
    longitude: 77.0266,
    type: 'commercial',
    status: 'active'
  },
  {
    locationId: 'mount-fuji-japan',
    name: 'Mount Fuji',
    description: 'Iconic volcanic mountain in Japan',
    country: 'Japan',
    latitude: 35.3606,
    longitude: 138.7274,
    type: 'landmark',
    status: 'active'
  },
  {
    locationId: 'gurgaon-city-center',
    name: 'Gurgaon City Center',
    description: 'Urban center of Gurgaon, Haryana',
    country: 'India',
    latitude: 28.4595,
    longitude: 77.0266,
    type: 'urban',
    status: 'active'
  },
  {
    locationId: 'mumbai-marine-drive',
    name: 'Mumbai Marine Drive',
    description: 'Famous waterfront promenade in Mumbai',
    country: 'India',
    latitude: 18.9434,
    longitude: 72.8234,
    type: 'tourist',
    status: 'active'
  }
];

const feeds = [
  // Bhopal Farm feeds
  {
    feedId: 'bhopal-farm-001-satellite-nasa',
    locationId: 'bhopal-farm-001',
    type: 'satellite-nasa',
    description: 'NASA satellite view of agricultural area',
    sourceUrl: 'nasa-api',
    updateInterval: 1800, // 30 minutes
    status: 'active'
  },
  {
    feedId: 'bhopal-farm-001-weather',
    locationId: 'bhopal-farm-001',
    type: 'weather',
    description: 'Weather station camera',
    sourceUrl: 'https://example-weather-cam.com/bhopal/current.jpg',
    updateInterval: 300, // 5 minutes
    status: 'active'
  },
  
  // Delhi-Mumbai Highway feeds
  {
    feedId: 'delhi-mumbai-highway-km70-traffic',
    locationId: 'delhi-mumbai-highway-km70',
    type: 'traffic',
    description: 'Highway traffic camera',
    sourceUrl: 'https://traffic-cams.gov.in/nh48/km70.jpg',
    updateInterval: 60, // 1 minute
    status: 'active'
  },
  {
    feedId: 'delhi-mumbai-highway-km70-satellite-sentinel',
    locationId: 'delhi-mumbai-highway-km70',
    type: 'satellite-sentinel',
    description: 'Sentinel satellite imagery',
    sourceUrl: 'sentinel-api',
    updateInterval: 1800,
    status: 'active'
  },
  
  // Mount Fuji feeds
  {
    feedId: 'mount-fuji-japan-webcam-1',
    locationId: 'mount-fuji-japan',
    type: 'webcam',
    description: 'Live webcam from Kawaguchi Lake',
    sourceUrl: 'https://fuji-webcam.jp/live/kawaguchi.jpg',
    updateInterval: 300,
    status: 'active'
  },
  {
    feedId: 'mount-fuji-japan-webcam-2',
    locationId: 'mount-fuji-japan',
    type: 'webcam',
    description: 'Live webcam from Hakone',
    sourceUrl: 'https://fuji-webcam.jp/live/hakone.jpg',
    updateInterval: 300,
    status: 'active'
  },
  {
    feedId: 'mount-fuji-japan-satellite-nasa',
    locationId: 'mount-fuji-japan',
    type: 'satellite-nasa',
    description: 'NASA satellite view',
    sourceUrl: 'nasa-api',
    updateInterval: 1800,
    status: 'active'
  }
];

async function seedData() {
  try {
    console.log('Seeding locations...');
    for (const location of locations) {
      await dynamodb.put({
        TableName: process.env.LOCATIONS_TABLE,
        Item: {
          ...location,
          createdAt: new Date().toISOString(),
          feedCount: feeds.filter(f => f.locationId === location.locationId).length
        }
      }).promise();
      console.log(`✓ Added location: ${location.name}`);
    }
    
    console.log('\nSeeding feeds...');
    for (const feed of feeds) {
      await dynamodb.put({
        TableName: process.env.FEEDS_TABLE,
        Item: {
          ...feed,
          createdAt: new Date().toISOString(),
          lastUpdated: new Date().toISOString()
        }
      }).promise();
      console.log(`✓ Added feed: ${feed.feedId}`);
    }
    
    console.log('\n🎉 Data seeding completed successfully!');
  } catch (error) {
    console.error('❌ Seeding failed:', error);
  }
}

seedData();
```

## Advanced Features

### 1. Weather Integration
```javascript
// src/services/weatherService.js
const axios = require('axios');

class WeatherService {
  constructor() {
    this.apiKey = process.env.OPENWEATHER_API_KEY;
    this.baseUrl = 'https://api.openweathermap.org/data/2.5';
  }
  
  async getCurrentWeather(lat, lon) {
    try {
      const response = await axios.get(`${this.baseUrl}/weather`, {
        params: {
          lat,
          lon,
          appid: this.apiKey,
          units: 'metric'
        }
      });
      
      return {
        temperature: Math.round(response.data.main.temp),
        condition: response.data.weather[0].description,
        humidity: response.data.main.humidity,
        windSpeed: response.data.wind.speed,
        icon: response.data.weather[0].icon
      };
    } catch (error) {
      console.error('Weather fetch failed:', error);
      return null;
    }
  }
  
  async getWeatherForecast(lat, lon) {
    try {
      const response = await axios.get(`${this.baseUrl}/forecast`, {
        params: {
          lat,
          lon,
          appid: this.apiKey,
          units: 'metric'
        }
      });
      
      return response.data.list.slice(0, 8).map(item => ({
        time: new Date(item.dt * 1000).toLocaleTimeString(),
        temperature: Math.round(item.main.temp),
        condition: item.weather[0].description,
        icon: item.weather[0].icon
      }));
    } catch (error) {
      console.error('Forecast fetch failed:', error);
      return [];
    }
  }
}

module.exports = WeatherService;
```

### 2. Image Processing with AI
```javascript
// src/services/imageAnalysisService.js
const AWS = require('aws-sdk');
const rekognition = new AWS.Rekognition();

class ImageAnalysisService {
  async analyzeImage(imageBuffer) {
    try {
      // Detect objects and scenes
      const objectsResult = await rekognition.detectLabels({
        Image: { Bytes: imageBuffer },
        MaxLabels: 10,
        MinConfidence: 70
      }).promise();
      
      // Detect text in image
      const textResult = await rekognition.detectText({
        Image: { Bytes: imageBuffer }
      }).promise();
      
      // Analyze image for inappropriate content
      const moderationResult = await rekognition.detectModerationLabels({
        Image: { Bytes: imageBuffer },
        MinConfidence: 60
      }).promise();
      
      return {
        objects: objectsResult.Labels.map(label => ({
          name: label.Name,
          confidence: label.Confidence
        })),
        text: textResult.TextDetections
          .filter(text => text.Type === 'LINE')
          .map(text => text.DetectedText),
        isAppropriate: moderationResult.ModerationLabels.length === 0,
        moderationFlags: moderationResult.ModerationLabels
      };
    } catch (error) {
      console.error('Image analysis failed:', error);
      return null;
    }
  }
  
  async enhanceImage(imageBuffer) {
    // Use AWS Lambda with OpenCV or similar for image enhancement
    const lambda = new AWS.Lambda();
    
    try {
      const result = await lambda.invoke({
        FunctionName: 'image-enhancement-function',
        Payload: JSON.stringify({
          imageData: imageBuffer.toString('base64')
        })
      }).promise();
      
      const response = JSON.parse(result.Payload);
      return Buffer.from(response.enhancedImage, 'base64');
    } catch (error) {
      console.error('Image enhancement failed:', error);
      return imageBuffer; // Return original if enhancement fails
    }
  }
}

module.exports = ImageAnalysisService;
```

### 3. Mobile App Integration
```javascript
// Mobile push notifications for feed updates
const AWS = require('aws-sdk');
const sns = new AWS.SNS();

class NotificationService {
  async sendPushNotification(deviceTokens, message) {
    const promises = deviceTokens.map(async (token) => {
      try {
        await sns.publish({
          TargetArn: token,
          Message: JSON.stringify({
            default: message.text,
            APNS: JSON.stringify({
              aps: {
                alert: message.text,
                badge: 1,
                sound: 'default'
              },
              customData: message.data
            }),
            GCM: JSON.stringify({
              data: {
                message: message.text,
                ...message.data
              }
            })
          }),
          MessageStructure: 'json'
        }).promise();
      } catch (error) {
        console.error(`Failed to send notification to ${token}:`, error);
      }
    });
    
    await Promise.all(promises);
  }
  
  async notifyLocationUpdate(locationId, updateType) {
    // Get subscribers for this location
    const subscribers = await this.getLocationSubscribers(locationId);
    
    if (subscribers.length > 0) {
      await this.sendPushNotification(
        subscribers.map(s => s.deviceToken),
        {
          text: `New ${updateType} available for your watched location`,
          data: { locationId, updateType }
        }
      );
    }
  }
}
```

## Deployment & Scaling

### Infrastructure as Code
```bash
# Deploy the complete stack
serverless deploy --stage prod

# Set up environment variables
export NASA_API_KEY="your-nasa-api-key"
export SENTINEL_TOKEN="your-sentinel-hub-token"
export OPENWEATHER_API_KEY="your-openweather-key"

# Deploy frontend
npm run build
aws s3 sync build/ s3://earth-viewer-frontend --delete
aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"
```

### Cost Optimization
- Use S3 Intelligent Tiering for image storage
- Implement CloudFront caching with appropriate TTLs
- Use DynamoDB on-demand pricing for unpredictable traffic
- Set up Lambda reserved concurrency for critical functions
- Implement image compression and WebP format conversion

### Monitoring & Analytics
```javascript
// CloudWatch custom metrics
const AWS = require('aws-sdk');
const cloudwatch = new AWS.CloudWatch();

async function trackMetric(metricName, value, unit = 'Count') {
  await cloudwatch.putMetricData({
    Namespace: 'EarthViewer',
    MetricData: [{
      MetricName: metricName,
      Value: value,
      Unit: unit,
      Timestamp: new Date()
    }]
  }).promise();
}

// Usage examples:
await trackMetric('FeedUpdates', 1);
await trackMetric('UserSessions', 1);
await trackMetric('ImageProcessingTime', processingTime, 'Milliseconds');
```

This platform gives you a comprehensive real-time earth viewing system! You can start with basic satellite imagery and webcams, then expand to include weather data, traffic cameras, and even custom IoT cameras for specific locations like your farm in Bhopal.

The architecture is designed to handle thousands of concurrent users and can automatically scale based on demand. Want me to help you implement any specific part or add more advanced features?