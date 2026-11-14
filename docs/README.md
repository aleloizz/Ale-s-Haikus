# Documentation

Questa repository pubblica contiene il codice dell'applicazione, i test e la
documentazione generica di architettura e sicurezza.

I runbook operativi dettagliati — deploy, backup, restore, cutover, topologia
reale, hostname, porte, utenti e procedure di emergenza — sono mantenuti nella
cartella privata `aleshaikus-deploy/docs/`, fuori da questa repository.

Regole:

- nessun token, password, chiave o passphrase in questa repository;
- nessun hostname/IP/porta/utente reale nella documentazione pubblica;
- i runbook operativi non vanno committati qui, nemmeno con `.gitignore`;
- `.gitignore` è solo una rete di sicurezza, non una misura di sicurezza.

Sono pubblici solo i riepiloghi degli Step 1 e 2, che non contengono segreti né
dettagli operativi sensibili.
