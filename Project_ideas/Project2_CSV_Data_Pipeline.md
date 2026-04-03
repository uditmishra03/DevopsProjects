# Project 2: CSV Data Pipeline

## Overview
Build an automated CSV data pipeline using S3, Lambda, Glue, and QuickSight for data processing and visualization.

## Architecture Components
- **Storage**: Three S3 buckets (raw, processed, transformed data)
- **Compute**: Lambda function for file processing
- **ETL**: AWS Glue for extract, transform, load operations
- **Visualization**: Amazon QuickSight for dashboard creation
- **Security**: IAM roles and policies

## Implementation Steps

### 1. S3 Bucket Setup
- Create three S3 buckets:
  - Raw CSV files bucket
  - Processed data bucket
  - Transformed files bucket

### 2. IAM Configuration
- Configure IAM roles and policies
- Grant services access to S3 buckets

### 3. Lambda Function
- Set up Lambda function triggered by new CSV uploads
- Implement file cleaning logic
- Move processed files to appropriate bucket

### 4. AWS Glue ETL
- Configure AWS Glue for detailed ETL operations
- Extract data from processed bucket
- Transform data according to business rules
- Load transformed data to final bucket

### 5. QuickSight Dashboard
- Connect Amazon QuickSight to final S3 bucket
- Create data visualizations
- Build interactive dashboard

## Project Specifications
- **Estimated Time**: 3-4 hours
- **Cost**: Less than $1 (with proper cleanup)
- **Target Roles**: Cloud Data Engineer, Data-focused Consultant

## Benefits
- Automated serverless data pipeline
- No manual data processing required
- Scalable analytics solution
- Real-time data visualization

## Skills Demonstrated
- Data pipeline architecture
- ETL processes
- Serverless computing
- Data visualization
- Event-driven processing