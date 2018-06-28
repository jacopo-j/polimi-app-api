# polimi_cli

Wrapper scritto in Python3 per i Servizi Online del Politecnico di Milano. Le API utilizzate sono state ottenute dall'app ufficiale per Android.

## Note su autorizzazione, password, portachiavi
* Perché lo script funzioni è necessario inserire un token segreto che identifica il client. Per esempio è possibile utilizzare quello dell'app per Android; tuttavia nel codice pubblicato in questo repository il token non viene fornito. Trovarlo è comunque molto semplice.
* La password viene richiesta e utilizzata solo se non esiste già un token di sessione valido.
* Quando lo script riceve un token di sessione dai Servizi Online, questo viene salvato nel portachiavi di sistema usando il modulo `keyring`. Verificare la compatibilità con il proprio sistema o eventualmente commentare le relative linee di codice. Il funzionamento dello script con il modulo `keyring` è stato testato su macOS.

## Esempio di utilizzo
```python
>>> from polimi_cli import *

>>> me = PoliMiAccount(12345678) # Codice Persona
Password:

>>> me.print_user_info()

Codice persona: 12345678
Cognome:        ROSSI
Nome:           MARIO

Matricola 123456: tipo anagrafica: Studenti
                  tipo carriera: Studente
                  stato carriera: Attiva

>>> me.print_studyplan()

Matricola:       123456
Corso di laurea: Ingegneria Informatica
Tipo CdL:        Laurea di primo livello
Anno accademico: 2017
Piano approvato: S
Media:           30.0
CFU superati:    160.0

Fondamenti di Automatica
    Anno accademico: 2017/18
    Periodo: 2 AC -  2 sem.
    Lingua: IT
    Stato: Sost.
    Voto: 30L
```

## To do
* Dettagli di ogni insegnamento
* Generazione di un calendario in formato `vcal` a partire dall'orario
* Tante altre cose
