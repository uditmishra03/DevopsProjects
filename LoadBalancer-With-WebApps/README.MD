# Configure a Load Balancer to redirect request of application on two or more server hosting application.
Tasks:
1. Create a Load balancer along with two servers hosting web application.
2. IP Blocking manually on the Load balancer. 
3. Rate limiting (Automated) for the more than 5 requests per minute.

## **We need to Spin up 3 Linux aws EC2 instances **
1. Load balancer
2. Webapp1
3. Webapp2

## **To create:**

1. Need a LB between webapp1 and webapp2, which will redirect the request to servers.
2. Block the ip's on the LB manually.
3. Block IP's which are sending more than 5 request per minute--> Rate limiting.

## **TO DO:**
1. Spin up 3  AWS instances.
2. On Instance 1, call it as LB, install Nginx and set up LB.
3. On instance 2 and 3, set up webapp1 and webapp2.
4. Now link the load balancer with webapp1 and 2.
5. Request the load balancer by hitting its public IP, see the response of the webpage, observe how the LB is sending requests to both the servers simultaneously in Round robin fashion.

## **Creating Load Balancer:**

1. update repository:<br/>
**`sudo apt update`**
2. Install nginx: <br/>
**`sudo apt install nginx -y`**
3. Get public ip of machine: <br/>
**`curl ifconfig.me`**
4. Check the status of installation of nginx:<br/>
**`sudo systemctl status nginx.service`**<br/>
**`ll /etc/nginx/nginx.conf`**<br/>
**`cat /etc/nginx/nginx.conf`**<br/>

5. Create custom Load balancer config file:
`vi /etc/nginx/conf.d/loadBalancer.conf`<br/>
Add content: 
<br/>
```upstream backend_servers {
    server <webapp1 ip addr>;
    server <webapp2 ip addr>;
}

server {
listen 80;
server_name <public ip>;

   location / {
       proxy_redirect off;
       proxy_pass http://backend_servers;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header Host $host;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
   }
}`

6. reload the config files for nginx:
`sudo systemctl reload nginx.service`

7. check the nginx service status:
  `sudo systemctl status nginx.service`
