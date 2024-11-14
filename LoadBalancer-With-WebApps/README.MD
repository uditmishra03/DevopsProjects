# Configure a Load Balancer to redirect request of application on two or more server hosting application.
# Need to create:
1. Load balancer
2. IP Blocking
3. Rate limiting.

We need: 3 Linux aws spin machines
1. Load balancer
2. Webapp1
3. Webapp2

To create:

1. Need a LB between webapp1 and webapp2, which will redirect the request to servers.
2. Block the ip's on the LB manually.
3. Block IP's which are sending more than 5 request per minute--> Rate limiting.


1. Spin up 3  AWS instances.
2. On Instance 1, call it as LB, install Nginx and set up LB.
3. On instance 2 and 3, set up webapp1 and webapp2.
4. Now link the load balancer with webapp1 and 2.
5. Request the load balancer by hitting its public IP, see the response of the webpage, observe how the LB is sending requests to both the servers simultaneously in Round robin fashion.
