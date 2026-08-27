# Deploy manual na Locaweb

O site continua estático e compatível com hospedagem compartilhada. Não é
necessário instalar Node, Python ou qualquer framework na Locaweb.

## 1. Preparar e validar

Na raiz do projeto, execute:

```powershell
python scripts/apply_sitewide.py
python scripts/check_site.py
python scripts/build_deploy_package.py
```

Se `python` não estiver disponível no Windows, use o executável Python já
instalado no seu ambiente ou rode os mesmos scripts pelo GitHub Actions.

O último comando cria:

- `deploy.zip`: somente os arquivos públicos que devem ir para o FTP;
- `deploy-manifest.json`: lista, tamanho e hash de cada arquivo.

O ZIP exclui deliberadamente fontes, documentação, dados brutos, Git e
`mail-config.php`.

## 2. Fazer backup

Antes de substituir arquivos, baixe uma cópia da pasta pública atual da
Locaweb. Guarde também uma cópia separada do `mail-config.php`, que contém as
credenciais SMTP e deve continuar acima da pasta pública.

## 3. Enviar por FTP

Extraia `deploy.zip` no computador. Envie o conteúdo extraído para a pasta
pública do domínio, preservando a estrutura de pastas. Uma ordem que reduz o
risco de páginas temporariamente inconsistentes é:

1. `assets/`, `css/` e `js/`;
2. `produto/`;
3. `submit.php`, `.htaccess`, `robots.txt` e `sitemap.xml`;
4. arquivos `.html` por último.

Não envie `mail-config.example.php` e não sobrescreva o `mail-config.php` real.

## 4. Conferir após o envio

- Abra a home em uma janela anônima e teste aceitar, rejeitar e personalizar cookies.
- Confira `privacidade.html` e uma URL inexistente para validar a página 404.
- Teste filtros do catálogo, menu móvel, WhatsApp e carrosséis.
- Envie um contato e uma candidatura de teste; confirme a chegada dos e-mails.
- Confira no DevTools que GA, GTM e Meta não carregam antes do consentimento.
- Depois de aceitar, valide os eventos no modo de depuração das plataformas.

Os arquivos CSS e JavaScript têm versão no endereço, reduzindo problemas com o
cache agressivo da hospedagem. Se a Locaweb ainda exibir conteúdo antigo, limpe
o cache pelo painel e teste novamente em janela anônima.
