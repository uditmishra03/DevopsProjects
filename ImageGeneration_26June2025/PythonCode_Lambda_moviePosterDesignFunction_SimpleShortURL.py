import json
#1. import boto3
import boto3
import base64
import datetime
import hashlib

#2. Create client connection with Bedrock and S3 Services – Link
client_bedrock = boto3.client('bedrock-runtime')
client_s3 = boto3.client('s3')

def create_simple_short_url(original_url, poster_name):
    """Create a simple shortened identifier using hash"""
    # Create a hash of the poster name for a shorter identifier
    hash_object = hashlib.md5(poster_name.encode())
    short_hash = hash_object.hexdigest()[:8]  # Take first 8 characters
    
    # You can create a simple mapping or use the S3 key directly
    return {
        'short_id': short_hash,
        'direct_s3_url': f"https://image-generation-29072025.s3.amazonaws.com/{poster_name}",
        'original_presigned_url': original_url
    }

def lambda_handler(event, context):
    
#3. Store the input data (prompt) in a variable
    input_prompt=event['prompt']
    print(input_prompt)

#4. Create a Request Syntax to access the Bedrock Service (Amazon Titan Image Generator)
    request_body = {
        "taskType": "TEXT_IMAGE",
        "textToImageParams": {
            "text": input_prompt,
            "negativeText": "",
            "seed": 0
        },
        "imageGenerationConfig": {
            "numberOfImages": 1,
            "quality": "standard",
            "cfgScale": 8.0,
            "height": 1024,
            "width": 1024
        }
    }
    
    response_bedrock = client_bedrock.invoke_model(
        contentType='application/json', 
        accept='application/json',
        modelId='amazon.titan-image-generator-v2:0',
        body=json.dumps(request_body)
    )
    #print(response_bedrock)   
       
#5. 5a. Retrieve from Dictionary, 5b. Convert Streaming Body to Byte using json load 5c. Print

    response_bedrock_byte=json.loads(response_bedrock['body'].read())
    print(response_bedrock_byte)
#6. 6a. Retrieve data with images key, 6b. Import Base 64, 6c. Decode from Base64
    response_bedrock_base64 = response_bedrock_byte['images'][0]
    response_bedrock_finalimage = base64.b64decode(response_bedrock_base64)
    print(response_bedrock_finalimage)
    
#7. 7a. Upload the File to S3 using Put Object Method – Link 7b. Import datetime 7c. Generate the image name to be stored in S3 - Link
    poster_name = 'image-name-'+ datetime.datetime.today().strftime('%Y-%m-%d-%H-%M-%S')+'.png'

    # Make the S3 object publicly readable (optional)
    response_s3=client_s3.put_object(
        Bucket='image-generation-29072025',
        Body=response_bedrock_finalimage,
        Key=poster_name,
        ContentType='image/png'
    )

#8. Generate Pre-Signed URL and Create Short URL
    generate_presigned_url = client_s3.generate_presigned_url('get_object', Params={'Bucket':'image-generation-29072025','Key':poster_name}, ExpiresIn=3600)
    
    # Create short URL alternatives
    url_options = create_simple_short_url(generate_presigned_url, poster_name)
    
    print("Original URL:", generate_presigned_url)
    print("Short ID:", url_options['short_id'])
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'presigned_url': generate_presigned_url,
            'short_id': url_options['short_id'],
            'direct_s3_url': url_options['direct_s3_url'],
            'image_key': poster_name,
            'message': 'Image generated successfully'
        })
    }
