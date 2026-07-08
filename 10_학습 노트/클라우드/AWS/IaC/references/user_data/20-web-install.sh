dnf install -y httpd php php-mysqlnd php-fpm

systemctl enable --now php-fpm
systemctl enable --now httpd

cat > /var/www/html/index.html <<'HTML'
<h1>Terraform Web Server</h1>
<p>Public Web Server is running.</p>
<p>DB test: <a href="/db-test.php">/db-test.php</a></p>
HTML

cat > /var/www/html/db-test.php <<'PHP'
<?php
header('Content-Type: text/plain; charset=utf-8');

$host = '192.168.10.13';
$db   = 'appdb';
$user = 'webuser';
$pass = 'itbank';

try {
    $pdo = new PDO(
        "mysql:host=$host;dbname=$db;charset=utf8mb4",
        $user,
        $pass,
        [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        ]
    );

    $pdo->exec("INSERT INTO connection_test (message) VALUES ('WEB -> DB OK')");

    $stmt = $pdo->query(
        "SELECT id, message, created_at
         FROM connection_test
         ORDER BY id DESC
         LIMIT 5"
    );

    echo "WEB -> DB CONNECT OK\n";
    echo "DB_HOST={$host}\n\n";

    foreach ($stmt as $row) {
        echo "{$row['id']} | {$row['message']} | {$row['created_at']}\n";
    }
} catch (Throwable $e) {
    http_response_code(500);
    echo "WEB -> DB CONNECT FAIL\n";
    echo $e->getMessage() . "\n";
}
PHP

systemctl restart httpd