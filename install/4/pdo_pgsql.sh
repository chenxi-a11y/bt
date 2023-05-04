#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

Install_Pdo_Pgsql()
{	
	
	if [ ! -f "/www/server/php/$version/bin/php-config" ];then
		echo "php-$vphp 未安装,请选择其它版本!"
		echo "php-$vphp not install, Plese select other version!"
		return
	fi
	
	isInstall=`cat /www/server/php/$version/etc/php.ini|grep 'pdo_pgsql.so'`
	if [ "${isInstall}" != "" ];then
		echo "php-$vphp 已安装过pdo_pgsql,请选择其它版本!"
		echo "php-$vphp not install, Plese select other version!"
		return
	fi

	if [ ! -d "/www/server/php/$version/src/ext/pdo_pgsql" ];then
		public_file=/www/server/panel/install/public.sh
		if [ ! -f $public_file ];then
			wget -O $public_file 域名/install/public.sh -T 5;
		fi
		. $public_file

		download_Url=https://download.bt.cn
		mkdir -p /www/server/php/$version/src
		cd /www/server/php/$version/src
		wget -O $version-ext.tar.gz ${download_Url}/install/ext/$version-ext.tar.gz
		tar -xvf $version-ext.tar.gz
		rm -f $version-ext.tar.gz
	fi
	case "${version}" in 
		'52')
		extFile='/www/server/php/52/lib/php/extensions/no-debug-non-zts-20060613/pdo_pgsql.so'
		;;
		'53')
		extFile='/www/server/php/53/lib/php/extensions/no-debug-non-zts-20090626/pdo_pgsql.so'
		;;
		'54')
		extFile='/www/server/php/54/lib/php/extensions/no-debug-non-zts-20100525/pdo_pgsql.so'
		;;
		'55')
		extFile='/www/server/php/55/lib/php/extensions/no-debug-non-zts-20121212/pdo_pgsql.so'
		;;
		'56')
		extFile='/www/server/php/56/lib/php/extensions/no-debug-non-zts-20131226/pdo_pgsql.so'
		;;
		'70')
		extFile='/www/server/php/70/lib/php/extensions/no-debug-non-zts-20151012/pdo_pgsql.so'
		;;
		'71')
		extFile='/www/server/php/71/lib/php/extensions/no-debug-non-zts-20160303/pdo_pgsql.so'
		;;
		'72')
		extFile='/www/server/php/72/lib/php/extensions/no-debug-non-zts-20170718/pdo_pgsql.so'
		;;
		'73')
		extFile='/www/server/php/73/lib/php/extensions/no-debug-non-zts-20180731/pdo_pgsql.so'
		;;
		'74')
		extFile='/www/server/php/74/lib/php/extensions/no-debug-non-zts-20190902/pdo_pgsql.so'
		;;
		'80')
		extFile='/www/server/php/80/lib/php/extensions/no-debug-non-zts-20200930/pdo_pgsql.so'
		;;
		'81')
		extFile='/www/server/php/81/lib/php/extensions/no-debug-non-zts-20210902/pdo_pgsql.so'
		;;
	esac

	if [ ! -f "${extFile}" ];then
		cd /www/server/php/$version/src/ext/pdo_pgsql
		/www/server/php/$version/bin/phpize
		./configure --with-php-config=/www/server/php/$version/bin/php-config --with-pdo-pgsql=/www/server/pgsql
		make && make install
	fi

	if [ ! -f "${extFile}" ];then
		echo 'error';
		exit 0;
	fi

	echo -e "extension = $extFile" >> /www/server/php/$version/etc/php.ini
		/www/server/php/${version}/bin/php -m |grep pgsql
	service php-fpm-$version reload
	echo '==============================================='
	echo 'successful!'

}
Uninstall_Pdo_Pgsql()
{
	if [ ! -f "/www/server/php/$version/bin/php-config" ];then
		echo "php-$vphp 未安装,请选择其它版本!"
		echo "php-$vphp not install, Plese select other version!"
		return
	fi

	isInstall=`cat /www/server/php/$version/etc/php.ini|grep 'pdo_pgsql.so'`
	if [ "${isInstall}" = "" ];then
		echo "php-$vphp 未安装Fileinfo,请选择其它版本!"
		echo "php-$vphp not install Fileinfo, Plese select other version!"
		return
	fi

	sed -i '/pdo_pgsql.so/d' /www/server/php/$version/etc/php.ini

	service php-fpm-$version reload
	echo '==============================================='
	echo 'successful!'
}
actionType=$1
version=$2
vphp=${version:0:1}.${version:1:1}
if [ "$actionType" == 'install' ];then
	Install_Pdo_Pgsql
elif [ "$actionType" == 'uninstall' ];then
	Uninstall_Pdo_Pgsql
fi
