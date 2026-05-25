<?php
// SMTP credentials for submit.php. Copy this to `mail-config.php`, fill in
// the real password, and upload `mail-config.php` to the FTP root (one level
// ABOVE public_html/) so it is not web-fetchable.
//
// On Locaweb the deployed path will be:
//   /home/asafan2/mail-config.php
// which resolves to dirname(__DIR__) . '/mail-config.php' from submit.php.
//
// mail-config.php is gitignored — never commit the real password.

return [
    // Locaweb SMTP server (use email-ssl.com.br for SSL on 465).
    'host'         => 'email-ssl.com.br',
    'port'         => 465,
    'secure'       => 'ssl', // 'ssl' for port 465, 'tls' for STARTTLS on port 587

    // Authentication. Full e-mail address as username.
    'username'     => 'noreply@asafan.com.br',
    'password'     => 'REPLACE_WITH_NOREPLY_MAILBOX_PASSWORD',

    // Headers that appear in the e-mail.
    'from_address' => 'noreply@asafan.com.br',
    'from_name'    => 'ASA Fan Site',

    // Where form submissions are delivered.
    'to'           => 'comercial@asafan.com.br',
];
