# Project 1: Event Announcement System

## Overview
Create an event announcement system using SNS, Lambda, and API Gateway for real-time alerts and notifications.

## Architecture Components
- **Frontend**: HTML, CSS, and events.json file
- **Hosting**: S3 bucket with static website hosting
- **Messaging**: Amazon SNS for email subscriptions and notifications
- **Compute**: Two Lambda functions (subscription handler and event creation)
- **API**: API Gateway with subscribe and create event endpoints

## Implementation Steps

### 1. Frontend Development
- Create frontend using HTML, CSS
- Set up events.json file to store event data

### 2. Static Website Hosting
- Host frontend on S3 bucket using static website hosting

### 3. SNS Configuration
- Set up Amazon SNS to manage email subscriptions
- Configure notifications system

### 4. Lambda Functions
- **Subscription Lambda**: Handle user subscriptions
- **Event Creation Lambda**: Handle event creation and notifications

### 5. API Gateway Setup
- Expose Lambda functions via API Gateway
- Create subscribe endpoint
- Create event creation endpoint
- Connect endpoints to frontend

## Project Specifications
- **Estimated Time**: 2-3 hours
- **Cost**: Free tier eligible (remember to delete resources after)
- **Target Roles**: Cloud Engineer, Solutions Architect

## Use Cases
1. **Event Promotion**: Collect emails and send announcements for company events
2. **Early Access Alerts**: Notify employees about new product releases for testing
3. **Birthday Notifications**: Connect with team calendar for automated birthday alerts

## Skills Demonstrated
- Serverless architecture design
- Event-driven programming
- API development
- Real-time notification systems
- End-to-end application development