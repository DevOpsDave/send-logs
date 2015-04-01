#!/usr/bin/bash

yum install -y java

# just to get things working
rsync -a /vagrant/dropwizard-helloworld /opt/
cd /opt/dropwizard-helloworld


nohup java -Ddw.defaultName=$(hostname) -jar target/dropwizard-example-0.0.1-SNAPSHOT.jar server hello-world.yml &
