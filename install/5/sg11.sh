#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
LANG=en_US.UTF-8
runPath="/root"
Is_64bit=`getconf LONG_BIT`

extFile(){
	case "${version}" in 
		'52')
		extFile='/www/server/php/52/lib/php/extensions/no-debug-non-zts-20060613/ixed.lin'
		;;
		'53')
		extFile='/www/server/php/53/lib/php/extensions/no-debug-non-zts-20090626/ixed.lin'
		;;
		'54')
		extFile='/www/server/php/54/lib/php/extensions/no-debug-non-zts-20100525/ixed.lin'
		;;
		'55')
		extFile='/www/server/php/55/lib/php/extensions/no-debug-non-zts-20121212/ixed.lin'
		;;
		'56')
		extFile='/www/server/php/56/lib/php/extensions/no-debug-non-zts-20131226/ixed.lin'
		;;
		'70')
		extFile='/www/server/php/70/lib/php/extensions/no-debug-non-zts-20151012/ixed.lin'
		;;
		'71')
		extFile='/www/server/php/71/lib/php/extensions/no-debug-non-zts-20160303/ixed.lin'
		;;
		'72')
		extFile='/www/server/php/72/lib/php/extensions/no-debug-non-zts-20170718/ixed.lin'
		;;
		'73')
		extFile='/www/server/php/73/lib/php/extensions/no-debug-non-zts-20180731/ixed.lin'
		;;
		'74')
		extFile='/www/server/php/74/lib/php/extensions/no-debug-non-zts-20190902/ixed.lin'
		;;
	esac;
}
Install_sg11()
{
	extFile
	
	isInstall=`cat /www/server/php/$version/etc/php.ini|grep ${extFile}`
	if [ "${isInstall}" != "" ];then
		echo "php-$vphp 已安装sg11,请选择其它版本!"
		return
	fi

	if [ ! -f "$extFile" ];then
		public_file=/www/server/panel/install/public.sh
		if [ ! -f $public_file ];then
			wget -O $public_file https://raw.githubusercontent.com/chenxi-a11y/bt/main/install/public.sh -T 5;
		fi
		. $public_file

		download_Url=$NODE_URL

		sed -i '/ixed/d'  /www/server/php/$version/etc/php.ini
		
		cd $runPath
		wget -O sg11.zip $download_Url/src/sg11.zip
		unzip -o sg11.zip

		case "${version}" in 
			'52')
			mkdir -p /www/server/php/52/lib/php/extensions/no-debug-non-zts-20060613/
			\cp /root/sg11/$Is_64bit/ixed.5.2.lin /www/server/php/52/lib/php/extensions/no-debug-non-zts-20060613/ixed.lin
			;;
			'53')
			mkdir -p /www/server/php/53/lib/php/extensions/no-debug-non-zts-20090626/
			\cp /root/sg11/$Is_64bit/ixed.5.3.lin /www/server/php/53/lib/php/extensions/no-debug-non-zts-20090626/ixed.lin
			;;
			'54')
			mkdir -p /www/server/php/54/lib/php/extensions/no-debug-non-zts-20100525/
			\cp /root/sg11/$Is_64bit/ixed.5.4.lin /www/server/php/54/lib/php/extensions/no-debug-non-zts-20100525/ixed.lin
			;;
			'55')
			mkdir -p /www/server/php/55/lib/php/extensions/no-debug-non-zts-20121212/
			\cp /root/sg11/$Is_64bit/ixed.5.5.lin /www/server/php/55/lib/php/extensions/no-debug-non-zts-20121212/ixed.lin
			;;
			'56')
			mkdir -p /www/server/php/56/lib/php/extensions/no-debug-non-zts-20131226/
			\cp /root/sg11/$Is_64bit/ixed.5.6.lin /www/server/php/56/lib/php/extensions/no-debug-non-zts-20131226/ixed.lin
			;;
			'70')
			mkdir -p /www/server/php/70/lib/php/extensions/no-debug-non-zts-20151012/
			\cp /root/sg11/$Is_64bit/ixed.7.0.lin /www/server/php/70/lib/php/extensions/no-debug-non-zts-20151012/ixed.lin
			;;
			'71')
			mkdir -p /www/server/php/71/lib/php/extensions/no-debug-non-zts-20160303/
			\cp /root/sg11/$Is_64bit/ixed.7.1.lin /www/server/php/71/lib/php/extensions/no-debug-non-zts-20160303/ixed.lin
			;;
			'72')
			mkdir -p /www/server/php/72/lib/php/extensions/no-debug-non-zts-20170718/
			\cp /root/sg11/$Is_64bit/ixed.7.2.lin /www/server/php/72/lib/php/extensions/no-debug-non-zts-20170718/ixed.lin
			;;
			'73')
			mkdir -p /www/server/php/73/lib/php/extensions/no-debug-non-zts-20180731/
			\cp /root/sg11/$Is_64bit/ixed.7.3.lin /www/server/php/73/lib/php/extensions/no-debug-non-zts-20180731/ixed.lin
			;;
			'74')
			mkdir -p /www/server/php/74/lib/php/extensions/no-debug-non-zts-20190902/
			\cp /root/sg11/$Is_64bit/ixed.7.3.lin /www/server/php/74/lib/php/extensions/no-debug-non-zts-20190902/ixed.lin
			;;
		esac;

	fi

	rm -rf sg11*

	if [ ! -f "$extFile" ];then
		echo "ERROR!"
		return;
	fi

	echo "extension=$extFile" >> /www/server/php/$version/etc/php.ini
	service php-fpm-$version reload
	echo '==========================================================='
	echo 'successful!'

}
Uninstall_sg11()
{
	if [ ! -f "/www/server/php/$version/bin/php-config" ];then
		echo "php-$vphp 未安装,请选择其它版本!"
		return;
	fi

	extFile

	if [ ! -f "$extFile" ];then
		echo "php-$vphp 未安装sg11,请选择其它版本!"
		return
	fi

	sed -i '/ixed/d'  /www/server/php/$version/etc/php.ini
		
	rm -f $extFile
	/etc/init.d/php-fpm-$version reload
	echo '==============================================='
	echo 'successful!'
}
actionType=$1
version=$2
vphp=${version:0:1}.${version:1:1}
if [ "$actionType" == 'install' ];then
	Install_sg11
elif [ "$actionType" == 'uninstall' ];then
	Uninstall_sg11
fi
