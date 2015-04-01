# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|

    config.vm.box = 'puppetlabs/centos-7.0-64-puppet'

    config.vm.provider 'virtualbox' do |vb|
      vb.customize ['modifyvm', :id, '--memory', '2048']
    end

    # Setup networking
    config.vm.provision :hosts do |hosts|
      hosts.autoconfigure = true
      hosts.add_host = '192.168.10.30', ['remotehost']
    end

    # Common script.
    config.vm.provision :shell, :privileged => true, :path => 'provisioners/shell/common.sh'

    config.vm.define 'remotehost' do |node|
      node.vm.hostname = 'remotehost'
      node.vm.network :private_network, :ip => '192.168.10.30'
      #node.vm.provision :shell, :privileged => true, :path =>  'provisioners/shell/remotehost.sh'
    end

end
