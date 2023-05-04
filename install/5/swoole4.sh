#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

Swoole_Version='4.5.9'
runPath=/root

extPath()
{
  case "${version}" in 
  '70')
  extFile='/www/server/php/70/lib/php/extensions/no-debug-non-zts-20151012/swoole.so'
  ;;
  '71')
  extFile='/www/server/php/71/lib/php/extensions/no-debug-non-zts-20160303/swoole.so'
  ;;
  '72')
  extFile='/www/server/php/72/lib/php/extensions/no-debug-non-zts-20170718/swoole.so'
  ;;
  '73')
  extFile='/www/server/php/73/lib/php/extensions/no-debug-non-zts-20180731/swoole.so'
  ;;
  '74')
  extFile='/www/server/php/74/lib/php/extensions/no-debug-non-zts-20190902/swoole.so'
  ;;
  '80')
  extFile='/www/server/php/80/lib/php/extensions/no-debug-non-zts-20200930/swoole.so'
  ;;
esac
}


Install_Swoole()
{
  #public_file=/www/server/panel/install/public.sh
  if [ ! -f $public_file ];then
    wget -O $public_file 域名/install/public.sh -T 5;
  fi
  . $public_file

  download_Url=https://download.bt.cn
  extPath
  if [ ! -f "${extFile}" ];then
  	wget $download_Url/src/swoole-$Swoole_Version.tgz
  	tar -zxvf swoole-$Swoole_Version.tgz
  	cd swoole-$Swoole_Version
  	/www/server/php/$version/bin/phpize
		./configure --with-php-config=/www/server/php/$version/bin/php-config --enable-openssl --with-openssl-dir=/usr/local/openssl --enable-sockets
		make && make install
		cd ../
		rm -rf swoole*
 	fi

 	if [ ! -f "${extFile}" ];then
 		echo 'error';
 		exit 0;
 	fi
 	
 	echo -e "\n[swoole]\nextension = swoole.so\n" >> /www/server/php/$version/etc/php.ini

 	service php-fpm-$version reload
}



Uninstall_Swoole()
{
  extPath
	sed -i '/swoole/d' /www/server/php/$version/etc/php.ini
  rm -f ${extFile}
	service php-fpm-$version reload
	echo '==============================================='
	echo 'successful!'
}

actionType=$1
version=$2
vphp=${version:0:1}.${version:1:1}
if [ "$actionType" == 'install' ];then
	Install_Swoole
elif [ "$actionType" == 'uninstall' ];then
	Uninstall_Swoole
fi
