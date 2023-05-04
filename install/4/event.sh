#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

event_version="3.0.6"
runPath=/root

public_file=/www/server/panel/install/public.sh
[ ! -f $public_file ] && wget -O $public_file https://raw.githubusercontent.com/chenxi-a11y/bt/main/install/public.sh -T 5;

. $public_file
download_Url=https://download.bt.cn

Install_event()
{
	if [ ! -f "/www/server/php/$version/bin/php-config" ];then
		echo "php-$vphp 未安装,请选择其它版本!"
		echo "php-$vphp not install, Plese select other version!"
		return
	fi
	
	isInstall=`cat /www/server/php/$version/etc/php.ini|grep 'event.so'`
	if [ "${isInstall}" != "" ];then
		echo "php-$vphp 已安装过event,请选择其它版本!"
		echo "php-$vphp not install, Plese select other version!"
		return
	fi
	
	case "${version}" in 
		'56')
			extFile='/www/server/php/56/lib/php/extensions/no-debug-non-zts-20131226/event.so'
		;;
		'70')
			extFile='/www/server/php/70/lib/php/extensions/no-debug-non-zts-20151012/event.so'
		;;
		'71')
			extFile='/www/server/php/71/lib/php/extensions/no-debug-non-zts-20160303/event.so'
		;;
		'72')
			extFile='/www/server/php/72/lib/php/extensions/no-debug-non-zts-20170718/event.so'
		;;
		'73')
			extFile='/www/server/php/73/lib/php/extensions/no-debug-non-zts-20180731/event.so'
		;;
		'74')
			extFile='/www/server/php/74/lib/php/extensions/no-debug-non-zts-20190902/event.so'
		;;
		'80')
			extFile='/www/server/php/80/lib/php/extensions/no-debug-non-zts-20200930/event.so'
		;;
		'81')
			extFile='/www/server/php/81/lib/php/extensions/no-debug-non-zts-20210902/event.so'
		;;
	esac
	
	if [ ! -f "${extFile}" ];then
		cd ${runPath}
		wget -O event-${event_version}.tgz ${download_Url}/src/event-${event_version}.tgz
		tar -xvf event-${event_version}.tgz
		cd event-${event_version}
		/www/server/php/$version/bin/phpize
		./configure --with-php-config=/www/server/php/$version/bin/php-config
	    make && make install
		cd ../
		rm -rf ${runPath}/event*
	fi
	
	if [ ! -f "${extFile}" ];then
		echo 'error';
		exit 0;
	else
		echo -e "extension = $extFile" >> /www/server/php/$version/etc/php.ini
		if [ -f /www/server/php/$version/etc/php-cli.ini ];then
			echo -e "extension = $extFile" >> /www/server/php/$version/etc/php-cli.ini
		fi
	fi
	service php-fpm-$version restart
	echo '==============================================='
	echo 'successful!'
}

Uninstall_event()
{
	if [ ! -f "/www/server/php/$version/bin/php-config" ];then
		echo "php-$vphp 未安装,请选择其它版本!"
		echo "php-$vphp not install, Plese select other version!"
		return
	fi
	
	isInstall=`cat /www/server/php/$version/etc/php.ini|grep 'event.so'`
	if [ "${isInstall}" = "" ];then
		echo "php-$vphp 未安装event,请选择其它版本!"
		echo "php-$vphp not install event, Plese select other version!"
		return
	fi

	sed -i '/event.so/d' /www/server/php/$version/etc/php.ini
	if [ -f /www/server/php/$version/etc/php-cli.ini ];then
		sed -i '/event.so/d' /www/server/php/$version/etc/php-cli.ini
	fi

	service php-fpm-$version restart
	echo '==============================================='
	echo 'successful!'
}

actionType=$1
version=$2
vphp=${version:0:1}.${version:1:1}
if [ "$actionType" == 'install' ];then
	Install_event
elif [ "$actionType" == 'uninstall' ];then
	Uninstall_event
fi
