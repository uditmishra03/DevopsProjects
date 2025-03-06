# Configure a Load Balancer to redirect request of application on two or more server hosting application.
Tasks:
1. Create a Load balancer along with two servers hosting web application.
2. IP Blocking manually on the Load balancer. 
3. Rate limiting (Automated) for the more than 5 requests per minute.

## **We need to Spin up 3 Linux AWS EC2 instances as:**
1. Load balancer
2. Webapp1
3. Webapp2

## **To create:**

1. Need a LB between webapp1 and webapp2, which will redirect the request to servers.
2. Block the ip's on the LB manually.
3. Block IP's which are sending more than 5 request per minute--> Rate limiting.

## **TO DO:**
1. Spin up 3 AWS EC2 instances.
2. On Instance 1, call it as LB, install Nginx and set up LB.
3. On instance 2 and 3, set up webapp1 and webapp2.
4. Now link the load balancer with webapp1 and 2.
5. Send requests to the load balancer by hitting its public IP, see the response of the webpage, observe how the LB is sending requests to both the servers simultaneously in Round robin fashion.

## **Task1: Setup Load balancer with Web application.**
### **Creating Load Balancer:**

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

5. Create custom Load balancer config file: <br/>
**`vi /etc/nginx/conf.d/loadBalancer.conf`**

Add content: <br/>
```
upstream backend_servers {
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
}
```

6. reload the config files for nginx:<br/>
**`sudo systemctl reload nginx.service`**

7. check the nginx service status:<br/>
  **`sudo systemctl status nginx.service`**


### **Configuring WebApp1:** <br/>
1. update repository:<br/>
**`sudo apt update`**
2. Install apache server: <br/>
```
sudo apt install apache2 -y
sudo systemctl status apache2
sudo systemctl start apache2
sudo systemctl enable apache2
```
3. Create an html page and verify it:<br/>
```
echo "<h1>Hello from WEBAPP1 $(curl ifconfig.me)</h1>" | sudo tee /var/www/html/index.html
ll /var/www/html/index.html
cat  /var/www/html/index.html
```

### **Configuring WebApp2:** <br/>
1. update repository:<br/>
**`sudo apt update`**
2. Install apache server: <br/>
```
sudo apt install apache2 -y
sudo systemctl status apache2
sudo systemctl start apache2
sudo systemctl enable apache2
```
3. Create an html page and verify it:<br/>
```
echo "<h1>Hello from WEBAPP2 $(curl ifconfig.me)</h1>" | sudo tee /var/www/html/index.html
ll /var/www/html/index.html
cat  /var/www/html/index.html
```

**Hit the LB public IP or curl the LB public IP to access the webapp.**

## **Task 2: To block the IP manually on load balancer, Iptables need to be updated.** <br/>
1. File: `/var/log/nginx/access.log` contains the details of the requests made to LB.
To get the list of IP addresses access the Webapp: <br/>
```
cat /var/log/nginx/access.log | awk '{print $1}' | sort | uniq
```
2. Using the above IP, update the iptables rules for INPUT stream as: <br/>
```
cat /var/log/nginx/access.log | awk '{print $1}' | sort | uniq | xargs -I {} sudo iptables -A INPUT -s {} -p tcp --dport 80 -j DROP
```

3. To verify iptables:
```
sudo iptables -L
```
4. To flush(remove) all the rules of iptables:
```
sudo iptables -F
```

## **Task 3: To block the Ip address in automated way by applying Rate limiting rule for more than 5 requests made by same IP address with in a minute.** <br/>

1. Update the http section of /etc/nginx/nginx.conf, by adding below configuration:<br/>
   **`limit_req_zone $binary_remote_addr zone=mylimit:10m rate=5r/m;`**

2. Update the /etc/nginx/conf.d/loadBalancer.conf by adding below configuration: <br/>
   **`limit_req zone=mylimit burst=5 nodelay;`**

3. Save the files and reload the nginx service:<br/>
```
sudo systemctl reload nginx.service
sudo systemctl status nginx.service
```

### Note: To check the syntax of nginx service after adding the config file, Run: <br/>
```
nginx -t -c /etc/nginx/nginx.conf
```
