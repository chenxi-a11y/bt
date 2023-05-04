#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

Install_bz2()
{
	if [ ! -f "/www/server/php/$version/bin/php-config" ];then
		echo "php-$vphp 未安装,请选择其它版本!"
		echo "php-$vphp not install, Plese select other version!"
		return
	fi
	
	isInstall=`cat /www/server/php/$version/etc/php.ini|grep 'bz2.so'`
	if [ "${isInstall}" != "" ];then
		echo "php-$vphp 已安装过bz2,请选择其它版本!"
		echo "php-$vphp is installed bz2, Plese select other version!"
		return
	fi
	
	if [ ! -d "/www/server/php/$version/src/ext/bz2" ];then
		#public_file=/www/server/panel/install/public.sh
		if [ ! -f $public_file ];then
			wget -O $public_file 域名/install/public.sh -T 5;
		fi
		. $public_file

		download_Url=https://download.bt.cn
		mkdir -p /www/server/php/$version/src
		wget -O $version-ext.tar.gz $download_Url/install/ext/$version-ext.tar.gz
		tar -zxf $version-ext.tar.gz -C /www/server/php/$version/src/ 
		rm -f $version-ext.tar.gz
	fi
	
	case "${version}" in 
		'52')
		extFile="/www/server/php/52/lib/php/extensions/no-debug-non-zts-20060613/bz2.so"
		;;
		'53')
		extFile="/www/server/php/53/lib/php/extensions/no-debug-non-zts-20090626/bz2.so"
		;;
		'54')
		extFile="/www/server/php/54/lib/php/extensions/no-debug-non-zts-20100525/bz2.so"
		;;
		'55')
		extFile="/www/server/php/55/lib/php/extensions/no-debug-non-zts-20121212/bz2.so"
		;;
		'56')
		extFile="/www/server/php/56/lib/php/extensions/no-debug-non-zts-20131226/bz2.so"
		;;
		'70')
		extFile="/www/server/php/70/lib/php/extensions/no-debug-non-zts-20151012/bz2.so"
		;;
		'71')
		extFile="/www/server/php/71/lib/php/extensions/no-debug-non-zts-20160303/bz2.so"
		;;
		'72')
		extFile="/www/server/php/72/lib/php/extensions/no-debug-non-zts-20170718/bz2.so"
		;;
		'73')
		extFile='/www/server/php/73/lib/php/extensions/no-debug-non-zts-20180731/bz2.so'
		;;
		'74')
		extFile='/www/server/php/74/lib/php/extensions/no-debug-non-zts-20190902/bz2.so'
		;;
		'80')
		extFile='/www/server/php/80/lib/php/extensions/no-debug-non-zts-20200930/bz2.so'
		;;
		'81')
		extFile='/www/server/php/81/lib/php/extensions/no-debug-non-zts-20210902/bz2.so'
		;;
		'82')
        extFile='/www/server/php/82/lib/php/extensions/no-debug-non-zts-20220829/bz2.so'
        ;;
		
	esac
	
	if [ ! -f "${extFile}" ];then
		cd /www/server/php/$version/src/ext/bz2
		/www/server/php/$version/bin/phpize
		./configure --with-php-config=/www/server/php/$version/bin/php-config
		make && make install
	fi
	
	if [ ! -f "${extFile}" ];then
		echo 'error';
		exit 0;
	fi

	echo -e "extension = " ${extFile} >> /www/server/php/$version/etc/php.ini
	if [[ -f /www/server/php/$version/etc/php-cli.ini ]];then
		echo -e "extension = " ${extFile} >> /www/server/php/$version/etc/php-cli.ini
	fi
	service php-fpm-$version reload
	echo '==============================================='
	echo 'successful!'
}

Uninstall_bz2()
{
	if [ ! -f "/www/server/php/$version/bin/php-config" ];then
		echo "php-$vphp 未安装,请选择其它版本!"
		echo "php-$vphp not install, Plese select other version!"
		return
	fi
	
	isInstall=`cat /www/server/php/$version/etc/php.ini|grep 'bz2.so'`
	if [ "${isInstall}" = "" ];then
		echo "php-$vphp 未安装bz2,请选择其它版本!"
		echo "php-$vphp not install bz2, Plese select other version!"
		return
	fi

	sed -i '/bz2.so/d' /www/server/php/$version/etc/php.ini
	if [ -f /www/server/php/$version/etc/php-cli.ini ];then
		sed -i '/bz2.so/d' /www/server/php/$version/etc/php-cli.ini
	fi
	service php-fpm-$version reload
	echo '==============================================='
	echo 'successful!'
}

actionType=$1
version=$2
vphp=${version:0:1}.${version:1:1}
if [ "$actionType" == 'install' ];then
	Install_bz2
elif [ "$actionType" == 'uninstall' ];then
	Uninstall_bz2
fi
