# How to run server for BULLET
## a. Connect domain address and IP address

We deploy server on Amazon AWS and connect domain with Route 53 in the AWS service (ubuntu)

For amazone linux or centos, refer https://awswithatiq.com/letsencrypt-with-amazon-linux-2-centos-7/

Reference: https://aws.amazon.com/en/route53/

## b. Install letsencrypt 

sudo apt update 

sudo apt-get install  letsencrypt -y 

## c. Get certificate

cd /root/

service nginx stop

certbot certonly --standalone -d your_domain

service nginx restart

## d. Copy certificate information on the working folder

cd etc/letsencrypt/live/your_domain

cp fullchain.pem  /your_folder/your_domain/

cp privkey.pem /your_folder/your_domain/

Then, enable pem file to be accessed with chmod 777 command

Finally, change pem file reference path of the run.sh file on the working folder. For example, 

python3 server.py --port 4433 -v --certificate ./*your_domain*/fullchain.pem --private-key ./*your_domain*/privkey.pem

## e. Run QUIC server

./run.sh 




