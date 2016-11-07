docker run  -d  --name="sumpad1" -v /opt/data/sumpad1:/usr/local/sumpad -p 5001:5000 -p 14506:4506 -p 14505:14505 --env pub_port=14505 sumpad
docker run  -d  --name="sumpad2" -v /opt/data/sumpad2:/usr/local/sumpad -p 5002:5000 -p 24506:4506 -p 24505:24505 --env pub_port=24505 sumpad
docker run  -d  --name="minion1" minion
docker run  -d  --name="minion2" minion
docker run  -d  --name="minion3" minion




