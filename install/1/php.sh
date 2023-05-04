#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

public_file=/www/server/panel/install/public.sh
publicFileMd5=$(md5sum ${public_file} 2>/dev/null|awk '{print $1}')
md5check="8e49712d1fd332801443f8b6fd7f9208"
if [ "${publicFileMd5}" != "${md5check}"  ]; then
	wget -O Tpublic.sh 域名/install/public.sh -T 20;
	publicFileMd5=$(md5sum Tpublic.sh 2>/dev/null|awk '{print $1}')
	if [ "${publicFileMd5}" == "${md5check}"  ]; then
		\cp -rpa Tpublic.sh $public_file
	fi
	rm -f Tpublic.sh
fi
. $public_file

download_Url=https://download.bt.cn

run_path="/root"
mysql_dir="$Root_Path/server/mysql"
mysql_config="${mysql_dir}/bin/mysql_config"
php_path="$Root_Path/server/php"
Is_64bit=$(getconf LONG_BIT)
Root_Path=$(cat /var/bt_setupPath.conf)
apacheVersion=$(cat /var/bt_apacheVersion.pl)
sysType=$(uname -a|grep x86_64)

if [ -f "/etc/redhat-release" ] && [ $(cat /etc/os-release|grep PLATFORM_ID|grep -oE "el8|an8") ];then
	el="8"
fi

CENTOS_OS=$(cat /etc/redhat-release|grep  -oEi centos)
if [ "${CENTOS_OS}" ];then
	el=$(cat /etc/redhat-release|grep -oE "([6-8]\.)+[0-9]+"|cut -f1 -d ".")
	if [ -z "${el}" ];then
		el=$(cat /etc/redhat-release|grep -i "Centos Stream"|grep -oE 8)
	fi

fi

ALIYUN_OS=$(cat /etc/redhat-release|grep  -oEi aliyun)
if [ "${ALIYUN_OS}" ];then
	el=$(uname -r|grep -oE "al7|al8"|grep -oE "[7-8]")
fi
HUAWEI_CLOUD_EULER=$(cat /etc/os-release |grep '"Huawei Cloud EulerOS 1')
EULER_OS=$(cat /etc/os-release |grep "EulerOS 2.0 ")
[ "${HUAWEI_CLOUD_EULER}" ] && el="8"
[ "${EULER_OS}" ] && el="7"

if [ "${el}" == "8" ];then
	yum config-manager --set-enabled PowerTools
    yum config-manager --set-enabled powertools
fi

Install_Libzip(){
	if [ "${el}" == "8" ];then
		yum install -y libzip-devel
	else
		mkdir libzip
		cd libzip
		wget -O libzip5-1.5.2.rpm ${download_Url}/rpm/remi/${el}/libzip5-1.5.2.rpm
		wget -O libzip5-devel-1.5.2.rpm ${download_Url}/rpm/remi/${el}/libzip5-devel-1.5.2.rpm
		wget -O libzip5-tools-1.5.2.rpm ${download_Url}/rpm/remi/${el}/libzip5-tools-1.5.2.rpm
		yum install * -y
		cd ..
		rm -rf libzip
	fi
}

Install_Libsodium(){
	if [ ! -f "/usr/local/libsodium/lib/libsodium.so" ];then
		cd ${run_path}
		libsodiumVer="1.0.18"
		wget ${download_Url}/src/libsodium-${libsodiumVer}-stable.tar.gz
		tar -xvf libsodium-${libsodiumVer}-stable.tar.gz
		rm -f libsodium-${libsodiumVer}-stable.tar.gz
		cd libsodium-stable
		./configure --prefix=/usr/local/libsodium
		make -j${cpuCore}
		make install
		ln -sf /usr/local/libsodium/lib/libsodium.so /lib
		ln -sf /usr/local/libsodium/lib/libsodium.so.23 /usr/lib
		ldconfig
		cd ..
		rm -f libsodium-${libsodiumVer}-stable.tar.gz
		rm -rf libsodium-stable
	fi
}

Install_Onig(){
	onigCheck=$(ldconfig -p|grep libonig)
	if [ -z "${onigCheck}" ];then
		cd ${run_path}
		onigVer="6.9.6"
		wget -O onig-${onigVer}.tar.gz ${download_Url}/src/onig-${onigVer}.tar.gz
		tar  -xvf onig-${onigVer}.tar.gz
		cd onig-${onigVer}
		./configure --prefix=/usr/local/onig
		make -j${cpuCore}
		make install
		ln -sf /usr/local/onig/lib/libonig.so.5 /lib64/libonig.so.5
		ln -sf /usr/local/onig/lib/libonig.so /lib64/libonig.so
		ldconfig
		cd ..
		rm -rf onig-${onigVer}*
	fi
}

Install_Icu4c(){
	cd ${run_path}
	icu4cVer=$(/usr/bin/icu-config --version)
	if [ ! -f "/usr/bin/icu-config" ] || [ "${icu4cVer:0:2}" -gt "60" ];then
		wget -O icu4c-60_3-src.tgz ${download_Url}/src/icu4c-60_3-src.tgz
		tar -xvf icu4c-60_3-src.tgz
		cd icu/source
		./configure --prefix=/usr/local/icu
		make -j${cpuCore}
		make install
		[ -f "/usr/bin/icu-config" ] && mv /usr/bin/icu-config /usr/bin/icu-config.bak 
		ln -sf /usr/local/icu/bin/icu-config /usr/bin/icu-config
		echo "/usr/local/icu/lib" > /etc/ld.so.conf.d/zicu.conf
		ldconfig
		cd ../../
		rm -rf icu
		rm -f icu4c-60_3-src.tgz 
	fi
}

if [ -z "${el}" ] || [ "${Is_64bit}" == "32" ] || [ -z "${sysType}" ];then
	wget -O php.sh $download_Url/install/0/php.sh -T 5
	bash php.sh $1 $2
	exit;
fi

LibCurlVer=$(/usr/local/curl/bin/curl -V|grep curl|awk '{print $2}'|cut -d. -f2)
if [[ "${LibCurlVer}" -lt "64" ]] || [ "${el}" == "6" ] ; then
	wget -O php.sh $download_Url/install/1/old/php.sh -T 5
	bash php.sh $1 $2
	exit;
fi

Set_Php_INI(){
	sed -i 's/disable_functions =.*/disable_functions = passthru,exec,system,putenv,chroot,chgrp,chown,shell_exec,popen,proc_open,pcntl_exec,ini_alter,ini_restore,dl,openlog,syslog,readlink,symlink,popepassthru,pcntl_alarm,pcntl_fork,pcntl_waitpid,pcntl_wait,pcntl_wifexited,pcntl_wifstopped,pcntl_wifsignaled,pcntl_wifcontinued,pcntl_wexitstatus,pcntl_wtermsig,pcntl_wstopsig,pcntl_signal,pcntl_signal_dispatch,pcntl_get_last_error,pcntl_strerror,pcntl_sigprocmask,pcntl_sigwaitinfo,pcntl_sigtimedwait,pcntl_exec,pcntl_getpriority,pcntl_setpriority,imap_open,apache_setenv/g' /www/server/php/${php_version}/etc/php.ini
	sed -i 's/expose_php = On/expose_php = Off/g' /www/server/php/${php_version}/etc/php.ini
}
Set_Php_FPM(){
	sed -i "s#listen.backlog.*#listen.backlog = 8192#" /www/server/php/${php_version}/etc/php-fpm.conf
}
Install_PHP(){
	if [ "${php_version}" -ge "73" ]; then
		Install_Libzip
		yum install libsodium-devel sqlite-devel oniguruma-devel -y
		LIBSODIUM_SO=$(ldconfig -p|grep libsodium)
		if [ -z "${LIBSODIUM_SO}" ];then
			Install_Libsodium
		fi
		ONIGURUMA_SO=$(ldconfig -p|grep libonig)
		if [ -z "${ONIGURUMA_SO}" ];then
			Install_Onig
		fi
	fi
	wget ${download_Url}/rpm/centos${el}/${Is_64bit}/bt-php${php_version}.rpm
	rpm -ivh bt-php${php_version}.rpm --force --nodeps
	rm -f bt-php${php_version}.rpm
}
Uninstall_PHP(){
	php_version=${1/./}
	if [ -f "/www/server/php/${php_version}/rpm.pl" ];then
		yum remove -y bt-php${php_version}
		[ ! -f "/www/server/php/${php_version}/bin/php" ] && exit 0;
	fi
	service php-fpm-$php_version stop

	chkconfig --del php-fpm-${php_version}
	chkconfig --level 2345 php-fpm-${php_version} off

	rm -rf $php_path/$php_version
	rm -f /etc/init.d/php-fpm-$php_version

}
Download_Conf(){
	if [ ! -f "/www/server/nginx/conf/enable-php-${php_version}.conf" ];then
		wget -O /www/server/nginx/conf/enable-php-${php_version}.conf ${download_Url}/conf/enable-php-${php_version}.conf
	fi
}

Install_Zip_ext(){
	php_setup_path="/www/server/php/${php_version}"
	mkdir -p ${php_setup_path}/src/ext
	cd ${php_setup_path}/src/ext
	wget -O zip${php_version}.tar.gz ${download_Url}/rpm/src/zip${php_version}.tar.gz
	tar -xvf zip${php_version}.tar.gz
	rm -f zip${php_version}.tar.gz
	cd zip
	${php_setup_path}/bin/phpize
	./configure --with-php-config=${php_setup_path}/bin/php-config
	make && make install
	cd ../../

	if [ "${php_version}" == "73" ];then
		extFile="/www/server/php/73/lib/php/extensions/no-debug-non-zts-20180731/zip.so"
	elif [ "${php_version}" == "74" ]; then
		extFile="/www/server/php/74/lib/php/extensions/no-debug-non-zts-20190902/zip.so"
	elif [ "${php_version}" == "80" ]; then
		extFile="/www/server/php/80/lib/php/extensions/no-debug-non-zts-20200930/zip.so"
	elif [ "${php_version}" == "81" ]; then
		extFile="/www/server/php/81/lib/php/extensions/no-debug-non-zts-20210902/zip.so"
	elif [ "${php_version}" == "82" ]; then
		extFile="/www/server/php/82/lib/php/extensions/no-debug-non-zts-20220829/zip.so"

	fi

	if [ -f "${extFile}" ];then
		echo "extension = zip.so" >> ${php_setup_path}/etc/php.ini
	fi
}


actionType=$1
version=$2

if [ "$actionType" == 'install' ];then
	php_version=`echo $version|sed "s/\.//"`
	rm -f /tmp/php-cgi-${php_version}.sock
	Install_Icu4c
	Install_PHP
	Set_Php_INI
	Set_Php_FPM
	Download_Conf
	if [ "${php_version}" -ge "73" ];then
		Install_Zip_ext
	fi 
	/etc/init.d/php-fpm-${php_version} reload
	rm -f /tmp/php-cgi-${php_version}.sock
	/etc/init.d/php-fpm-${php_version} start	
else 
	if [ "$actionType" == 'uninstall' ];then
	Uninstall_PHP $version
	fi
fi

