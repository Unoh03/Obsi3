dnf clean all
dnf makecache
dnf install -y mariadb105-server

cat > /etc/my.cnf.d/99-terraform-lab.cnf <<'EOF'
[mysqld]
bind-address=0.0.0.0
EOF

systemctl enable --now mariadb

mysql <<'SQL'
CREATE DATABASE IF NOT EXISTS appdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'webuser'@'192.168.1.%' IDENTIFIED BY 'itbank';

GRANT SELECT, INSERT ON appdb.* TO 'webuser'@'192.168.1.%';

CREATE TABLE IF NOT EXISTS appdb.connection_test (
  id INT AUTO_INCREMENT PRIMARY KEY,
  message VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO appdb.connection_test (message)
VALUES ('DB bootstrap OK');

FLUSH PRIVILEGES;
SQL

mysql --version > /var/log/db-install-check.log 2>&1
mysql -e "SELECT user, host FROM mysql.user;" >> /var/log/db-install-check.log 2>&1
mysql -e "SELECT * FROM appdb.connection_test;" >> /var/log/db-install-check.log 2>&1