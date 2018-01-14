# Quickstart

- Make cure you have an AWS *profile* setup and set it's name in the example_project/shunts/variables file

- change into this project's directory :)

- make a new ssh key for the project-manager

	```bash
	ssh-keygen -t rsa -b 4096 -f javier.project-manager.devops
	```

- Apply the Shuntfile

	```bash
	cd ..
	pipenv run python shunt.py example_project/Shuntfile
	```

- Ok, now in the example_project/materialized_views we will have the following:
  - cluster.tf Terraform file
  - packer-*.json Packer files

- Create the images for the bastion, salt-master and salt-minion hosts

	```bash
	cd example_project/materialized_views
	packer build packer-bastion.json
	packer build packer-salt-master.json
	packer build packer-salt-minion.json
	```
	
- Bring up the cluster

	```bash
	terraform init
	terraform plan
	terraform apply
	```

- SSH into the salt-master through the bastion host

	```bash
	terraform output eip
	ssh -i javier.project-manager.devops -o ProxyCommand="ssh -i javier.project-manager.devops -W %h:%p ubuntu@<EIP>" ubuntu@10.0.0.10
	```

- Test minion connectivity

	```bash
	sudo salt '*' test.ping
	```

- Provision all the minions (including master, which is also a minion)

	```bash
	sudo salt '*' state.apply
	```

- have fun :)
