# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|
  if (/cygwin|mswin|mingw|bccwin|wince|emx/ =~ RUBY_PLATFORM) != nil
    config.vm.synced_folder ".", "/vagrant", mount_options: ["dmode=700,fmode=600"]
  else
    config.vm.synced_folder ".", "/vagrant"
  end
  config.vm.define "ansible" do |d|
    d.vm.box = "ubuntu/xenial64"
    d.vm.hostname = "ansible"
    d.vm.provision :shell, inline: "sudo apt-get update -y"
    d.vm.provision :shell, inline: "sudo apt-get install -y python python-pip ansible"
    d.vm.provision :shell, inline: "sudo pip install dnspython"
    d.vm.provider "virtualbox" do |v|
      v.memory = 1024
    end
  end
  if Vagrant.has_plugin?("vagrant-cachier")
    config.cache.scope = :box
  end
  if Vagrant.has_plugin?("vagrant-vbguest")
    config.vbguest.auto_update = false
    config.vbguest.no_install = true
    config.vbguest.no_remote = true
  end
end