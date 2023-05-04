#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

Install_ZendGuardLoader()
{
	isInstall=`cat /www/server/php/$version/etc/php.ini|grep 'ZendGuardLoader.so'`
	if [ "${isInstall}" != "" ];then
		echo "php-$vphp 已安装xdebug,请选择其它版本!"
		return
	fi
	
	public_file=/www/server/panel/install/public.sh
	if [ ! -f $public_file ];then
		wget -O $public_file https://raw.githubusercontent.com/chenxi-a11y/bt/main/install/public.sh -T 5;
	fi
	. $public_file

	download_Url=https://download.bt.cn
	if [ ! -f "/usr/local/zend/php$version/ZendGuardLoader.so" ];then
		Is_64bit=`getconf LONG_BIT`
		mkdir -p /usr/local/zend/php$version
		if [ "${Is_64bit}" = "64" ] ; then
			wget $download_Url/src/ZendGuardLoader-php-$vphp-linux-glibc23-x86_64.tar.gz
			tar zxf ZendGuardLoader-php-$vphp-linux-glibc23-x86_64.tar.gz
			\cp ZendGuardLoader-php-$vphp-linux-glibc23-x86_64/php-$vphp.x/ZendGuardLoader.so /usr/local/zend/php$version/
			rm -f ZendGuardLoader-php-$vphp-linux-glibc23-x86_64.tar.gz
			rm -rf ZendGuardLoader-php-$vphp-linux-glibc23-x86_64
		else
			wget $download_Url/src/ZendGuardLoader-php-$vphp-linux-glibc23-i386.tar.gz
			tar zxf ZendGuardLoader-php-$vphp-linux-glibc23-i386.tar.gz
			\cp ZendGuardLoader-php-$vphp-linux-glibc23-i386/php-$vphp.x/ZendGuardLoader.so /usr/local/zend/php$version/
			rm -rf ZendGuardLoader-php-$vphp-linux-glibc23-i386
			rm -f ZendGuardLoader-php-$vphp-linux-glibc23-i386.tar.gz
		fi
	fi
	
	if [ ! -f "/usr/local/zend/php$version/ZendGuardLoader.so" ];then
		echo "ERROR!"
		return;
	fi
	isZZL=`cat /www/server/php/$version/etc/php.ini|grep '[Zend ZendGuard Loader]'`
	if [ "$isZZL" != "" ];then
		sed -i "s#\[Zend ZendGuard Loader\]#\[Zend ZendGuard Loader\]\nzend_extension=/usr/local/zend/php$version/ZendGuardLoader.so\nzend_loader.enable=1\nzend_loader.disable_licensing=0\nzend_loader.obfuscation_level_support=3\nzend_loader.license_path=#" /www/server/php/$version/etc/php.ini
	else
		echo "s#\[Zend ZendGuard Loader\]#\[Zend ZendGuard Loader\]\nzend_extension=/usr/local/zend/php$version/ZendGuardLoader.so\nzend_loader.enable=1\nzend_loader.disable_licensing=0\nzend_loader.obfuscation_level_support=3\nzend_loader.license_path=#" >> /www/server/php/$version/etc/php.ini
	fi
	service php-fpm-$version reload
	echo '==========================================================='
	echo 'successful!'
}


Uninstall_ZendGuardLoader()
{
	if [ ! -f "/www/server/php/$version/bin/php-config" ];then
		echo "php-$vphp 未安装,请选择其它版本!"
		return
	fi
	isInstall=`cat /www/server/php/$version/etc/php.ini|grep 'ZendGuardLoader.so'`
	if [ "${isInstall}" == "" ];then
		echo "php-$vphp 未安装intl,请选择其它版本!"
		return
	fi
	
	sed -i '/ZendGuardLoader.so/d'  /www/server/php/$version/etc/php.ini
	sed -i '/zend_loader/d'  /www/server/php/$version/etc/php.ini
	service php-fpm-$version reload
	echo '==============================================='
	echo 'successful!'
}

actionType=$1
version=$2
vphp=${version:0:1}.${version:1:1}
if [ "$actionType" == 'install' ];then
	Install_ZendGuardLoader
elif [ "$actionType" == 'uninstall' ];then
	Uninstall_ZendGuardLoader
fi
