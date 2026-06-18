#!/bin/bash

### ===== 변수 =====
DEV_USER="user1"
WEB_ROOT="/var/www/care"
APACHE_PORT=80
DB_NAME="care"
DB_USER="user"
DB_PASS="1111"

echo "▶ LAMP 환경 구성 시작 (/var/www/care 기준)"

### 1. 패키지 업데이트
sudo apt update -y

### 2. Apache 설치
sudo apt install -y apache2
sudo systemctl enable --now apache2

# ### 3. Apache 포트 설정 (8080)
# PORTS_CONF="/etc/apache2/ports.conf"
# if ! grep -q "Listen ${APACHE_PORT}" $PORTS_CONF; then
#     echo "Listen ${APACHE_PORT}" | sudo tee -a $PORTS_CONF
# fi

### 4. Apache 서버포트 및 웹최상위 경로 설정
VHOST="/etc/apache2/sites-available/000-default.conf"
sudo sed -i "s/<VirtualHost \*:80>/<VirtualHost *:${APACHE_PORT}>/" $VHOST
sudo sed -i "s|DocumentRoot .*|DocumentRoot ${WEB_ROOT}|" $VHOST

### 5. 웹 디렉터리 생성
sudo mkdir -p ${WEB_ROOT}

### 6. 권한 설정
sudo chown -R ${DEV_USER}:www-data ${WEB_ROOT}
sudo chmod -R 775 ${WEB_ROOT}

### 7. Apache Directory 접근 허용
APACHE_CONF="/etc/apache2/apache2.conf"
if ! grep -q "<Directory ${WEB_ROOT}>" $APACHE_CONF; then
sudo tee -a $APACHE_CONF > /dev/null <<EOF

<Directory ${WEB_ROOT}>
    Options Indexes FollowSymLinks
    AllowOverride All
    Require all granted
</Directory>
EOF
fi

### 8. PHP 설치
sudo apt install -y \
php php-cli php-common php-mysql php-xml php-mbstring php-curl php-zip

### 9. PHP 설정 (short_open_tag)
PHP_INI="/etc/php/8.3/apache2/php.ini"
sudo sed -i 's/^short_open_tag = .*/short_open_tag = On/' $PHP_INI

### 10. PHP 테스트 파일 생성
cat <<EOF | sudo tee ${WEB_ROOT}/index.php > /dev/null
<?php
phpinfo();
?>
EOF

# ### 11. MySQL 설치
# sudo apt install -y mysql-server mysql-client
# sudo systemctl enable --now mysql

# ### 12. MySQL 문자셋 설정 (utf8mb4)
# MYSQL_CNF="/etc/mysql/mysql.conf.d/mysqld.cnf"
# sudo sed -i '/\[mysqld\]/a character-set-server=utf8mb4\ncollation-server=utf8mb4_unicode_ci' $MYSQL_CNF
# sudo sed -i '/\[client\]/a default-character-set=utf8mb4' $MYSQL_CNF
# sudo sed -i '/\[mysql\]/a default-character-set=utf8mb4' $MYSQL_CNF

# sudo systemctl restart mysql

# ### 13. DB 및 계정 생성
# sudo mysql <<EOF
# CREATE DATABASE IF NOT EXISTS ${DB_NAME}
# DEFAULT CHARACTER SET utf8mb4
# COLLATE utf8mb4_unicode_ci;

# CREATE USER IF NOT EXISTS '${DB_USER}'@'%' IDENTIFIED BY '${DB_PASS}';
# GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'%';
# FLUSH PRIVILEGES;
# EOF

### 14. Apache 재시작
sudo systemctl restart apache2

echo "구성 완료"
echo "▶ 웹 접속: http://<서버_IP>:${APACHE_PORT}"
echo "▶ DocumentRoot: ${WEB_ROOT}"
echo "▶ VS Code SSH → ${WEB_ROOT} 열어서 작업"
