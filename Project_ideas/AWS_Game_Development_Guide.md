# AWS Game Development Guide

## Game Types & AWS Architecture

### 1. Endless Runner Games (Subway Surfer, Temple Run style)

**Architecture:**
- **Frontend**: Unity/Unreal Engine or HTML5 Canvas
- **Backend**: AWS Lambda + API Gateway
- **Database**: DynamoDB for player scores/progress
- **Storage**: S3 for game assets
- **CDN**: CloudFront for fast asset delivery
- **Analytics**: Amazon Kinesis for gameplay analytics

**Key Features:**
- Real-time leaderboards
- Player progression tracking
- In-app purchases
- Social sharing

### 2. Match-3 Puzzle Games (Candy Crush style)

**Architecture:**
- **Frontend**: Unity WebGL or React/Vue.js
- **Backend**: AWS AppSync (GraphQL) + Lambda
- **Database**: DynamoDB for game state, RDS for complex queries
- **Real-time**: AWS IoT Core for multiplayer features
- **Push Notifications**: Amazon SNS
- **Analytics**: Amazon Pinpoint

**Key Features:**
- Level progression system
- Lives/energy system
- Social features (friends, competitions)
- Daily challenges

### 3. Word Games (Wordle style)

**Architecture:**
- **Frontend**: React/Vue.js Progressive Web App
- **Backend**: Lambda + API Gateway
- **Database**: DynamoDB for game state
- **Cache**: ElastiCache for word validation
- **Storage**: S3 for word dictionaries
- **Authentication**: Amazon Cognito

**Key Features:**
- Daily puzzles
- Statistics tracking
- Social sharing
- Streak counters

## Sample Implementation: Simple Word Game

Let me create a basic Wordle-style game architecture:## 
Project: AWS Wordle Clone

### Infrastructure Setup

```yaml
# serverless.yml
service: aws-wordle-game

provider:
  name: aws
  runtime: nodejs18.x
  region: us-east-1
  environment:
    WORDS_TABLE: ${self:service}-words-${opt:stage, self:provider.stage}
    GAMES_TABLE: ${self:service}-games-${opt:stage, self:provider.stage}

functions:
  getWord:
    handler: src/handlers/getWord.handler
    events:
      - http:
          path: /word/{date}
          method: get
          cors: true
  
  submitGuess:
    handler: src/handlers/submitGuess.handler
    events:
      - http:
          path: /guess
          method: post
          cors: true

  getStats:
    handler: src/handlers/getStats.handler
    events:
      - http:
          path: /stats/{userId}
          method: get
          cors: true

resources:
  Resources:
    WordsTable:
      Type: AWS::DynamoDB::Table
      Properties:
        TableName: ${self:provider.environment.WORDS_TABLE}
        AttributeDefinitions:
          - AttributeName: date
            AttributeType: S
        KeySchema:
          - AttributeName: date
            KeyType: HASH
        BillingMode: PAY_PER_REQUEST

    GamesTable:
      Type: AWS::DynamoDB::Table
      Properties:
        TableName: ${self:provider.environment.GAMES_TABLE}
        AttributeDefinitions:
          - AttributeName: userId
            AttributeType: S
          - AttributeName: date
            AttributeType: S
        KeySchema:
          - AttributeName: userId
            KeyType: HASH
          - AttributeName: date
            KeyType: RANGE
        BillingMode: PAY_PER_REQUEST
```

### Backend Lambda Functions

```javascript
// src/handlers/getWord.js
const AWS = require('aws-sdk');
const dynamodb = new AWS.DynamoDB.DocumentClient();

exports.handler = async (event) => {
  const { date } = event.pathParameters;
  
  try {
    const result = await dynamodb.get({
      TableName: process.env.WORDS_TABLE,
      Key: { date }
    }).promise();
    
    if (!result.Item) {
      return {
        statusCode: 404,
        headers: { 'Access-Control-Allow-Origin': '*' },
        body: JSON.stringify({ error: 'Word not found for date' })
      };
    }
    
    // Don't return the actual word, just confirm it exists
    return {
      statusCode: 200,
      headers: { 'Access-Control-Allow-Origin': '*' },
      body: JSON.stringify({ 
        date,
        wordLength: result.Item.word.length,
        available: true 
      })
    };
  } catch (error) {
    return {
      statusCode: 500,
      headers: { 'Access-Control-Allow-Origin': '*' },
      body: JSON.stringify({ error: 'Internal server error' })
    };
  }
};
```

```javascript
// src/handlers/submitGuess.js
const AWS = require('aws-sdk');
const dynamodb = new AWS.DynamoDB.DocumentClient();

exports.handler = async (event) => {
  const { userId, date, guess, gameState } = JSON.parse(event.body);
  
  try {
    // Get the target word
    const wordResult = await dynamodb.get({
      TableName: process.env.WORDS_TABLE,
      Key: { date }
    }).promise();
    
    if (!wordResult.Item) {
      return {
        statusCode: 404,
        headers: { 'Access-Control-Allow-Origin': '*' },
        body: JSON.stringify({ error: 'Word not found' })
      };
    }
    
    const targetWord = wordResult.Item.word.toLowerCase();
    const guessWord = guess.toLowerCase();
    
    // Check guess against target word
    const result = checkGuess(guessWord, targetWord);
    const isWin = guessWord === targetWord;
    const isGameOver = isWin || gameState.attempts >= 6;
    
    // Update game state
    const updatedGameState = {
      ...gameState,
      attempts: gameState.attempts + 1,
      guesses: [...gameState.guesses, { word: guessWord, result }],
      isWin,
      isGameOver
    };
    
    // Save game state
    await dynamodb.put({
      TableName: process.env.GAMES_TABLE,
      Item: {
        userId,
        date,
        gameState: updatedGameState,
        updatedAt: new Date().toISOString()
      }
    }).promise();
    
    return {
      statusCode: 200,
      headers: { 'Access-Control-Allow-Origin': '*' },
      body: JSON.stringify({
        result,
        gameState: updatedGameState,
        isWin,
        isGameOver
      })
    };
  } catch (error) {
    return {
      statusCode: 500,
      headers: { 'Access-Control-Allow-Origin': '*' },
      body: JSON.stringify({ error: 'Internal server error' })
    };
  }
};

function checkGuess(guess, target) {
  const result = [];
  const targetArray = target.split('');
  const guessArray = guess.split('');
  
  // First pass: exact matches
  for (let i = 0; i < guessArray.length; i++) {
    if (guessArray[i] === targetArray[i]) {
      result[i] = 'correct';
      targetArray[i] = null; // Mark as used
    }
  }
  
  // Second pass: wrong position
  for (let i = 0; i < guessArray.length; i++) {
    if (result[i]) continue; // Already marked as correct
    
    const letterIndex = targetArray.indexOf(guessArray[i]);
    if (letterIndex !== -1) {
      result[i] = 'present';
      targetArray[letterIndex] = null; // Mark as used
    } else {
      result[i] = 'absent';
    }
  }
  
  return result;
}
```

### Frontend React Component

```jsx
// src/components/WordleGame.jsx
import React, { useState, useEffect } from 'react';
import './WordleGame.css';

const WordleGame = () => {
  const [gameState, setGameState] = useState({
    attempts: 0,
    guesses: [],
    isWin: false,
    isGameOver: false
  });
  const [currentGuess, setCurrentGuess] = useState('');
  const [loading, setLoading] = useState(false);
  
  const today = new Date().toISOString().split('T')[0];
  const API_BASE = process.env.REACT_APP_API_URL;
  
  useEffect(() => {
    loadGameState();
  }, []);
  
  const loadGameState = async () => {
    try {
      const response = await fetch(`${API_BASE}/stats/user123`);
      if (response.ok) {
        const data = await response.json();
        setGameState(data.gameState || gameState);
      }
    } catch (error) {
      console.error('Failed to load game state:', error);
    }
  };
  
  const submitGuess = async () => {
    if (currentGuess.length !== 5) return;
    
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/guess`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userId: 'user123',
          date: today,
          guess: currentGuess,
          gameState
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        setGameState(data.gameState);
        setCurrentGuess('');
      }
    } catch (error) {
      console.error('Failed to submit guess:', error);
    }
    setLoading(false);
  };
  
  const handleKeyPress = (key) => {
    if (gameState.isGameOver) return;
    
    if (key === 'ENTER') {
      submitGuess();
    } else if (key === 'BACKSPACE') {
      setCurrentGuess(prev => prev.slice(0, -1));
    } else if (key.match(/[A-Z]/) && currentGuess.length < 5) {
      setCurrentGuess(prev => prev + key);
    }
  };
  
  return (
    <div className="wordle-game">
      <h1>AWS Wordle</h1>
      
      <div className="game-board">
        {Array.from({ length: 6 }, (_, rowIndex) => (
          <div key={rowIndex} className="guess-row">
            {Array.from({ length: 5 }, (_, colIndex) => {
              const guess = gameState.guesses[rowIndex];
              const isCurrentRow = rowIndex === gameState.attempts && !gameState.isGameOver;
              const letter = isCurrentRow ? currentGuess[colIndex] || '' : 
                           guess ? guess.word[colIndex] || '' : '';
              const status = guess ? guess.result[colIndex] : '';
              
              return (
                <div 
                  key={colIndex} 
                  className={`letter-box ${status}`}
                >
                  {letter.toUpperCase()}
                </div>
              );
            })}
          </div>
        ))}
      </div>
      
      <div className="keyboard">
        {['QWERTYUIOP', 'ASDFGHJKL', 'ZXCVBNM'].map((row, rowIndex) => (
          <div key={rowIndex} className="keyboard-row">
            {rowIndex === 2 && (
              <button 
                className="key special-key" 
                onClick={() => handleKeyPress('ENTER')}
                disabled={loading}
              >
                ENTER
              </button>
            )}
            {row.split('').map(key => (
              <button
                key={key}
                className="key"
                onClick={() => handleKeyPress(key)}
                disabled={loading}
              >
                {key}
              </button>
            ))}
            {rowIndex === 2 && (
              <button 
                className="key special-key" 
                onClick={() => handleKeyPress('BACKSPACE')}
                disabled={loading}
              >
                ⌫
              </button>
            )}
          </div>
        ))}
      </div>
      
      {gameState.isGameOver && (
        <div className="game-over">
          <h2>{gameState.isWin ? '🎉 You Won!' : '😔 Game Over'}</h2>
          <p>Attempts: {gameState.attempts}/6</p>
        </div>
      )}
    </div>
  );
};

export default WordleGame;
```### CSS S
tyles

```css
/* src/components/WordleGame.css */
.wordle-game {
  max-width: 500px;
  margin: 0 auto;
  padding: 20px;
  font-family: 'Arial', sans-serif;
  text-align: center;
}

.game-board {
  margin: 20px 0;
}

.guess-row {
  display: flex;
  justify-content: center;
  gap: 5px;
  margin-bottom: 5px;
}

.letter-box {
  width: 60px;
  height: 60px;
  border: 2px solid #d3d6da;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: bold;
  text-transform: uppercase;
  background-color: white;
}

.letter-box.correct {
  background-color: #6aaa64;
  color: white;
  border-color: #6aaa64;
}

.letter-box.present {
  background-color: #c9b458;
  color: white;
  border-color: #c9b458;
}

.letter-box.absent {
  background-color: #787c7e;
  color: white;
  border-color: #787c7e;
}

.keyboard {
  margin-top: 20px;
}

.keyboard-row {
  display: flex;
  justify-content: center;
  gap: 6px;
  margin-bottom: 8px;
}

.key {
  min-width: 43px;
  height: 58px;
  border: none;
  border-radius: 4px;
  background-color: #d3d6da;
  color: #1a1a1b;
  font-weight: bold;
  cursor: pointer;
  font-size: 12px;
}

.key:hover {
  background-color: #bbb;
}

.key:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.special-key {
  min-width: 65px;
  font-size: 10px;
}

.game-over {
  margin-top: 20px;
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 8px;
}
```

## Advanced Game Features

### 1. Real-time Multiplayer (for competitive games)

```javascript
// WebSocket connection using AWS IoT Core
const AWS = require('aws-sdk');

class GameMultiplayer {
  constructor(gameId, playerId) {
    this.gameId = gameId;
    this.playerId = playerId;
    this.iotData = new AWS.IotData({
      endpoint: process.env.IOT_ENDPOINT
    });
  }
  
  async sendMove(moveData) {
    const message = {
      gameId: this.gameId,
      playerId: this.playerId,
      type: 'MOVE',
      data: moveData,
      timestamp: Date.now()
    };
    
    await this.iotData.publish({
      topic: `game/${this.gameId}/moves`,
      payload: JSON.stringify(message)
    }).promise();
  }
  
  async broadcastGameState(gameState) {
    const message = {
      gameId: this.gameId,
      type: 'GAME_STATE',
      data: gameState,
      timestamp: Date.now()
    };
    
    await this.iotData.publish({
      topic: `game/${this.gameId}/state`,
      payload: JSON.stringify(message)
    }).promise();
  }
}
```

### 2. Leaderboards with DynamoDB

```javascript
// Leaderboard handler
const AWS = require('aws-sdk');
const dynamodb = new AWS.DynamoDB.DocumentClient();

exports.updateLeaderboard = async (event) => {
  const { userId, score, gameType } = JSON.parse(event.body);
  
  try {
    // Update player's best score
    await dynamodb.update({
      TableName: process.env.LEADERBOARD_TABLE,
      Key: { gameType, userId },
      UpdateExpression: 'SET #score = if_not_exists(#score, :score), #bestScore = if_not_exists(#bestScore, :score), #bestScore = if_(:score > #bestScore, :score, #bestScore), #updatedAt = :now',
      ExpressionAttributeNames: {
        '#score': 'score',
        '#bestScore': 'bestScore',
        '#updatedAt': 'updatedAt'
      },
      ExpressionAttributeValues: {
        ':score': score,
        ':now': new Date().toISOString()
      }
    }).promise();
    
    // Get top 10 players
    const result = await dynamodb.query({
      TableName: process.env.LEADERBOARD_TABLE,
      KeyConditionExpression: 'gameType = :gameType',
      ExpressionAttributeValues: { ':gameType': gameType },
      ScanIndexForward: false,
      Limit: 10
    }).promise();
    
    return {
      statusCode: 200,
      headers: { 'Access-Control-Allow-Origin': '*' },
      body: JSON.stringify({
        leaderboard: result.Items,
        playerRank: await getPlayerRank(gameType, userId)
      })
    };
  } catch (error) {
    return {
      statusCode: 500,
      headers: { 'Access-Control-Allow-Origin': '*' },
      body: JSON.stringify({ error: 'Failed to update leaderboard' })
    };
  }
};
```

### 3. In-App Purchases with AWS Lambda

```javascript
// IAP validation handler
const AWS = require('aws-sdk');

exports.validatePurchase = async (event) => {
  const { userId, receiptData, platform } = JSON.parse(event.body);
  
  try {
    let isValid = false;
    
    if (platform === 'ios') {
      isValid = await validateAppleReceipt(receiptData);
    } else if (platform === 'android') {
      isValid = await validateGooglePlayReceipt(receiptData);
    }
    
    if (isValid) {
      // Grant in-game currency or items
      await grantPurchaseRewards(userId, receiptData);
      
      return {
        statusCode: 200,
        headers: { 'Access-Control-Allow-Origin': '*' },
        body: JSON.stringify({ success: true, message: 'Purchase validated' })
      };
    } else {
      return {
        statusCode: 400,
        headers: { 'Access-Control-Allow-Origin': '*' },
        body: JSON.stringify({ success: false, message: 'Invalid receipt' })
      };
    }
  } catch (error) {
    return {
      statusCode: 500,
      headers: { 'Access-Control-Allow-Origin': '*' },
      body: JSON.stringify({ error: 'Purchase validation failed' })
    };
  }
};
```

## Deployment Commands

```bash
# Install Serverless Framework
npm install -g serverless

# Deploy the game backend
serverless deploy --stage prod

# Deploy frontend to S3 + CloudFront
aws s3 sync build/ s3://your-game-bucket --delete
aws cloudfront create-invalidation --distribution-id YOUR_DISTRIBUTION_ID --paths "/*"
```

## Cost Optimization Tips

1. **Use DynamoDB On-Demand** for unpredictable traffic
2. **Implement CloudFront caching** for game assets
3. **Use Lambda@Edge** for regional game logic
4. **Set up Auto Scaling** for EC2 instances if needed
5. **Monitor with CloudWatch** and set up billing alerts

## Analytics & Monitoring

```javascript
// Game analytics with Amazon Kinesis
const AWS = require('aws-sdk');
const kinesis = new AWS.Kinesis();

const trackGameEvent = async (eventData) => {
  await kinesis.putRecord({
    StreamName: process.env.ANALYTICS_STREAM,
    Data: JSON.stringify({
      ...eventData,
      timestamp: Date.now()
    }),
    PartitionKey: eventData.userId
  }).promise();
};

// Usage examples:
await trackGameEvent({
  userId: 'user123',
  eventType: 'LEVEL_COMPLETED',
  level: 5,
  score: 1250,
  timeSpent: 45000
});

await trackGameEvent({
  userId: 'user123',
  eventType: 'PURCHASE_MADE',
  itemId: 'extra_lives',
  amount: 0.99,
  currency: 'USD'
});
```

This architecture gives you a solid foundation for building engaging games on AWS. The serverless approach keeps costs low during development and scales automatically as your player base grows!