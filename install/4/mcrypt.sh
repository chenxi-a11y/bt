#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

mcrypt_version="1.0.4"
runPath=/root

public_file=/www/server/panel/install/public.sh
[ ! -f $public_file ] && wget -O $public_file https://raw.githubusercontent.com/chenxi-a11y/bt/main/install/public.sh -T 5;

. $public_file
download_Url=https://download.bt.cn

if [ -z "${cpuCore}" ]; then
	cpuCore="1"
fi

ext_Path(){
	case "${version}" in 
		'72')
		extFile='/www/server/php/72/lib/php/extensions/no-debug-non-zts-20170718/mcrypt.so'
		;;
		'73')
		extFile='/www/server/php/73/lib/php/extensions/no-debug-non-zts-20180731/mcrypt.so'
		;;
		'74')
		extFile='/www/server/php/74/lib/php/extensions/no-debug-non-zts-20190902/mcrypt.so'
		;;
		'80')
		extFile='/www/server/php/80/lib/php/extensions/no-debug-non-zts-20200930/mcrypt.so'
		;;
	esac
}
Install_Mcrypt(){
	isInstall=`cat /www/server/php/$version/etc/php.ini|grep 'mcrypt.so'`
	if [ "${isInstall}" ];then
		echo "php-$vphp 已安装过mcrypt,请选择其它版本!"
		return
	fi
	if [ ! -f "${extFile}" ];then 
		cd ${runPath}
		wget -O mcrypt-${mcrypt_version}.tgz ${download_Url}/src/mcrypt-${mcrypt_version}.tgz
		tar -xvf mcrypt-${mcrypt_version}.tgz
		cd mcrypt-${mcrypt_version}
		/www/server/php/$version/bin/phpize
		./configure --with-php-config=/www/server/php/$version/bin/php-config
		make && make install
		cd ../
		rm -rf mcrypt-${mcrypt_version}*
	fi

	if [ ! -f "${extFile}" ];then
		GetSysInfo
		echo 'error';
		exit 1;
	fi

	echo -e "extension = mcrypt.so\n" >> /www/server/php/$version/etc/php.ini
	/etc/init.d/php-fpm-$version reload
	echo '==============================================='
	echo 'successful!'
}
Uninstall_Mcrypt(){
	sed -i '/mcrypt.so/d' /www/server/php/$version/etc/php.ini
	/etc/init.d/php-fpm-$version reload
}

actionType=$1
version=$2
vphp=${version:0:1}.${version:1:1}
ext_Path
if [ "$actionType" == 'install' ];then
	Install_Mcrypt
elif [ "$actionType" == 'uninstall' ];then
	Uninstall_Mcrypt
fi

