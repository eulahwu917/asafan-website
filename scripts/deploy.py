#!/usr/bin/env python3
"""
scripts/deploy.py

Mirror the project root to Locaweb shared hosting via FTPS, using Python's ftplib.FTP_TLS
(OpenSSL-backed) instead of Windows Schannel-based clients.

Both prior attempts against this host failed under Schannel:
  - scripts/deploy.ps1 (System.Net.FtpWebRequest): every command (MKD and STOR alike) came
    back a generic "500 Syntax error, command unrecognized" once logged in.
  - scripts/deploy-curl.ps1 (curl.exe on Windows, also Schannel-backed): failed earlier, at
    the TLS handshake itself, with "curl: (64) Requested SSL level failed".

Best guess: Locaweb's FTP server enforces strict TLS session reuse between the control and
data connections (a common vsftpd "require_ssl_reuse"-style setting). Schannel-based clients
are known to have trouble satisfying this. Python's ftplib.FTP_TLS does the reuse correctly
by default via prot_p(), and runs on OpenSSL rather than Schannel -- different failure mode
entirely, worth trying before falling back to a manual web upload.

Usage:
  Dry run (no upload, just lists what would go):
    python scripts/deploy.py --dry-run

  Real upload:
    python scripts/deploy.py
"""
import argparse
import ftplib
import getpass
import pathlib
import sys

FTP_HOST = 'ftp.asafan2.hospedagemdesites.ws'
FTP_PORT = 21
FTP_USER = 'asafan2'
TARGET_ROOT = '/public_html/'

# Same exclude list as scripts/deploy.ps1 and scripts/deploy-curl.ps1 -- keep all three in
# sync if any changes.
EXCLUDE_NAMES = {
    '.git', '.gitignore', '.gitattributes',
    '.claude', '.gstack', '.vscode',
    'sessions', 'raw_assets', 'project files', 'assets_upgrade',
    # docs/ holds internal client feedback files, not site content -- must never go public
    'docs',
    'scripts',
    'PROJECT.md', 'REFERENCE.md',
    'deploy.zip', 'test.zip', 'hero-video-payload.bin',
    'mail-config.php',
    '_diag.php',
}

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def discover_files():
    files = []
    for p in REPO_ROOT.rglob('*'):
        if p.is_dir():
            continue
        rel = p.relative_to(REPO_ROOT)
        if any(part in EXCLUDE_NAMES for part in rel.parts):
            continue
        files.append(p)
    return sorted(files)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--target-root', default=TARGET_ROOT)
    args = ap.parse_args()

    files = discover_files()
    total_bytes = sum(f.stat().st_size for f in files)

    print()
    print(f'Host:   {FTP_HOST}:{FTP_PORT}  (FTPS via Python ftplib / OpenSSL)')
    print(f'User:   {FTP_USER}')
    print(f'Target: {args.target_root}')
    print()
    print(f'Files to upload: {len(files)}')
    print(f'Total size:      {total_bytes / 1024 / 1024:.2f} MB')
    print()

    if args.dry_run:
        for f in files:
            rel = f.relative_to(REPO_ROOT).as_posix()
            print(f'  {rel}  ({f.stat().st_size / 1024:.1f} KB)')
        print()
        print('DRY RUN - no files uploaded.')
        return

    confirm = input(f'Upload {len(files)} files to {args.target_root}? [y/N]: ')
    if confirm.strip().lower() != 'y':
        print('Cancelled.')
        return

    password = getpass.getpass(f'FTP password for {FTP_USER}@{FTP_HOST}: ')
    if not password:
        print('No password entered.', file=sys.stderr)
        sys.exit(1)

    print('Connecting...')
    ftps = ftplib.FTP_TLS(timeout=30)
    ftps.connect(FTP_HOST, FTP_PORT)
    ftps.auth()
    ftps.login(FTP_USER, password)
    ftps.prot_p()  # secure the data channel + reuse the control connection's TLS session
    ftps.set_pasv(True)
    print('Connected and authenticated.\n')

    target_root = args.target_root.rstrip('/')

    dirs_needed = sorted({
        f.relative_to(REPO_ROOT).parent.as_posix()
        for f in files
        if f.relative_to(REPO_ROOT).parent != pathlib.PurePosixPath('.')
    })
    print(f'Ensuring {len(dirs_needed)} directories exist...')
    created_dirs = set()
    for d in dirs_needed:
        accum = target_root
        for part in d.split('/'):
            accum = f'{accum}/{part}'
            if accum in created_dirs:
                continue
            try:
                ftps.mkd(accum)
            except ftplib.error_perm as e:
                print(f'  (mkdir {accum} -> {e}, continuing)')
            created_dirs.add(accum)
    print()

    failed = []
    for i, f in enumerate(files, 1):
        rel = f.relative_to(REPO_ROOT).as_posix()
        remote_path = f'{target_root}/{rel}'
        print(f'[{i}/{len(files)}] {rel} ...', end=' ')
        try:
            with open(f, 'rb') as fh:
                ftps.storbinary(f'STOR {remote_path}', fh)
            print('ok')
        except Exception as e:
            print(f'FAILED: {e}')
            failed.append(rel)

    try:
        ftps.quit()
    except Exception:
        ftps.close()

    print()
    if not failed:
        print(f'Done. Uploaded {len(files)} files.')
    else:
        print(f'Finished with {len(failed)} failure(s) out of {len(files)}:')
        for rel in failed:
            print(f'  {rel}')


if __name__ == '__main__':
    main()
