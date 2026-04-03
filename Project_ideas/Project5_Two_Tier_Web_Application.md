# Project 5: Two-Tier Web Application Deployment

## Overview
Deploy a scalable two-tier web application using EC2, RDS, and Application Load Balancer with secure VPC networking.

## Architecture Components
- **Compute Layer**: EC2 instances for application hosting
- **Database Layer**: RDS MySQL database
- **Load Balancing**: Application Load Balancer (ALB)
- **Networking**: Custom VPC with public/private subnets
- **Security**: Security groups and proper network isolation

## Implementation Steps

### 1. VPC and Networking Setup
- Create custom VPC
- Configure public subnets for EC2 instances
- Configure private subnets for RDS database
- Set up proper routing and internet gateway

### 2. RDS Database Deployment
- Deploy RDS MySQL database in private subnets
- Run SQL commands to create necessary tables
- Configure database security groups

### 3. EC2 Instance Launch
- Launch two EC2 instances across different availability zones
- Deploy Node.js application on both instances
- Configure application to connect to RDS database

### 4. Application Load Balancer Setup
- Configure ALB to route traffic between EC2 instances
- Set up health checks for instances
- Update security groups for ALB-to-EC2 communication

### 5. Security Configuration
- Configure security groups for proper communication
- Ensure database is only accessible from application layer
- Test application accessibility and functionality

## Project Specifications
- **Estimated Time**: 2-3 hours
- **Cost**: Mostly free tier (minor ALB charges during runtime)
- **Target Roles**: Cloud deployment, infrastructure setup positions

## Architecture Benefits
- High availability across multiple AZs
- Scalable application tier
- Secure database isolation
- Production-ready design patterns

## Skills Demonstrated
- VPC design and networking
- Multi-tier application architecture
- Load balancing and high availability
- Database security and isolation
- Infrastructure as Code concepts
- Production deployment practices