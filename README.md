# ansible-dnszone
For more information and examples see ```library/dnszone.py``` file.

# Development
You can use the Vagrantfile to set the test env.
```
git clone https://github.com/rmin/ansible-dnszone.git
cd ansible-dnszone
vagrant up
```

Next you can ```vagrant ssh``` into the VM and run the example playbook inside the Ubuntu box.
```
cd /vagrant/
ansible-playbook playbook.yml
```

You should be able to see the new record added to ```sample.zone``` file.

## License
MIT License

Copyright (c) 2018 @rmin
