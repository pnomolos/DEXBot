*****
Setup
*****

Requirements -- Linux
---------------------

To run in the background you need systemd and *lingering* enabled::

   sudo loginctl enable-linger $USER

On some systems, such as the Raspberry Pi, you need to reboot for this to take effect.

You need to have python3 installed, including the ``pip`` tool, and the development tools for C extensions, and
the OpenSSL libraries.

Plus for the easy configuration you need the ``whiptail`` command.

On Ubuntu/Debian/Raspian::

   sudo apt-get install gcc libssl-dev python3-pip python3-dev whiptail

On some Ubuntu systems, it will complain about missing packages: you need to enable
the ``universe`` repository::

   sudo add-apt-repository universe
   sudo apt-get update

NOTE: you *don't* need to upgrade the system: the issue here is about the *range* of packages
available, not how new/old they are.

On some Ubuntu systems, ``add-apt-repository`` isn't available::

   sudo apt-get install software-properties-common python-software-properties

On CentOS/RedHat::

   sudo yum install -y epel-release
   sudo yum install gcc openssl-devel python34-pip python34-devel newt

On other distros you need to check the documentation for how to install these packages, the names should be very similar.
  
Installation
------------

::

   pip3 install https://github.com/ihaywood3/DEXBot/releases/download/0.0.7-ih/dexbot-0.0.8_ih-py3-none-any.whl

If you add the ``--user`` flag to this command, the binaries of
``dexbot`` and ``uptick`` are located in ``~/.local/bin``.
Otherwise they should be globally reachable.

If you want the latest development version (which may not be tested at all), use git to download::

   git clone git://github.com/ihaywood3/DEXBot/
   cd DEXBot
   pip3 install -e .


Adding Keys
-----------

It is important to *install* the private key of your
bot's account into a local wallet. This can be done using
``uptick`` which is installed as a dependency of ``dexbot``::

   uptick addkey

``uptick`` will ask you for a passphrase to protect private keys stored in its wallet.
This has no relation to any passphrase used in the web wallet.

You can get your private key from the BitShares Web Wallet: click the menu on the top right,
then "Settings", "Accounts", "View keys", then tab "Owner Permissions", click 
on the public key, then "Show". 

Look for the private key in Wallet Import Format (WIF), it's a "5" followed
by a long list of letters. Select, copy and paste this into the screen
where uptick asks for the key.

Check ``uptick`` successfully imported the key with::

   uptick listaccounts

Yes, this process is a pain but for security reasons this part probably won't ever be "easy".

Configuration
-------------

``dexbot`` can be configured using::

  dexbot configure

This will walk you through the configuration process.
Read more about this in the :doc:`configuration`.

