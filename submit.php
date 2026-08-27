<?php
// Form submission endpoint for asafan.com.br.
// Accepts the contact form (fale-conosco) and the career form (carreira),
// emails them via authenticated SMTP (mail() is disabled on Locaweb shared hosting).
//
// Credentials live in a config file ABOVE the web root so they are not web-fetchable.
// See mail-config.example.php for the expected structure.

declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');
header('X-Content-Type-Options: nosniff');
header('Referrer-Policy: same-origin');
header('Cache-Control: no-store, max-age=0');
header("Content-Security-Policy: default-src 'none'; frame-ancestors 'none'");

function bail(int $status, string $message): void {
    http_response_code($status);
    echo json_encode(['ok' => false, 'error' => $message], JSON_UNESCAPED_UNICODE);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    header('Allow: POST');
    bail(405, 'Metodo nao permitido.');
}

$contentLength = (int) ($_SERVER['CONTENT_LENGTH'] ?? 0);
if ($contentLength > 131072) {
    bail(413, 'Solicitacao muito grande.');
}

// Browser form posts should originate on the ASA Fan website. Origin is not
// always supplied by non-browser clients, so it is an additional signal rather
// than the only anti-abuse control.
$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
if ($origin !== '' && !in_array($origin, ['https://www.asafan.com.br', 'https://asafan.com.br'], true)) {
    bail(403, 'Origem da solicitacao nao permitida.');
}

function post_string(string $key): string {
    $value = $_POST[$key] ?? '';
    if (!is_string($value)) {
        bail(400, 'Formato de campo invalido.');
    }
    return $value;
}

function enforce_rate_limit(string $clientKey, int $maxRequests = 10, int $windowSeconds = 900): void {
    $path = rtrim(sys_get_temp_dir(), DIRECTORY_SEPARATOR) . DIRECTORY_SEPARATOR
        . 'asafan-form-' . hash('sha256', $clientKey) . '.json';
    $fp = @fopen($path, 'c+');
    if ($fp === false) {
        // Do not take the form offline if the host temporarily denies temp-file writes.
        error_log('[submit.php] Unable to open rate-limit file.');
        return;
    }
    try {
        if (!flock($fp, LOCK_EX)) {
            return;
        }
        $raw = stream_get_contents($fp);
        $timestamps = json_decode($raw ?: '[]', true);
        if (!is_array($timestamps)) {
            $timestamps = [];
        }
        $now = time();
        $timestamps = array_values(array_filter($timestamps, static function ($value) use ($now, $windowSeconds): bool {
            return is_int($value) && $value > ($now - $windowSeconds);
        }));
        if (count($timestamps) >= $maxRequests) {
            header('Retry-After: ' . $windowSeconds);
            bail(429, 'Muitas tentativas. Aguarde alguns minutos e tente novamente.');
        }
        $timestamps[] = $now;
        ftruncate($fp, 0);
        rewind($fp);
        fwrite($fp, json_encode($timestamps));
        fflush($fp);
    } finally {
        flock($fp, LOCK_UN);
        fclose($fp);
    }
}

enforce_rate_limit($_SERVER['REMOTE_ADDR'] ?? 'unknown');

// Honeypot — bots fill hidden fields, humans do not.
if (post_string('website') !== '' || post_string('url') !== '') {
    echo json_encode(['ok' => true]);
    exit;
}

$type = post_string('type');
if (!in_array($type, ['contact', 'career'], true)) {
    bail(400, 'Tipo de formulario invalido.');
}

function clean_line(string $value, int $maxLen = 500): string {
    $value = str_replace(["\r", "\n", "\0"], '', $value);
    $value = trim($value);
    return mb_substr($value, 0, $maxLen);
}

function clean_multiline(string $value, int $maxLen = 10000): string {
    $value = str_replace(["\r\n", "\r"], "\n", $value);
    $value = str_replace("\0", '', $value);
    $value = trim($value);
    return mb_substr($value, 0, $maxLen);
}

if ($type === 'contact') {
    $nome     = clean_line(post_string('nome'));
    $telefone = clean_line(post_string('telefone'));
    $email    = clean_line(post_string('email'));
    $mensagem = clean_multiline(post_string('mensagem'));

    if ($nome === '' || $telefone === '' || $email === '') {
        bail(400, 'Preencha os campos obrigatorios.');
    }
    if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
        bail(400, 'E-mail invalido.');
    }

    $subject = "[Site] Contato: $nome";
    $body =
        "Nome: $nome\n" .
        "Telefone: $telefone\n" .
        "E-mail: $email\n\n" .
        "Mensagem:\n" . ($mensagem !== '' ? $mensagem : '(sem mensagem)') . "\n";

} else { // career
    $nome           = clean_line(post_string('nome'));
    $nascimento     = clean_line(post_string('nascimento'));
    $email          = clean_line(post_string('email'));
    $telefone       = clean_line(post_string('telefone'));
    $cargo          = clean_line(post_string('cargo'));
    $pretensao      = clean_line(post_string('pretensao'));
    $experiencia    = clean_multiline(post_string('experiencia'));
    $formacao       = clean_multiline(post_string('formacao'));
    $complementares = clean_multiline(post_string('complementares'));
    $lgpd           = post_string('lgpd') !== '';

    if ($nome === '' || $email === '' || $telefone === '' || $cargo === '' ||
        $experiencia === '' || $formacao === '') {
        bail(400, 'Preencha os campos obrigatorios.');
    }
    if (!$lgpd) {
        bail(400, 'E necessario aceitar o termo de LGPD.');
    }
    if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
        bail(400, 'E-mail invalido.');
    }
    $allowedRoles = ['Administrativo', 'Financeiro', 'Comercial e Vendas', 'Representante Comercial', 'Estoque/Logística'];
    if (!in_array($cargo, $allowedRoles, true)) {
        bail(400, 'Cargo de interesse invalido.');
    }
    $birthDate = DateTimeImmutable::createFromFormat('!d/m/Y', $nascimento);
    $dateErrors = DateTimeImmutable::getLastErrors();
    if ($birthDate === false || ($dateErrors !== false && ($dateErrors['warning_count'] > 0 || $dateErrors['error_count'] > 0))) {
        bail(400, 'Data de nascimento invalida.');
    }

    $subject = "[Site] Candidatura: $nome - $cargo";
    $body =
        "Nome: $nome\n" .
        "Data de Nascimento: $nascimento\n" .
        "E-mail: $email\n" .
        "Telefone: $telefone\n" .
        "Cargo de Interesse: $cargo\n" .
        "Pretensao Salarial: " . ($pretensao !== '' ? $pretensao : '-') . "\n\n" .
        "Experiencia Profissional:\n$experiencia\n\n" .
        "Formacao:\n$formacao\n\n" .
        "Informacoes Complementares:\n" . ($complementares !== '' ? $complementares : '-') . "\n\n" .
        "LGPD: autorizou tratamento de dados.\n";
}

// ----- Load SMTP config from above the web root -----
$configPath = dirname(__DIR__) . '/mail-config.php';
if (!is_file($configPath)) {
    bail(500, 'Configuracao do servidor de e-mail nao encontrada. Tente novamente em alguns minutos ou envie um e-mail diretamente para comercial@asafan.com.br.');
}
$config = require $configPath;
foreach (['host', 'port', 'secure', 'username', 'password', 'from_address', 'from_name', 'to'] as $k) {
    if (!isset($config[$k])) {
        bail(500, 'Configuracao incompleta. Envie um e-mail diretamente para comercial@asafan.com.br.');
    }
}
if (!in_array($config['secure'], ['ssl', 'tls'], true)) {
    bail(500, 'Configuracao de seguranca do servidor de e-mail invalida.');
}

// ----- Compose the message -----
$encodedSubject = '=?UTF-8?B?' . base64_encode($subject) . '?=';
$encodedFromName = '=?UTF-8?B?' . base64_encode($config['from_name']) . '?=';

$headers = [
    "From: $encodedFromName <{$config['from_address']}>",
    "To: <{$config['to']}>",
    "Reply-To: <$email>",
    "Subject: $encodedSubject",
    'MIME-Version: 1.0',
    'Content-Type: text/plain; charset=UTF-8',
    'Content-Transfer-Encoding: 8bit',
    'X-Mailer: ASA Fan Site',
    'Date: ' . date('r'),
];

try {
    smtp_send($config, $config['to'], $headers, $body);
} catch (\Throwable $t) {
    error_log('[submit.php] SMTP failure: ' . $t->getMessage());
    bail(500, 'Nao foi possivel enviar a mensagem agora. Tente novamente em instantes ou envie um e-mail diretamente para comercial@asafan.com.br.');
}

echo json_encode(['ok' => true]);


// ===== Minimal SMTP client (no PHPMailer dependency) =====

function smtp_send(array $config, string $to, array $headers, string $body): void {
    $host = $config['host'];
    $port = (int) $config['port'];
    $secure = $config['secure']; // 'ssl' | 'tls' | 'none'
    $user = $config['username'];
    $pass = $config['password'];
    $fromAddr = $config['from_address'];
    $timeout = 30;

    $remote = ($secure === 'ssl' ? 'ssl://' : 'tcp://') . $host . ':' . $port;
    $context = stream_context_create([
        'ssl' => [
            'verify_peer'       => true,
            'verify_peer_name'  => true,
            'allow_self_signed' => false,
        ],
    ]);

    $fp = @stream_socket_client($remote, $errno, $errstr, $timeout, STREAM_CLIENT_CONNECT, $context);
    if (!$fp) {
        throw new RuntimeException("SMTP connect failed: $errstr ($errno)");
    }
    stream_set_timeout($fp, $timeout);

    $read = function () use ($fp): string {
        $out = '';
        while (!feof($fp)) {
            $line = fgets($fp, 1024);
            if ($line === false) break;
            $out .= $line;
            if (isset($line[3]) && $line[3] === ' ') break;
        }
        return $out;
    };
    $expect = function (string $expected) use ($read): string {
        $line = $read();
        if (substr($line, 0, 3) !== $expected) {
            throw new RuntimeException("SMTP expected $expected, got: " . trim($line));
        }
        return $line;
    };
    $send = function (string $cmd) use ($fp): void {
        fwrite($fp, $cmd . "\r\n");
    };

    $expect('220');
    $send('EHLO asafan.com.br');
    $expect('250');

    if ($secure === 'tls') {
        $send('STARTTLS');
        $expect('220');
        if (!stream_socket_enable_crypto($fp, true, STREAM_CRYPTO_METHOD_TLS_CLIENT)) {
            throw new RuntimeException('SMTP STARTTLS handshake failed');
        }
        $send('EHLO asafan.com.br');
        $expect('250');
    }

    $send('AUTH LOGIN');
    $expect('334');
    $send(base64_encode($user));
    $expect('334');
    $send(base64_encode($pass));
    $expect('235');

    $send("MAIL FROM:<$fromAddr>");
    $expect('250');
    $send("RCPT TO:<$to>");
    $expect('250');
    $send('DATA');
    $expect('354');

    // RFC 5321 dot-stuffing: any line starting with '.' must be doubled
    $bodyEsc = preg_replace('/^\./m', '..', $body);

    $message = implode("\r\n", $headers) . "\r\n\r\n" . str_replace("\n", "\r\n", $bodyEsc);
    fwrite($fp, $message . "\r\n.\r\n");
    $expect('250');

    $send('QUIT');
    fclose($fp);
}
