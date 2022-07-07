export PATH=/usr/local/sbin:/usr/sbin:/sbin:/usr/local/bin:/usr/bin:/bin:/usr/local/games:/usr/games
yum install gcc openssl-devel bzip2-devel libffi-devel zlib-devel xz-devel wget curl make -y
cd /usr/src
wget https://www.python.org/ftp/python/3.7.11/Python-3.7.11.tgz || curl https://www.python.org/ftp/python/3.7.11/Python-3.7.11.tgz --output Python-3.7.11.tgz
tar xzf Python-3.7.11.tgz
cd Python-3.7.11
./configure --enable-optimizations
make altinstall
rm /usr/src/Python-3.7.11.tgz
rm -rf /usr/bin/python3
ln -s /usr/src/Python-3.7.11/python /usr/bin/python3
python3 --version
